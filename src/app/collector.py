import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from config import (
    API_BASE,
    EXCLUDED_CATEGORIES,
    MAX_RETRIES,
    MAX_WORKERS,
    RAW_DIR,
    REQUEST_DELAY,
    REQUEST_TIMEOUT,
    USER_AGENT,
)
from naming import build_filename, clean_part, event_code


class FetchError(Exception):
    """A request failed even after backup attempts."""


class Cancelled(Exception):
    """The user pressed Cancel."""

_thread_data = threading.local()


def _http():
    session = getattr(_thread_data, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        _thread_data.session = session
    return session


def fetch_json(url):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = _http().get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 404:
                return None
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code}")
            response.raise_for_status()
            data = response.json()
            time.sleep(REQUEST_DELAY)
            return data
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(attempt * 1.5)
    raise FetchError(f"{url}: {last_error}")

def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, path)


def _run_parallel(function, items, check_cancel):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(function, item): item for item in items}
        try:
            for future in as_completed(futures):
                check_cancel()
                try:
                    yield futures[future], future.result(), None
                except FetchError as exc:
                    yield futures[future], None, exc
        except BaseException:
            pool.shutdown(wait=False, cancel_futures=True)
            raise

def _sessions_url(event, category):
    return f"{API_BASE}/sessions?eventUuid={event['id']}&categoryUuid={category['id']}"

def _fetch_sessions(pair):
    event, category = pair
    return fetch_json(_sessions_url(event, category))

def _fetch_and_save(job):
    session_id, path = job
    data = fetch_json(f"{API_BASE}/session/{session_id}/classification?test=false")
    if data is None:
        return "missing"
    save_json(data, path)
    return "downloaded"

def download_season(year, progress=None, cancel=None):
    report = progress or (lambda percent, message: None)

    def check_cancel():
        if cancel is not None and cancel.is_set():
            raise Cancelled()

    summary = {"downloaded": 0, "skipped": 0, "missing": 0, "failed": 0, "cancelled": False}
    try:
        _download(year, report, check_cancel, summary)
    except Cancelled:
        summary["cancelled"] = True
    return summary

def _download(year, report, check_cancel, summary):
    report(0, f"Looking up season {year}...")
    seasons = fetch_json(f"{API_BASE}/seasons") or []
    season = next((s for s in seasons if s.get("year") == year), None)
    if season is None:
        raise ValueError(f"Season {year} not found in the API")

    events = fetch_json(f"{API_BASE}/events?seasonUuid={season['id']}&isFinished=true") or []
    categories = fetch_json(f"{API_BASE}/categories?seasonUuid={season['id']}") or []
    events = [e for e in events if not e.get("test")]
    categories = [
        c for c in categories
        if not any(excluded in c.get("name", "") for excluded in EXCLUDED_CATEGORIES)
    ]
    if not events or not categories:
        raise ValueError(f"No finished events found for {year}")

    year_dir = RAW_DIR / str(year)

    pairs = [(event, category) for event in events for category in categories]
    jobs = []
    done = 0
    for (event, category), sessions, error in _run_parallel(_fetch_sessions, pairs, check_cancel):
        done += 1
        if error is not None:
            summary["failed"] += 1
        elif sessions:
            code = event_code(event)
            save_json(sessions, year_dir / "sessions" / f"{clean_part(code)}_{clean_part(category['name'])}.json")
            for session in sessions:
                if not session.get("id"):
                    continue
                filename = build_filename(
                    category["name"], year, code, session.get("type"), session.get("number")
                )
                jobs.append((session["id"], year_dir / filename))
        report(int(15 * done / len(pairs)), f"Sessions {done}/{len(pairs)}")

    missing_jobs = []
    for job in jobs:
        if job[1].exists():
            summary["skipped"] += 1
        else:
            missing_jobs.append(job)

    total = len(jobs)
    processed = summary["skipped"]
    report(15, f"Results {processed}/{total}")
    for _, outcome, error in _run_parallel(_fetch_and_save, missing_jobs, check_cancel):
        summary["failed" if error is not None else outcome] += 1
        processed += 1
        report(15 + int(85 * processed / total), f"Results {processed}/{total}")
