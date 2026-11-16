"""Walk-Forward Cross-Validation — Baseline vs Seasonality vs Drop is_big_ramp."""
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error
from dateutil.relativedelta import relativedelta

# Load data
df = pd.read_parquet("data/processed/features.parquet")
df["HourUTC"] = pd.to_datetime(df["HourUTC"])
df = df.sort_values("HourUTC").reset_index(drop=True)

# Base features (the 19 canonical ones)
base_features = [
    "forecast_wind_da",
    "lag_1h", "lag_2h", "lag_3h", "lag_6h", "lag_12h", "lag_24h", "lag_48h", "lag_168h",
    "ramp_1h",
    "hour", "day_of_week", "month", "is_weekend",
    "forecast_lag_1h", "forecast_lag_2h", "forecast_lag_24h",
    "is_big_ramp", "is_moderate_ramp",
]

# --- Create the seasonality feature ---
# The ACF showed weak daily (24h) seasonality. We test an explicit interaction.
df["hour_x_lag24"] = df["hour"] * df["lag_24h"]
seasonal_features = base_features + ["hour_x_lag24"]

# --- Define the 3 configurations to test ---
configs = {
    "Baseline (19)": base_features,
    "Drop is_big_ramp (18)": [f for f in base_features if f != "is_big_ramp"],
    "Add Seasonality (20)": seasonal_features
}

# --- Walk-Forward Setup ---
# We test on 2025-01 to 2025-12. Train on all data prior to the test month.
# Example: Test on Jan 2025 -> Train on data up to Dec 2024.
test_periods = pd.date_range(start="2025-01-01", end="2025-12-01", freq="MS")
results = {name: [] for name in configs}

print("Starting Walk-Forward CV...\n")

for test_start in test_periods:
    test_end = test_start + relativedelta(months=1)
    
    # Split
    train_df = df[df["HourUTC"] < test_start]
    test_df = df[(df["HourUTC"] >= test_start) & (df["HourUTC"] < test_end)]
    
    # Skip if not enough data (just in case)
    if len(test_df) == 0 or len(train_df) < 1000:
        continue

    y_train = train_df["error"].values
    y_test = test_df["error"].values

    for name, features in configs.items():
        X_train = train_df[features].values
        X_test = test_df[features].values

        model = lgb.LGBMRegressor(
            n_estimators=500, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1
        )
        
        # Train (we use a 10% validation split for early stopping inside the fold)
        val_size = int(len(X_train) * 0.1)
        model.fit(
            X_train[:-val_size], y_train[:-val_size],
            eval_set=[(X_train[-val_size:], y_train[-val_size:])],
            eval_metric="mae",
            callbacks=[lgb.early_stopping(50, verbose=False)]
        )

        # Predict and evaluate
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        results[name].append(mae)

# --- Summary ---
print(f"{'Config':<25} | {'Mean MAE':<10} | {'Std':<8} | {'Wins'}")
print("-" * 60)

baseline_maes = results["Baseline (19)"]

for name, maes in results.items():
    mean_mae = np.mean(maes)
    std_mae = np.std(maes)
    # Count how many months this config beat the baseline
    wins = sum(1 for a, b in zip(maes, baseline_maes) if a < b) if name != "Baseline (19)" else "-"
    print(f"{name:<25} | {mean_mae:<10.2f} | {std_mae:<8.2f} | {wins} / {len(maes)}")