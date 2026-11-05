import argparse

import joblib

from common import MODELS_DIR
from evaluation import best_model_name, cross_validate_by_race, summarize, walk_forward
from features import FEATURES, build_race_table, load_seasons
from models import make_models

def model_path(category):
    return MODELS_DIR / f"race_position_{category}.joblib"

def run_evaluation(category="MotoGP", progress=None):
    report = progress or (lambda percent, message: None)
    report(5, "Loading seasons...")
    df = load_seasons()
    report(15, "Building the dataset...")
    table = build_race_table(df, category)
    finished = table[table["race_position"].notna()]
    years = [int(year) for year in sorted(finished["year"].unique())]
    if len(finished) < 50:
        raise ValueError(f"Not enough finished results for {category}: {len(finished)} rows")

    def scaled(low, high):
        return lambda percent, message: report(low + int(percent * (high - low) / 100), message)

    if len(years) >= 2:
        mode = "walk-forward by season"
        per_race, fitted = walk_forward(table, scaled(20, 90))
        trained_years, test_year = years[:-1], years[-1]
    else:
        mode = "cross-validation by race (single season: indicative only)"
        per_race = cross_validate_by_race(table, scaled(20, 80))
        report(85, "Training the final models...")
        fitted = {name: model.fit(finished[FEATURES], finished["race_position"])
                  for name, model in make_models().items()}
        trained_years, test_year = years, None

    summary = summarize(per_race)
    best = best_model_name(summary)

    report(95, "Saving the model...")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = model_path(category)
    joblib.dump({
        "category": category, "model_name": best, "model": fitted[best], "features": FEATURES,
        "trained_years": trained_years, "test_year": test_year, "mode": mode,
    }, path)
    report(100, "Done")

    by_year = per_race.pivot_table(index="method", columns="year", values="mae_rank")
    return {
        "category": category, "mode": mode, "summary": summary, "mae_by_year": by_year,
        "best_model": best, "trained_years": trained_years, "test_year": test_year,
        "training_rows": len(finished), "model_path": path,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", default="MotoGP", choices=["MotoGP", "Moto2", "Moto3"])
    arguments = parser.parse_args()
    result = run_evaluation(arguments.category, progress=lambda p, m: print(f"[{p:3d}%] {m}"))
    print(f"\n{result['category']} - {result['mode']}")
    print(f"Training rows: {result['training_rows']} | years used for training: {result['trained_years']}")
    print("\nMAE = average error in finishing positions (lower is better)")
    print(result["summary"].round(3).to_string())
    print(f"\nBest model: {result['best_model']}  ->  saved to {result['model_path']}")
