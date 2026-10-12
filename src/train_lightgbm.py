"""Train LightGBM for Energium.

Input:  data/processed/features.parquet
Output: models/lgbm_model.pkl + reports
"""
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
from pathlib import Path
import json
import pickle

PROC = Path("data/processed")
MODELS = Path("models")
MODELS.mkdir(exist_ok=True)

# Config
N_ESTIMATORS = 500
LEARNING_RATE = 0.05
MAX_DEPTH = 6
NUM_LEAVES = 31
EARLY_STOPPING = 50
RANDOM_SEED = 42

FEATURE_COLS = [
    "forecast_wind_da",
    "lag_1h", "lag_2h", "lag_3h", "lag_6h",
    "lag_12h", "lag_24h", "lag_48h", "lag_168h",
    "mean_3h", "std_3h", "mean_6h", "std_6h",
    "mean_24h", "std_24h",
    "ramp_1h",
    "hour", "day_of_week", "month", "is_weekend",
    "forecast_lag_1h", "forecast_lag_2h", "forecast_lag_24h",
]


def main():
    print("Loading features...")
    df = pd.read_parquet(PROC / "features.parquet")
    df = df.sort_values("HourUTC").reset_index(drop=True)
    print(f"  → {len(df)} rows")

    # Split
    train_df = df[df["split"] == "train"].copy()
    val_df = df[df["split"] == "validation"].copy()
    test_df = df[df["split"] == "test"].copy()

    print(f"  Train: {len(train_df)}")
    print(f"  Validation: {len(val_df)}")
    print(f"  Test: {len(test_df)}")

    # Features and target
    X_train = train_df[FEATURE_COLS].values
    y_train = train_df["error"].values

    X_val = val_df[FEATURE_COLS].values
    y_val = val_df["error"].values

    X_test = test_df[FEATURE_COLS].values
    y_test = test_df["error"].values

    # Scale (fit on train only)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # Train
    print("\nTraining LightGBM...")
    model = lgb.LGBMRegressor(
        n_estimators=N_ESTIMATORS,
        learning_rate=LEARNING_RATE,
        max_depth=MAX_DEPTH,
        num_leaves=NUM_LEAVES,
        random_state=RANDOM_SEED,
        verbose=-1,
    )

    # Use eval_X and eval_y (new API, no deprecation)
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_val_scaled, y_val)],
        eval_metric='mae',
        callbacks=[
            lgb.early_stopping(EARLY_STOPPING, verbose=False),
            lgb.log_evaluation(period=50),
        ],
    )

    print(f"\nBest iteration: {model.best_iteration_}")

    # Evaluate on error prediction
    print("\n=== Evaluation (error prediction) ===")
    results = {}
    for name, X, y in [("Train", X_train_scaled, y_train),
                        ("Validation", X_val_scaled, y_val),
                        ("Test", X_test_scaled, y_test)]:
        y_pred = model.predict(X)
        mae_error = mean_absolute_error(y, y_pred)
        results[name] = float(mae_error)
        print(f"  {name:12s} | MAE (error): {mae_error:.2f}")

    # Evaluate on forecast correction
    print("\n=== Evaluation (forecast correction) ===")
    for name, X, y_true, df_split in [
        ("Train", X_train_scaled, train_df["actual_wind_mwh"].values, train_df),
        ("Validation", X_val_scaled, val_df["actual_wind_mwh"].values, val_df),
        ("Test", X_test_scaled, test_df["actual_wind_mwh"].values, test_df),
    ]:
        y_error_pred = model.predict(X)
        corrected_forecast = df_split["forecast_wind_da"].values + y_error_pred
        mae_corrected = mean_absolute_error(y_true, corrected_forecast)
        mae_energinet = mean_absolute_error(y_true, df_split["forecast_wind_da"].values)
        skill = 1 - mae_corrected / mae_energinet
        print(f"  {name:12s} | MAE corrected: {mae_corrected:.2f} | Skill vs Energinet: {skill:+.4f}")

    # Save model
    with open(MODELS / "lgbm_model.pkl", "wb") as f:
        pickle.dump(model, f)
    print(f"\nSaved to {MODELS / 'lgbm_model.pkl'}")

    # Save scaler
    with open(MODELS / "lgbm_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    # Feature importance
    print("\n=== Feature Importance (top 10) ===")
    importance = pd.DataFrame({
        "feature": FEATURE_COLS,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    print(importance.head(10).to_string(index=False))

    # Save results
    with open(MODELS / "lgbm_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nDone.")


if __name__ == "__main__":
    main()