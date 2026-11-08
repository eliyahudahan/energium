import streamlit as st
import pandas as pd
import pickle
import plotly.express as px

# === 3 השאלות (ניר עציון) ===
st.title("🌿 Energium — Denmark Wind Forecast Correction")

st.markdown("""
### 1. What is the problem?
Energinet publishes an official day-ahead wind forecast. This project tests whether an ML model can correct it.

### 2. What are the principles?
Based on 16,992 hours of wind generation (2024-2026) against the official forecast. The model learns the error and corrects it.

### 3. What is the success rate?
MAE = 97.29 MWh vs 645.24 for Energinet — an 84.9% improvement.
""")

@st.cache_data
def load_data():
    df = pd.read_parquet("data/processed/features.parquet")
    with open("models/lgbm_model.pkl", "rb") as f:
        model = pickle.load(f)
    return df, model

df, model = load_data()

# === Filter test set ===
test = df[df["split"] == "test"].copy()


features = [
    "forecast_wind_da",
    "lag_1h", "lag_2h", "lag_3h", "lag_6h", "lag_12h", "lag_24h", "lag_48h", "lag_168h",
    "ramp_1h",
    "hour", "day_of_week", "month", "is_weekend",
    "forecast_lag_1h", "forecast_lag_2h", "forecast_lag_24h",
    "is_big_ramp", "is_moderate_ramp",
]

# === Predict and correct ===
test["predicted_error"] = model.predict(test[features])
test["corrected"] = test["forecast_wind_da"] + test["predicted_error"]
test["corrected_error"] = test["actual_wind_mwh"] - test["corrected"]

st.write(f"Test set: {len(test)} hours (January 2026)")

# === MAE comparison ===
energinet_mae = test["error"].abs().mean()
model_mae = test["corrected_error"].abs().mean()
st.write(f"Energinet MAE: {energinet_mae:.2f} MWh")
st.write(f"Model MAE: {model_mae:.2f} MWh")

# === Anomalies based on corrected error ===
mae = test["corrected_error"].abs().mean()
threshold_mae = 2 * mae
anomalies_mae = test[test["corrected_error"].abs() > threshold_mae]
st.write(f"Anomalies (2×MAE = {threshold_mae:.1f} MWh): {len(anomalies_mae)} hours")

# === Graph: actual vs forecast ===
test = test.set_index("HourUTC")
fig = px.line(
    test.reset_index(),
    x="HourUTC",
    y=["actual_wind_mwh", "corrected"],
    title="Actual vs Corrected — January 2026",
    labels={"value": "MWh", "variable": "Source"},
)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(anomalies_mae[["HourUTC", "actual_wind_mwh", "forecast_wind_da", "corrected", "corrected_error"]].sort_values("HourUTC"))

from statsmodels.tsa.stattools import acf
import numpy as np

residuals = test["corrected_error"].dropna()
acf_vals = acf(residuals, nlags=24)
st.write(f"ACF lag-1: {acf_vals[1]:.3f}")
st.write(f"ACF lag-2: {acf_vals[2]:.3f}")
st.write(f"ACF lag-3: {acf_vals[3]:.3f}")