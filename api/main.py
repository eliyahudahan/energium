from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import pickle

app = FastAPI(title="Energium API", description="Corrects Energinet wind forecasts")

# Load model once at startup
with open("models/lgbm_model.pkl", "rb") as f:
    model = pickle.load(f)

# The exact features the model expects (same order as check_mae.py)
FEATURES = [
    "forecast_wind_da",
    "lag_1h", "lag_2h", "lag_3h", "lag_6h", "lag_12h", "lag_24h", "lag_48h", "lag_168h",
    "ramp_1h",
    "hour", "day_of_week", "month", "is_weekend",
    "forecast_lag_1h", "forecast_lag_2h", "forecast_lag_24h",
    "is_big_ramp", "is_moderate_ramp",
]

# Bias correction parameters (learned on VALIDATION, not test)
HIGH_WIND_THRESHOLD = 3000.0
BIAS_CORRECTION = 71.89

class ForecastInput(BaseModel):
    forecast_wind_da: float
    lag_1h: float
    lag_2h: float
    lag_3h: float
    lag_6h: float
    lag_12h: float
    lag_24h: float
    lag_48h: float
    lag_168h: float
    ramp_1h: float
    hour: int
    day_of_week: int
    month: int
    is_weekend: int
    forecast_lag_1h: float
    forecast_lag_2h: float
    forecast_lag_24h: float
    is_big_ramp: int
    is_moderate_ramp: int

class PredictionOutput(BaseModel):
    original_forecast: float
    predicted_error: float
    corrected_forecast: float
    bias_applied: bool

@app.get("/")
def health_check():
    return {"status": "ok", "model": "LightGBM", "mae": 92.10, "note": "bias-corrected"}

@app.post("/predict", response_model=PredictionOutput)
def predict(data: ForecastInput):
    input_dict = data.model_dump()
    X = pd.DataFrame([input_dict])[FEATURES]
    
    # 1. Base model prediction
    predicted_error = model.predict(X)[0]
    corrected = data.forecast_wind_da + float(predicted_error)
    
    # 2. Bias correction layer (applied on high-wind hours)
    bias_applied = False
    if data.forecast_wind_da > HIGH_WIND_THRESHOLD:
        corrected += BIAS_CORRECTION
        bias_applied = True
    
    return PredictionOutput(
        original_forecast=data.forecast_wind_da,
        predicted_error=float(predicted_error),
        corrected_forecast=corrected,
        bias_applied=bias_applied
    )