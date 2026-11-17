"""Check MAE — canonical training + leakage + drift checks."""
import joblib
import lightgbm as lgb
import pandas as pd
from scipy.stats import ks_2samp
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

# === Leakage checks (with strict assertions) ===
same_cols = sorted(train[features].columns) == sorted(test[features].columns)
lag_consistency = (train["lag_1h"] == train["actual_wind_mwh"].shift(1)).mean()
ramp_expected = train["actual_wind_mwh"].shift(1).diff(1)
ramp_consistency = (train["ramp_1h"] == ramp_expected).mean()
target_in_features = "actual_wind_mwh" in features

print(f"\nFeature sets identical: {same_cols}")
print(f"lag_1h consistency:  {lag_consistency:.4f}")
print(f"ramp_1h consistency: {ramp_consistency:.4f}")
print(f"Target 'actual_wind_mwh' in features: {target_in_features}")

assert same_cols, "Leakage check failed: feature mismatch between train and test!"
assert lag_consistency > 0.999, f"Leakage check failed in lag_1h: {lag_consistency:.4f}"
assert ramp_consistency > 0.999, f"Leakage check failed in ramp_1h: {ramp_consistency:.4f}"
assert not target_in_features, "Leakage check failed: target found in features!"

# === Drift checks (KS-test: All Train vs. Seasonal January Cohort) ===
print("\n=== Distribution Drift Checks (KS-Test) ===")
drift_features = ["lag_1h", "forecast_wind_da", "lag_24h", "lag_168h"]
train_jan = train[train["month"] == 1]

for col in drift_features:
    ks_all, p_all = ks_2samp(train[col].dropna(), test[col].dropna())
    ks_jan, p_jan = ks_2samp(train_jan[col].dropna(), test[col].dropna())
    print(
        f"{col:18s} | vs All Train: KS={ks_all:.3f} (p={p_all:.4f}) "
        f"| vs Train Jan: KS={ks_jan:.3f} (p={p_jan:.4f})"
    )

# === Saved artifact verification ===
print("\n=== Saved Model Artifact Check ===")
m = joblib.load("models/lgbm_model.pkl")
print("n_features:", m.n_features_in_)
print("best_iteration:", m.best_iteration_)
print("params:", m.get_params())
assert m.n_features_in_ == len(features), "Saved model feature count mismatch!"
