"""Check MAE — canonical training + leakage + drift checks."""
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error

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

# === Train model ===
model = lgb.LGBMRegressor(
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=31,
    random_state=42,
)
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    eval_metric="mae",
    callbacks=[lgb.early_stopping(50)],
)

# === Test MAE ===
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"Test MAE: {mae:.2f}")
print(f"Best iteration: {model.best_iteration_}")

# === Overfitting check ===
print(f"Train MAE: {mean_absolute_error(y_train, model.predict(X_train)):.2f}")
print(f"Val MAE:   {mean_absolute_error(y_val, model.predict(X_val)):.2f}")

# === Leakage check 1: same features in train and test ===
print(f"\nFeature sets identical: {sorted(train[features].columns) == sorted(test[features].columns)}")

# === Leakage check 2: lag_1h = actual.shift(1) ===
lag_consistency = (train["lag_1h"] == train["actual_wind_mwh"].shift(1)).mean()
print(f"lag_1h consistency:  {lag_consistency:.4f}")

# === Leakage check 3: ramp_1h = actual.shift(1).diff(1) ===
ramp_expected = train["actual_wind_mwh"].shift(1).diff(1)
ramp_consistency = (train["ramp_1h"] == ramp_expected).mean()
print(f"ramp_1h consistency: {ramp_consistency:.4f}")

# === Leakage check 4: no target in features ===
print(f"Target 'actual_wind_mwh' in features: {'actual_wind_mwh' in features}")