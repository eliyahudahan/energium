"""Compare LSTM predictions vs Energinet forecast on specific hours.

Input:  data/processed/features.parquet + models/lstm_model.keras
Output: console comparison + docs/PREDICTIONS_COMPARISON.md
"""
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import numpy as np
import pandas as pd
import tensorflow as tf
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
    # Load
    df = pd.read_parquet(PROC / "features.parquet")
    df = df.sort_values("HourUTC").reset_index(drop=True)

    # Split
    train_df = df[df["split"] == "train"].copy()
    test_df = df[df["split"] == "test"].copy()

    # ⚠️ KEEP ORIGINAL forecast values BEFORE scaling
    test_original = test_df.copy()  # ← שמירה על הערכים המקוריים

    # Scale (fit on train only)
    scaler = StandardScaler()
    scaler.fit(train_df[FEATURE_COLS])

    test_df[FEATURE_COLS] = scaler.transform(test_df[FEATURE_COLS])

    # Sequences
    X_test, y_test, test_hours = make_sequences(test_df, SEQ_LEN)

    # Load model
    model = tf.keras.models.load_model(MODELS / "lstm_model.keras")

    # Predict
    y_pred_error = model.predict(X_test, verbose=0).flatten()

    # Build comparison using ORIGINAL (unscaled) values
    test_target = test_original.iloc[SEQ_LEN:].reset_index(drop=True)

    comparison = pd.DataFrame({
        "HourUTC": test_hours,
        "actual": test_target["actual_wind_mwh"].values,          # original
        "forecast_energinet": test_target["forecast_wind_da"].values,  # original ✓
        "predicted_error": y_pred_error,
    })
    comparison["corrected_forecast"] = (
        comparison["forecast_energinet"] + comparison["predicted_error"]
    )

    # Errors
    comparison["error_energinet"] = (
        comparison["actual"] - comparison["forecast_energinet"]
    )
    comparison["error_corrected"] = (
        comparison["actual"] - comparison["corrected_forecast"]
    )
    comparison["abs_error_energinet"] = comparison["error_energinet"].abs()
    comparison["abs_error_corrected"] = comparison["error_corrected"].abs()

    # Show first 20 rows
    print("\n=== First 20 hours of test (January 2026) ===\n")
    cols = [
        "HourUTC", "actual", "forecast_energinet",
        "predicted_error", "corrected_forecast",
        "abs_error_energinet", "abs_error_corrected",
    ]
    print(comparison[cols].head(20).to_string(index=False))

    # MAE comparison
    mae_energinet = comparison["abs_error_energinet"].mean()
    mae_corrected = comparison["abs_error_corrected"].mean()
    skill = 1 - mae_corrected / mae_energinet

    print(f"\n=== MAE comparison ===")
    print(f"  Energinet forecast MAE:    {mae_energinet:.2f} MWh")
    print(f"  Corrected forecast MAE:    {mae_corrected:.2f} MWh")
    print(f"  Skill Score:               {skill:+.4f} ({skill*100:+.2f}%)")

    # Save to markdown
    DOCS.mkdir(exist_ok=True)
    with open(DOCS / "PREDICTIONS_COMPARISON.md", "w") as f:
        f.write("# Predictions Comparison — Test Set (January 2026)\n\n")
        f.write("## First 20 hours\n\n")
        f.write(comparison[cols].head(20).to_markdown(index=False))
        f.write(f"\n\n## MAE comparison\n\n")
        f.write(f"| Model | MAE (MWh) |\n")
        f.write(f"|---|---|\n")
        f.write(f"| Energinet forecast | {mae_energinet:.2f} |\n")
        f.write(f"| **Corrected (ours)** | **{mae_corrected:.2f}** |\n")
        f.write(f"\n**Skill Score: {skill:+.4f} ({skill*100:+.2f}%)**\n")

    print(f"\nSaved to {DOCS / 'PREDICTIONS_COMPARISON.md'}")


if __name__ == "__main__":
    main()