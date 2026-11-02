"""Check MAE — reproduce terminal result in a file."""
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

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"MAE: {mae:.2f}")
print(f"Best iteration: {model.best_iteration_}")