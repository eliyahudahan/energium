"""Statistical tests: Diebold-Mariano (DM) test for forecast comparison."""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from scipy import stats

PROC = Path("data/processed")
MODELS = Path("models")

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
    test_original = test_df.copy()

    # Scale
    scaler = StandardScaler()
    scaler.fit(train_df[FEATURE_COLS])
    test_df[FEATURE_COLS] = scaler.transform(test_df[FEATURE_COLS])

    # Load model
    with open(MODELS / "lgbm_model.pkl", "rb") as f:
        lgbm_model = pickle.load(f)

    # Predict
    pred_errors = lgbm_model.predict(test_df[FEATURE_COLS].values)
    corrected = test_original['forecast_wind_da'].values + pred_errors
    
    # Calculate squared errors (standard for DM test)
    e1 = (test_original['actual_wind_mwh'].values - test_original['forecast_wind_da'].values) ** 2 # Energinet
    e2 = (test_original['actual_wind_mwh'].values - corrected) ** 2 # Our model

    d = e1 - e2 # Loss differential
    mean_d = np.mean(d)
    
    # DM test statistic (simplified, assuming h=1)
    n = len(d)
    var_d = np.var(d, ddof=1) / n
    dm_stat = mean_d / np.sqrt(var_d)
    
    # Two-sided p-value (normal approximation)
    p_value = 2 * (1 - stats.norm.cdf(abs(dm_stat)))

    print("=== Diebold-Mariano Test ===")
    print(f"Null hypothesis: Energinet and LightGBM have equal forecast accuracy.")
    print(f"DM statistic: {dm_stat:.4f}")
    print(f"p-value: {p_value:.6f}")
    
    if p_value < 0.05:
        print("Result: Reject the null hypothesis. The difference is statistically significant.")
    else:
        print("Result: Fail to reject the null. The difference is not statistically significant.")

    # Daily MAE breakdown (Robustness check)
    print("\n=== Robustness: MAE by Day in January 2026 ===")
    test_original['corrected'] = corrected
    test_original['HourUTC'] = pd.to_datetime(test_original['HourUTC'])
    test_original['day'] = test_original['HourUTC'].dt.day
    
    test_original['err_energinet'] = np.abs(test_original['actual_wind_mwh'] - test_original['forecast_wind_da'])
    test_original['err_model'] = np.abs(test_original['actual_wind_mwh'] - test_original['corrected'])
    
    daily_mae = test_original.groupby('day')[['err_energinet', 'err_model']].mean().round(2)
    print(daily_mae.to_string())

if __name__ == "__main__":
    main()