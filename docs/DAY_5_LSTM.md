# Day 5 — LSTM

**Date:** 2026-10-12
**Status:** In progress

## Model
- LSTM 256 units
- Dense(20) sigmoid
- Dense(20) relu
- Dense(1) linear
- Loss: MAE
- Optimizer: Adam

## Input
- Sequence length: 24 hours
- Features: 24 (list)

## Training
- Epochs: 50 (early stopping patience=10)
- Batch: 32

## Results
- Train MAE: ?
- Val MAE: ?
- Test MAE: ?

## Baseline comparison
- Persistence t-1 (test): 119.89
- ForecastDayAhead (test): 645.24
- LSTM (test): ?

## Next Steps
Day 6 — LightGBM challenger