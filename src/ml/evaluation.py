import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from common import KEY
from features import FEATURES
from models import MODEL_NAMES, make_models

GRID_BASELINE = "Grid position (baseline)"
PRACTICE_BASELINE = "Practice pace (baseline)"
BASELINES = {GRID_BASELINE: "grid_position", PRACTICE_BASELINE: "practice_gap_pct"}
METRICS = ["mae_rank", "spearman", "top3_hits", "top10_hits"]

def race_metrics(race, score_col="score"):
    finished = race[race["race_position"].notna()]
    if len(finished) < 5:
        return None
    predicted = finished[score_col].rank(method="first")
    actual = finished["race_position"].rank(method="first")

    def hits(n):
        return len(set(predicted[predicted <= n].index) & set(actual[actual <= n].index))

    return {
        "mae_rank": (predicted - actual).abs().mean(),
        "spearman": predicted.corr(actual, method="spearman"),
        "top3_hits": hits(3),
        "top10_hits": hits(10) if len(finished) >= 10 else np.nan,
        "riders": len(finished),
    }

def score_races(test, scores, method):
    table = test.assign(score=np.asarray(scores, dtype=float))
    rows = []
    for (year, event), race in table.groupby(KEY):
        metrics = race_metrics(race)
        if metrics is not None:
            rows.append({"method": method, "year": year, "event": event, **metrics})
    return rows

def _evaluate_split(train, test):
    rows = []
    for name, column in BASELINES.items():
        rows += score_races(test, test[column].fillna(1e9), name)
    fitted = {}
    for name, model in make_models().items():
        model.fit(train[FEATURES], train["race_position"])
        rows += score_races(test, model.predict(test[FEATURES]), name)
        fitted[name] = model
    return rows, fitted

def walk_forward(table, progress=None):
    report = progress or (lambda percent, message: None)
    years = sorted(table["year"].unique())
    rows, fitted = [], {}
    for step, test_year in enumerate(years[1:], 1):
        train = table[(table["year"] < test_year) & table["race_position"].notna()]
        test = table[table["year"] == test_year]
        split_rows, fitted = _evaluate_split(train, test)
        rows += split_rows
        report(int(100 * step / (len(years) - 1)), f"Season {test_year} predicted with data up to {test_year - 1}")
    return pd.DataFrame(rows), fitted

def cross_validate_by_race(table, progress=None):
    report = progress or (lambda percent, message: None)
    labelled = table.reset_index(drop=True)
    groups = labelled["year"].astype(str) + "-" + labelled["event"]
    splits = min(5, groups.nunique())
    rows = []
    for step, (train_idx, test_idx) in enumerate(GroupKFold(n_splits=splits).split(labelled, groups=groups), 1):
        train = labelled.iloc[train_idx]
        train = train[train["race_position"].notna()]
        split_rows, _ = _evaluate_split(train, labelled.iloc[test_idx])
        rows += split_rows
        report(int(100 * step / splits), f"Fold {step}/{splits}")
    return pd.DataFrame(rows)

def summarize(per_race):
    summary = per_race.groupby("method")[METRICS].mean()
    summary["races"] = per_race.groupby("method").size()
    grid_mae = summary.loc[GRID_BASELINE, "mae_rank"]
    summary["vs_grid_pct"] = (grid_mae - summary["mae_rank"]) / grid_mae * 100
    return summary.sort_values("mae_rank")

def best_model_name(summary):
    candidates = summary.loc[[name for name in MODEL_NAMES if name in summary.index]]
    return candidates["mae_rank"].idxmin()
