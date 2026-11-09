import streamlit as st
import pandas as pd
import pickle
import plotly.express as px
from statsmodels.tsa.stattools import acf

# === Title and 3 questions (Nir Etzion) ===
st.title("🌿 Energium — Denmark Wind Forecast Correction")

st.markdown("""
### 1. What is the problem?
Energinet publishes an official day-ahead wind forecast. This project tests whether an ML model can correct it.

### 2. What are the principles?
Based on 16,992 hours of wind generation (2024-2026) against the official forecast. The model learns the error and corrects it.

### 3. What is the success rate?
MAE = 97.29 MWh vs 645.24 for Energinet — an 84.9% improvement.
""")

# === Load data and model (cached — disk read is expensive) ===
@st.cache_data
def load_data():
    df = pd.read_parquet("data/processed/features.parquet")
    with open("models/lgbm_model.pkl", "rb") as f:
        model = pickle.load(f)
    return df, model

df, model = load_data()

# === Feature list — must match training order in check_mae.py ===
# Defined BEFORE any model.predict call, because predict needs it.
features = [
    "forecast_wind_da",
    "lag_1h", "lag_2h", "lag_3h", "lag_6h", "lag_12h", "lag_24h", "lag_48h", "lag_168h",
    "ramp_1h",
    "hour", "day_of_week", "month", "is_weekend",
    "forecast_lag_1h", "forecast_lag_2h", "forecast_lag_24h",
    "is_big_ramp", "is_moderate_ramp",
]

# === Compute threshold on VALIDATION, not test (avoid threshold leakage — Idit's lesson) ===
val = df[df["split"] == "validation"].copy()
val["predicted_error"] = model.predict(val[features])
val["corrected"] = val["forecast_wind_da"] + val["predicted_error"]
val["corrected_error"] = val["actual_wind_mwh"] - val["corrected"]
val_mae = val["corrected_error"].abs().mean()
threshold_mae = 2 * val_mae

# === Filter test set (January 2026, 743 hours) ===
test = df[df["split"] == "test"].copy()

# === Predict residual and apply correction ===
# The model predicts the ERROR (actual - forecast), not the actual value.
# Corrected forecast = official forecast + predicted error.
test["predicted_error"] = model.predict(test[features])
test["corrected"] = test["forecast_wind_da"] + test["predicted_error"]
test["corrected_error"] = test["actual_wind_mwh"] - test["corrected"]

st.write(f"Test set: {len(test)} hours (January 2026)")

# === MAE comparison: Energinet vs corrected model ===
energinet_mae = test["error"].abs().mean()
model_mae = test["corrected_error"].abs().mean()
st.write(f"Energinet MAE: {energinet_mae:.2f} MWh")
st.write(f"Model MAE: {model_mae:.2f} MWh")
st.write(f"Validation MAE (threshold base): {val_mae:.2f} MWh")

# === Anomalies: hours where corrected error > threshold from VAL ===
anomalies_mae = test[test["corrected_error"].abs() > threshold_mae]
st.write(f"Anomalies (2×val MAE = {threshold_mae:.1f} MWh): {len(anomalies_mae)} hours")

# === Graph 1: actual vs Energinet forecast vs corrected ===
fig = px.line(
    test.reset_index(),
    x="HourUTC",
    y=["actual_wind_mwh", "forecast_wind_da", "corrected"],
    title="Actual vs Energinet Forecast vs Corrected — January 2026",
    labels={"value": "MWh", "variable": "Source"},
    color_discrete_map={
        "actual_wind_mwh": "#1f77b4",
        "forecast_wind_da": "#ff7f0e",
        "corrected": "#2ca02c",
    },
)
st.plotly_chart(fig, use_container_width=True)

# === Anomalies table (10 rows for review) ===
st.dataframe(
    anomalies_mae[["HourUTC", "actual_wind_mwh", "forecast_wind_da", "corrected", "corrected_error"]]
    .sort_values("HourUTC")
    .head(10)
)

# === ACF on residuals — checks if error is random or has a pattern ===
residuals = test["corrected_error"].dropna()
acf_vals = acf(residuals, nlags=24)
st.write(f"ACF lag-1: {acf_vals[1]:.3f}")
st.write(f"ACF lag-2: {acf_vals[2]:.3f}")
st.write(f"ACF lag-3: {acf_vals[3]:.3f}")

# === Graph 2: daily MAE (no coordinates in data -> bar chart, not map) ===
test_daily = test.reset_index()
test_daily["date"] = test_daily["HourUTC"].dt.date
daily_mae = (
    test_daily.groupby("date")["corrected_error"]
    .apply(lambda x: x.abs().mean())
    .reset_index()
)
daily_mae.columns = ["date", "mae"]

fig_daily = px.bar(
    daily_mae,
    x="date",
    y="mae",
    color="mae",
    color_continuous_scale="RdYlGn_r",
    title="Daily MAE — January 2026",
    labels={"mae": "MAE (MWh)", "date": "Date"},
)
st.plotly_chart(fig_daily, use_container_width=True)

# === 4 cuts: where does the model miss? ===
st.subheader("Where does the model miss?")

# Cut 1: MAE by hour of day
test_daily["hour"] = test_daily["HourUTC"].dt.hour
hourly_mae = test_daily.groupby("hour")["corrected_error"].apply(lambda x: x.abs().mean()).reset_index()
hourly_mae.columns = ["hour", "mae"]
fig_hour = px.bar(hourly_mae, x="hour", y="mae", title="MAE by Hour of Day",
                  labels={"mae": "MAE (MWh)", "hour": "Hour"})
st.plotly_chart(fig_hour, use_container_width=True)

# Cut 2: MAE by day of week
test_daily["dow"] = test_daily["HourUTC"].dt.day_name()
dow_mae = test_daily.groupby("dow")["corrected_error"].apply(lambda x: x.abs().mean()).reset_index()
dow_mae.columns = ["day", "mae"]
fig_dow = px.bar(dow_mae, x="day", y="mae", title="MAE by Day of Week",
                 labels={"mae": "MAE (MWh)", "day": "Day"})
st.plotly_chart(fig_dow, use_container_width=True)

# Cut 3: MAE by production level (5 bins) — cast Interval to str for Plotly
test_daily["prod_bin"] = pd.cut(test_daily["actual_wind_mwh"], bins=5).astype(str)
prod_mae = test_daily.groupby("prod_bin", observed=True)["corrected_error"].apply(lambda x: x.abs().mean()).reset_index()
prod_mae.columns = ["production_range", "mae"]
fig_prod = px.bar(prod_mae, x="production_range", y="mae", title="MAE by Production Level",
                  labels={"mae": "MAE (MWh)", "production_range": "Production (MWh)"})
st.plotly_chart(fig_prod, use_container_width=True)

# Cut 4: MAE by ramp intensity — use continuous ramp_1h, not the sparse is_big_ramp (only 5 hours)
# Why: is_big_ramp has just 5 hours in test — too few for a reliable mean.
# ramp_1h has all 743 hours, so we can bin it into intensity levels.
test_daily["ramp_abs"] = test_daily["ramp_1h"].abs()
test_daily["ramp_bin"] = pd.cut(test_daily["ramp_abs"], bins=5).astype(str)
ramp_mae = test_daily.groupby("ramp_bin", observed=True)["corrected_error"].apply(lambda x: x.abs().mean()).reset_index()
ramp_mae.columns = ["ramp_range", "mae"]

fig_ramp = px.bar(
    ramp_mae,
    x="ramp_range",
    y="mae",
    title="MAE by Ramp Intensity (|ramp_1h|)",
    labels={"mae": "MAE (MWh)", "ramp_range": "|Ramp| (MWh/h)"},
)
st.plotly_chart(fig_ramp, use_container_width=True)

# Report the sparse big-ramp numbers with an explicit caveat
big_ramp_count = int(test_daily["is_big_ramp"].sum())
big_ramp_mae = test_daily[test_daily["is_big_ramp"] == 1]["corrected_error"].abs().mean()
no_ramp_mae = test_daily[test_daily["is_big_ramp"] == 0]["corrected_error"].abs().mean()
st.write(f"Big-ramp hours in test: {big_ramp_count} (too few for a reliable conclusion)")
st.write(f"MAE on big-ramp hours: {big_ramp_mae:.2f} MWh")
st.write(f"MAE on normal hours:   {no_ramp_mae:.2f} MWh")
st.write(f"Ramp penalty (caveat: n={big_ramp_count}): {big_ramp_mae - no_ramp_mae:.2f} MWh")

# === Summary: what does each cut teach us? ===
st.subheader("What the data tells us")

top_hour = hourly_mae.loc[hourly_mae["mae"].idxmax()]
st.markdown(f"**Hours:** The model misses most around **{int(top_hour['hour']):02d}:00** "
            f"(MAE = {top_hour['mae']:.0f} MWh). Likely low-wind or ramp hours.")

top_day = dow_mae.loc[dow_mae["mae"].idxmax()]
st.markdown(f"**Days:** **{top_day['day']}** shows the highest MAE ({top_day['mae']:.0f} MWh). "
            f"January has only ~4 of each weekday — treat with caution.")

low_bin = prod_mae.iloc[0]
high_bin = prod_mae.iloc[-1]
if high_bin["mae"] > low_bin["mae"]:
    st.markdown(f"**Production:** MAE rises with production — from {low_bin['mae']:.0f} MWh "
                f"at low output to {high_bin['mae']:.0f} MWh at high output. The model misses more when wind is strong.")
else:
    st.markdown(f"**Production:** MAE does not rise with production — model is stable across output levels.")

low_ramp_mae = ramp_mae.iloc[0]["mae"]
high_ramp_mae = ramp_mae.iloc[-1]["mae"]
if high_ramp_mae > low_ramp_mae:
    st.markdown(f"**Ramp:** MAE rises with ramp intensity — from {low_ramp_mae:.0f} MWh at low ramp "
                f"to {high_ramp_mae:.0f} MWh at high ramp. Ramp events are harder for the model.")
else:
    st.markdown(f"**Ramp:** MAE does not rise with ramp intensity — model is stable across ramp levels. "
                f"(Note: only {big_ramp_count} big-ramp hours in test — that cut alone is not reliable.)")


# === Feature Importance — what did the model actually learn from? ===
st.subheader("What did the model learn from?")

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_,
}).sort_values("importance", ascending=False)

fig_imp = px.bar(
    importance,
    x="importance",
    y="feature",
    orientation="h",
    title="Feature Importance (LightGBM gain)",
    labels={"importance": "Importance (gain)", "feature": "Feature"},
)
fig_imp.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig_imp, use_container_width=True)

# Top 3 features
top3 = importance.head(3)
st.markdown(f"**Top 3 features:** {', '.join(top3['feature'].tolist())}")

# Check: is lag_1h (AR(1)) among the top? Is is_big_ramp near the bottom?
lag1_rank = importance[importance["feature"] == "lag_1h"].index[0] + 1
ramp_rank = importance[importance["feature"] == "is_big_ramp"].index[0] + 1
st.markdown(f"**lag_1h rank:** {lag1_rank} / {len(features)} | "
            f"**is_big_ramp rank:** {ramp_rank} / {len(features)}")      