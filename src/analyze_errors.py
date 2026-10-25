"""Analyze where LightGBM errors occur in the test set."""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.preprocessing import StandardScaler

PROC = Path("data/processed")
MODELS = Path("models")

# Same features as training
FEATURE_COLS = [
    "forecast_wind_da", "lag_1h", "lag_2h", "lag_3h", "lag_6h",
    "lag_12h", "lag_24h", "lag_48h", "lag_168h",
    "mean_3h", "std_3h", "mean_6h", "std_6h", "mean_24h", "std_24h",
    "ramp_1h", "hour", "day_of_week", "month", "is_weekend",
    "forecast_lag_1h", "forecast_lag_2h", "forecast_lag_24h",
]

def main():
    df = pd.read_parquet(PROC / "features.parquet")
    df = df.sort_values("HourUTC").reset_index(drop=True)

    train_df = df[df["split"] == "train"].copy()
    test_df = df[df["split"] == "test"].copy()

    # 1. Keep original unscaled values for error calculation
    test_original = test_df.copy()

    # 2. Scale using train
    scaler = StandardScaler()
    scaler.fit(train_df[FEATURE_COLS])
    test_df[FEATURE_COLS] = scaler.transform(test_df[FEATURE_COLS])

    # 3. Load LightGBM
    with open(MODELS / "lgbm_model.pkl", "rb") as f:
        lgbm_model = pickle.load(f)

    # 4. Predict on test
    pred_errors = lgbm_model.predict(test_df[FEATURE_COLS].values)
    
    # 5. Calculate errors using ORIGINAL unscaled values
    test_df = test_df.copy()
    test_df['predicted_error'] = pred_errors
    test_df['corrected'] = test_original['forecast_wind_da'].values + test_df['predicted_error'].values
    # FIX: Use np.abs() instead of .abs() because we are working with numpy arrays
    test_df['abs_error'] = np.abs(test_original['actual_wind_mwh'].values - test_df['corrected'].values)

    # 6. Print analysis
    print("=== Error by Hour of Day ===")
    print(test_df.groupby("hour")["abs_error"].mean().round(2).to_string())

    print("\n=== Error by Wind Regime (actual generation) ===")
    bins = [0, 1000, 2500, 5000, 10000]
    labels = ["Low (<1GWh)", "Medium (1-2.5GWh)", "High (2.5-5GWh)", "Very High (>5GWh)"]
    test_df["wind_regime"] = pd.cut(test_df["actual_wind_mwh"], bins=bins, labels=labels)
    print(test_df.groupby("wind_regime")["abs_error"].mean().round(2).to_string())

    print("\n=== Top 5 Worst Predictions ===")
    worst = test_df.nlargest(5, "abs_error")[["HourUTC", "actual_wind_mwh", "forecast_wind_da", "corrected", "abs_error"]]
    print(worst.to_string(index=False))

if __name__ == "__main__":
    main()