"""Train LSTM for Energium.

Input:  data/processed/features.parquet
Output: models/lstm_model.keras + reports
"""
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import Input
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import json

PROC = Path("data/processed")
MODELS = Path("models")
MODELS.mkdir(exist_ok=True)

# Config
SEQ_LEN = 24
LSTM_UNITS = 256
DENSE_1 = 20
DENSE_2 = 20
EPOCHS = 50
BATCH_SIZE = 32
PATIENCE = 10
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


def make_sequences(df, seq_len=24):
    """Create sequences for LSTM."""
    X, y, meta = [], [], []
    for i in range(seq_len, len(df)):
        X.append(df[FEATURE_COLS].iloc[i-seq_len:i].values)
        y.append(df["error"].iloc[i])
        meta.append(df["HourUTC"].iloc[i])
    return np.array(X), np.array(y), np.array(meta)


def main():
    # Seed for reproducibility
    tf.random.set_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    print("Loading features...")
    df = pd.read_parquet(PROC / "features.parquet")
    df = df.sort_values("HourUTC").reset_index(drop=True)
    print(f"  → {len(df)} rows")

    # Split first (before scaling!)
    train_df = df[df["split"] == "train"].copy()
    val_df = df[df["split"] == "validation"].copy()
    test_df = df[df["split"] == "test"].copy()

    print(f"  Train: {len(train_df)}")
    print(f"  Validation: {len(val_df)}")
    print(f"  Test: {len(test_df)}")

    # Scale features (fit on train only!)
    scaler = StandardScaler()
    scaler.fit(train_df[FEATURE_COLS])

    for sdf in [train_df, val_df, test_df]:
        sdf[FEATURE_COLS] = scaler.transform(sdf[FEATURE_COLS])

    # Create sequences
    print("\nCreating sequences...")
    X_train, y_train, _ = make_sequences(train_df, SEQ_LEN)
    X_val, y_val, _ = make_sequences(val_df, SEQ_LEN)
    X_test, y_test, test_hours = make_sequences(test_df, SEQ_LEN)

    print(f"  X_train: {X_train.shape}")
    print(f"  X_val: {X_val.shape}")
    print(f"  X_test: {X_test.shape}")

    # Model
    print("\nBuilding model...")
    model = Sequential([
        Input(shape=(SEQ_LEN, len(FEATURE_COLS))),
        LSTM(LSTM_UNITS),
        Dense(DENSE_1, activation='sigmoid'),
        Dense(DENSE_2, activation='relu'),
        Dense(1, activation='linear'),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='mae',
        metrics=['mae'],
    )

    model.summary()

    # Callbacks
    callbacks = [
        EarlyStopping(
            patience=PATIENCE,
            restore_best_weights=True,
            monitor='val_loss',
        ),
    ]

    # Train
    print("\nTraining...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1,
    )

    # Evaluate
    print("\n=== Evaluation ===")
    results = {}
    for name, X, y in [("Train", X_train, y_train),
                        ("Validation", X_val, y_val),
                        ("Test", X_test, y_test)]:
        loss, mae = model.evaluate(X, y, verbose=0)
        results[name] = float(mae)
        print(f"  {name:12s} | MAE: {mae:.2f}")

    # Save
    model.save(MODELS / "lstm_model.keras")
    print(f"\nSaved to {MODELS / 'lstm_model.keras'}")

    # Save history
    history_dict = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    with open(MODELS / "lstm_history.json", "w") as f:
        json.dump(history_dict, f, indent=2)

    # Save results
    with open(MODELS / "lstm_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nDone.")


if __name__ == "__main__":
    main()