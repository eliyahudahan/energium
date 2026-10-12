# Day 4 — Baselines

**Date:** 2026-10-12
**Status:** ✅ Complete

## Input
- `data/processed/features.parquet` — 16,992 rows

## Baselines Evaluated

| Split | Model | MAE | RMSE | Skill vs ForecastDayAhead |
|---|---|---|---|---|
| validation | ForecastDayAhead (official) | 401.66 | 540.27 | 0.000 |
| validation | Persistence t-1 | 135.68 | 194.27 | **+0.662** |
| validation | Persistence t-168 | 1248.88 | 1586.95 | -2.109 |
| test | ForecastDayAhead (official) | 645.24 | 773.43 | 0.000 |
| test | Persistence t-1 | 119.89 | 159.60 | **+0.814** |
| test | Persistence t-168 | 1538.10 | 1829.17 | -1.384 |

## Key Finding

**Persistence t-1 beats ForecastDayAhead by 81% in MAE on test.**

This is surprising: the official Energinet forecast has MAE = 645 MWh
on test, while a simple 1-hour lag achieves MAE = 120 MWh.

**Hypothesis:** Danish wind is highly autocorrelated — if wind was
3,000 MWh an hour ago, it's likely still 3,000 MWh.

**Implication for modeling:**
- The model must beat Persistence t-1 (MAE = 120), not ForecastDayAhead.
- ForecastDayAhead may still be useful as a *feature*, not as a baseline.

## Next Steps (Day 5)

LSTM model — following Jørgensen et al. (2025):
- LSTM 256 units
- Dense(20) + Dense(20)
- Loss: MAE
- Input: AR lags + time + rolling + ramp + ForecastDayAhead as feature
