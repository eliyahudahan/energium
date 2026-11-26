"""Walk-Forward Cross-Validation — Baseline vs Seasonality vs Drop is_big_ramp."""
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error
from dateutil.relativedelta import relativedelta


def load_and_prepare_data(filepath: str) -> pd.DataFrame:
    """Load parquet data, sort chronologically, and add interaction feature."""
    df = pd.read_parquet(filepath)
    df["HourUTC"] = pd.to_datetime(df["HourUTC"])
    df = df.sort_values("HourUTC").reset_index(drop=True)
    df["hour_x_lag24"] = df["hour"] * df["lag_24h"]
    return df


def get_monthly_split(
    df: pd.DataFrame, test_start: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split data chronologically into expanding train set and 1-month test set."""
    test_end = test_start + relativedelta(months=1)
    train_df = df[df["HourUTC"] < test_start]
    test_df = df[(df["HourUTC"] >= test_start) & (df["HourUTC"] < test_end)]
    return train_df, test_df


def train_and_evaluate_fold(
    train_df: pd.DataFrame, test_df: pd.DataFrame, features: list[str]
) -> float:
    """Train LightGBM with chronological 10% early-stopping split and return test MAE."""
    X_train, y_train = train_df[features].values, train_df["error"].values
    X_test, y_test = test_df[features].values, test_df["error"].values

    model = lgb.LGBMRegressor(
        n_estimators=500, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1
    )

    val_size = int(len(X_train) * 0.1)
    model.fit(
        X_train[:-val_size],
        y_train[:-val_size],
        eval_X=X_train[-val_size:],
        eval_y=y_train[-val_size:],
        eval_metric="mae",
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )

    preds = model.predict(X_test)
    return float(mean_absolute_error(y_test, preds))


def run_walk_forward_cv() -> None:
    """Run 12-fold expanding-window CV across 2025 and print comparison summary."""
    df = load_and_prepare_data("data/processed/features.parquet")

    base_features = [
        "forecast_wind_da",
        "lag_1h", "lag_2h", "lag_3h", "lag_6h", "lag_12h", "lag_24h", "lag_48h", "lag_168h",
        "ramp_1h",
        "hour", "day_of_week", "month", "is_weekend",
        "forecast_lag_1h", "forecast_lag_2h", "forecast_lag_24h",
        "is_big_ramp", "is_moderate_ramp",
    ]

    configs = {
        "Baseline (19)": base_features,
        "Drop is_big_ramp (18)": [f for f in base_features if f != "is_big_ramp"],
        "Add Seasonality (20)": base_features + ["hour_x_lag24"],
    }

    test_periods = pd.date_range(start="2025-01-01", end="2025-12-01", freq="MS")
    results = {name: [] for name in configs}

    print("Starting Walk-Forward CV...\n")

    for test_start in test_periods:
        train_df, test_df = get_monthly_split(df, test_start)
        if len(test_df) == 0 or len(train_df) < 1000:
            continue

        for name, features in configs.items():
            mae = train_and_evaluate_fold(train_df, test_df, features)
            results[name].append(mae)

    print(f"{'Config':<25} | {'Mean MAE':<10} | {'Std':<8} | {'Wins'}")
    print("-" * 60)

    baseline_maes = results["Baseline (19)"]
    for name, maes in results.items():
        mean_mae = np.mean(maes)
        std_mae = np.std(maes)
        wins = sum(1 for a, b in zip(maes, baseline_maes) if a < b) if name != "Baseline (19)" else "-"
        print(f"{name:<25} | {mean_mae:<10.2f} | {std_mae:<8.2f} | {wins} / {len(maes)}")

times = [
    pd.Timestamp("2025-01-01 08:00"),
    pd.Timestamp("2025-01-01 09:00"),
    pd.Timestamp("2025-01-01 11:00"),
]

def show_diffs(times):
    for i in range(1, len(times)):
        print((i, times[i] - times[i-1]))

show_diffs(times)

if __name__ == "__main__":
    run_walk_forward_cv()
