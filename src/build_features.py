"""Build features for Energium.

Input:  data/processed/merged_clean.parquet
Output: data/processed/features.parquet

AR lags follow Jørgensen et al. (2025):
    [1, 2, 3, 6, 12, 24, 48]
We add 168 (weekly pattern) as an experiment.
"""
import pandas as pd
from pathlib import Path

PROC = Path("data/processed")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time, lag, rolling, ramp features and error target."""
    df = df.copy().sort_values("HourUTC").reset_index(drop=True)

    # Target
    df["error"] = df["actual_wind_mwh"] - df["forecast_wind_da"]

    # Time features
    df["hour"] = df["HourUTC"].dt.hour
    df["day_of_week"] = df["HourUTC"].dt.dayofweek
    df["month"] = df["HourUTC"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # Lag features (actual)
    # Jørgensen lags: [1, 2, 3, 6, 12, 24, 48]
    # We add 168 for weekly pattern
    for lag in [1, 2, 3, 6, 12, 24, 48, 168]:
        df[f"lag_{lag}h"] = df["actual_wind_mwh"].shift(lag)

    # Rolling features
    for window in [3, 6, 24]:
        df[f"mean_{window}h"] = df["actual_wind_mwh"].rolling(window).mean()
        df[f"std_{window}h"] = df["actual_wind_mwh"].rolling(window).std()

    # Ramp
    df["ramp_1h"] = df["actual_wind_mwh"].diff(1)

    # Forecast lags
    for lag in [1, 2, 24]:
        df[f"forecast_lag_{lag}h"] = df["forecast_wind_da"].shift(lag)

    return df


def main():
    print("Loading merged_clean.parquet...")
    df = pd.read_parquet(PROC / "merged_clean.parquet")
    print(f"  → {len(df)} rows")

    print("Building features...")
    df = build_features(df)

    # Drop rows with NaN:
    # 1. lag_168h — first 168 hours have no history
    # 2. forecast_wind_da — 48 hours (2 days) missing from Energinet API
    #    (2024-05-31 22:00 → 2024-06-01 21:00,
    #     2025-02-25 23:00 → 2025-02-26 22:00)
    # All in train split — no impact on validation/test.
    before = len(df)
    nan_cols = df.isnull().sum()
    nan_cols = nan_cols[nan_cols > 0]
    print("  NaN per column:")
    for col, count in nan_cols.items():
        print(f"    {col}: {count}")

    df = df.dropna().reset_index(drop=True)
    after = len(df)
    print(f"  → dropped {before - after} rows with NaN")
    print(f"  → {after} rows remaining")

    # Save
    out = PROC / "features.parquet"
    df.to_parquet(out)
    print(f"\nSaved to {out}")
    print(f"  Columns: {len(df.columns)}")

    feature_cols = [
        c for c in df.columns
        if c not in ["HourUTC", "PriceArea", "split"]
    ]
    print(f"  Features: {feature_cols}")

    # Split counts
    print()
    print("Split counts:")
    print(df["split"].value_counts().sort_index())


if __name__ == "__main__":
    main()