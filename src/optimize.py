"""Optimize LightGBM hyperparameters with Optuna + TimeSeriesSplit."""
import pandas as pd
import numpy as np
import lightgbm as lgb
import optuna
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error

# Load data
df = pd.read_parquet("data/processed/features.parquet")
train = df[df["split"] == "train"]
val = df[df["split"] == "validation"]
test = df[df["split"] == "test"]

features = [
    "forecast_wind_da",
    "lag_1h", "lag_2h", "lag_3h", "lag_6h", "lag_12h", "lag_24h", "lag_48h", "lag_168h",
    "ramp_1h",
    "hour", "day_of_week", "month", "is_weekend",
    "forecast_lag_1h", "forecast_lag_2h", "forecast_lag_24h",
    "is_big_ramp", "is_moderate_ramp",
]

X_train = train[features].values
y_train = train["error"].values
X_val = val[features].values
y_val = val["error"].values
X_test = test[features].values
y_test = test["error"].values

# TimeSeriesSplit on training data
tscv = TimeSeriesSplit(n_splits=3)


def objective(trial):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 200, 800),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.08, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 15, 63),
        "min_child_samples": trial.suggest_int("min_child_samples", 20, 60),
        "subsample": trial.suggest_float("subsample", 0.6, 0.9),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 0.9),
        "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 0.3),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 0.3),
        "random_state": 42,
        "verbose": -1,
    }
    scores = []
    for train_idx, val_idx in tscv.split(X_train):
        X_tr, X_va = X_train[train_idx], X_train[val_idx]
        y_tr, y_va = y_train[train_idx], y_train[val_idx]
        m = lgb.LGBMRegressor(**params)
        m.fit(
            X_tr, y_tr,
            eval_set=[(X_va, y_va)],
            eval_metric="mae",
            callbacks=[lgb.early_stopping(50, verbose=False)],
        )
        scores.append(mean_absolute_error(y_va, m.predict(X_va)))
    return np.mean(scores)


study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=50)

print("\n=== Best params ===")
print(study.best_params)
print(f"Best CV MAE: {study.best_value:.2f}")

# Train final model with best params on full train, evaluate on val + test
best_params = study.best_params
best_params["random_state"] = 42
best_params["verbose"] = -1

final_model = lgb.LGBMRegressor(**best_params)
final_model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    eval_metric="mae",
    callbacks=[lgb.early_stopping(50)],
)

print("\n=== Final model ===")
print(f"Train MAE: {mean_absolute_error(y_train, final_model.predict(X_train)):.2f}")
print(f"Val MAE:   {mean_absolute_error(y_val, final_model.predict(X_val)):.2f}")
print(f"Test MAE:  {mean_absolute_error(y_test, final_model.predict(X_test)):.2f}")
print(f"Best iteration: {final_model.best_iteration_}")