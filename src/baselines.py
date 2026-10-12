"""Baseline models for Energium.

Input:  data/processed/features.parquet
Output: data/processed/baselines_report.md
"""
import pandas as pd
import numpy as np
from pathlib import Path

PROC = Path("data/processed")


def mae(y_true, y_pred):
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def evaluate(y_true, y_pred, name):
    return {
        "model": name,
        "MAE": mae(y_true, y_pred),
        "RMSE": rmse(y_true, y_pred),
    }


def main():
    print("Loading features.parquet...")
    df = pd.read_parquet(PROC / "features.parquet")
    print(f"  → {len(df)} rows")

    results = []

    # Evaluate on validation + test
    for split in ["validation", "test"]:
        sdf = df[df["split"] == split].copy()
        if len(sdf) == 0:
            continue

        y_true = sdf["actual_wind_mwh"].values

        # Baseline 1: ForecastDayAhead (official)
        y_forecast = sdf["forecast_wind_da"].values
        results.append({
            "split": split,
            **evaluate(y_true, y_forecast, "ForecastDayAhead (official)"),
        })

        # Baseline 2: Persistence t-1
        y_persist_1 = sdf["lag_1h"].values
        results.append({
            "split": split,
            **evaluate(y_true, y_persist_1, "Persistence t-1"),
        })

        # Baseline 3: Persistence t-168
        y_persist_168 = sdf["lag_168h"].values
        results.append({
            "split": split,
            **evaluate(y_true, y_persist_168, "Persistence t-168"),
        })

    # Report
    report = pd.DataFrame(results)
    print("\n=== Baseline Results ===\n")
    print(report.to_string(index=False))

    # Skill Score vs ForecastDayAhead
    print("\n=== Skill Score (vs ForecastDayAhead) ===\n")
    for split in ["validation", "test"]:
        sdf = report[report["split"] == split]
        if len(sdf) == 0:
            continue
        mae_official = sdf[sdf["model"] == "ForecastDayAhead (official)"]["MAE"].values[0]
        for _, row in sdf.iterrows():
            if row["model"] == "ForecastDayAhead (official)":
                continue
            skill = 1 - row["MAE"] / mae_official
            print(f"  {split:12s} | {row['model']:25s} | Skill: {skill:+.3f}")

    # Save report
    report.to_csv(PROC / "baselines_report.csv", index=False)
    print(f"\nSaved to data/processed/baselines_report.csv")


if __name__ == "__main__":
    main()