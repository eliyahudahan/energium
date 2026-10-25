"""Compare LSTM and LightGBM predictions vs Energinet forecast.

Input:  data/processed/features.parquet + models/lstm_model.keras + models/lgbm_model.pkl
Output: console comparison + docs/PREDICTIONS_COMPARISON.md
"""
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import numpy as np
import pandas as pd
import tensorflow as tf
import pickle
from sklearn.preprocessing import StandardScaler
from pathlib import Path

PROC = Path("data/processed")
MODELS = Path("models")
DOCS = Path("docs")

SEQ_LEN = 24
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


def make_sequences(df, seq_len=24):
    X, y, meta = [], [], []
    for i in range(seq_len, len(df)):
        X.append(df[FEATURE_COLS].iloc[i-seq_len:i].values)
        y.append(df["error"].iloc[i])
        meta.append(df["HourUTC"].iloc[i])
    return np.array(X), np.array(y), np.array(meta)


def main():
    df = pd.read_parquet(PROC / "features.parquet")
    df = df.sort_values("HourUTC").reset_index(drop=True)

    train_df = df[df["split"] == "train"].copy()
    test_df = df[df["split"] == "test"].copy()

    # Keep original values
    test_original = test_df.copy()

    # Scale
    scaler = StandardScaler()
    scaler.fit(train_df[FEATURE_COLS])
    test_df[FEATURE_COLS] = scaler.transform(test_df[FEATURE_COLS])

    # Prepare inputs
    X_test_seq, _, test_hours = make_sequences(test_df, SEQ_LEN)
    X_test_flat = test_df[FEATURE_COLS].values

    # Test target (skip first SEQ_LEN for LSTM, use all for LGBM)
    test_target_lstm = test_original.iloc[SEQ_LEN:].reset_index(drop=True)
    test_target_lgbm = test_original.reset_index(drop=True)

    # Load LSTM
    print("Loading LSTM...")
    lstm_model = tf.keras.models.load_model(MODELS / "lstm_model.keras")
    lstm_errors = lstm_model.predict(X_test_seq, verbose=0).flatten()

    # Load LightGBM
    print("Loading LightGBM...")
    with open(MODELS / "lgbm_model.pkl", "rb") as f:
        lgbm_model = pickle.load(f)
    lgbm_errors = lgbm_model.predict(X_test_flat)

    # Build comparison
    # Note: LSTM starts at hour 24, LGBM at hour 0
    # Align both for fair comparison: use LSTM's window

    # LSTM comparison
    comp_lstm = pd.DataFrame({
        "HourUTC": test_hours,
        "actual": test_target_lstm["actual_wind_mwh"].values,
        "forecast_energinet": test_target_lstm["forecast_wind_da"].values,
        "predicted_error_lstm": lstm_errors,
    })
    comp_lstm["corrected_lstm"] = (
        comp_lstm["forecast_energinet"] + comp_lstm["predicted_error_lstm"]
    )
    comp_lstm["abs_error_energinet"] = (
        comp_lstm["actual"] - comp_lstm["forecast_energinet"]
    ).abs()
    comp_lstm["abs_error_lstm"] = (
        comp_lstm["actual"] - comp_lstm["corrected_lstm"]
    ).abs()

        # LightGBM comparison (align by HourUTC, not by array slicing)
    comp_lgbm = pd.DataFrame({
        "HourUTC": test_target_lgbm["HourUTC"].values,
        "predicted_error_lgbm": lgbm_errors,
    })

    # Merge by HourUTC to ensure perfect alignment, then drop NaNs
    comparison = comp_lstm.merge(comp_lgbm, on="HourUTC", how="inner")

    # Now compute the corrected LGBM values using the aligned forecast
    comparison["corrected_lgbm"] = (
        comparison["forecast_energinet"] + comparison["predicted_error_lgbm"]
    )
    comparison["abs_error_lgbm"] = (
        comparison["actual"] - comparison["corrected_lgbm"]
    ).abs()
    
    # Show first 20 rows
    print("\n=== First 20 hours of test (January 2026) ===\n")
    cols = [
        "HourUTC", "actual", "forecast_energinet",
        "corrected_lstm", "corrected_lgbm",
        "abs_error_energinet", "abs_error_lstm", "abs_error_lgbm",
    ]
    print(comparison[cols].head(20).to_string(index=False))

    # MAE comparison
    mae_energinet = comparison["abs_error_energinet"].mean()
    mae_lstm = comparison["abs_error_lstm"].mean()
    mae_lgbm = comparison["abs_error_lgbm"].mean()

    skill_lstm = 1 - mae_lstm / mae_energinet
    skill_lgbm = 1 - mae_lgbm / mae_energinet

    print(f"\n=== MAE comparison ===")
    print(f"  Energinet forecast MAE:    {mae_energinet:.2f} MWh")
    print(f"  LSTM MAE:                  {mae_lstm:.2f} MWh  | Skill: {skill_lstm:+.4f}")
    print(f"  LightGBM MAE:              {mae_lgbm:.2f} MWh  | Skill: {skill_lgbm:+.4f}")

    # Winner
    if mae_lstm < mae_lgbm:
        print(f"\n  🏆 Winner: LSTM (by {mae_lgbm - mae_lstm:.2f} MWh)")
    elif mae_lgbm < mae_lstm:
        print(f"\n  🏆 Winner: LightGBM (by {mae_lstm - mae_lgbm:.2f} MWh)")
    else:
        print(f"\n  🤝 Tie")

    # Save
    DOCS.mkdir(exist_ok=True)
    with open(DOCS / "PREDICTIONS_COMPARISON.md", "w") as f:
        f.write("# Predictions Comparison — Test Set (January 2026)\n\n")
        f.write("## First 20 hours\n\n")
        f.write(comparison[cols].head(20).to_markdown(index=False))
        f.write(f"\n\n## MAE comparison\n\n")
        f.write(f"| Model | MAE (MWh) | Skill vs Energinet |\n")
        f.write(f"|---|---|---|\n")
        f.write(f"| Energinet forecast | {mae_energinet:.2f} | — |\n")
        f.write(f"| **LSTM** | **{mae_lstm:.2f}** | **{skill_lstm:+.4f}** |\n")
        f.write(f"| **LightGBM** | **{mae_lgbm:.2f}** | **{skill_lgbm:+.4f}** |\n")

    print(f"\nSaved to {DOCS / 'PREDICTIONS_COMPARISON.md'}")


if __name__ == "__main__":
    main()