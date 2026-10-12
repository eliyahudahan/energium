# Day 6 — LightGBM vs LSTM

**Date:** 2026-10-12
**Status:** ✅ Complete

## Results (Test, January 2026)

| Model | MAE (MWh) | Skill vs Energinet |
|---|---|---|
| Energinet forecast | 637.97 | — |
| Persistence t-1 | 119.89 | +81.2% |
| LSTM | 181.33 | +71.6% |
| **LightGBM** | **100.21** | **+84.3%** 🏆 |

## Winner: LightGBM

**Reason:** LightGBM wins by 81.12 MWh.

## Leakage Fix

Before fix (leakage):
- LSTM: 103.79
- LightGBM: 29.68

After fix (correct):
- LSTM: 181.33
- LightGBM: 100.21

**Impact:** 70-80 MWh of fake improvement.

**Root cause:** rolling and ramp features included the current hour.
**Fix:** `actual.shift(1)` before rolling/diff.

## Feature Importance (LightGBM)

Top 5:
1. lag_1h (1263)
2. forecast_wind_da (1010)
3. forecast_lag_1h (812)
4. ramp_1h (659)
5. hour (499)

## Key Findings

1. LightGBM beats LSTM (like in Metrodorf)
2. Both beat Energinet
3. Data leakage was 70-80 MWh
4. Skill Score = +84.3%

## Next Steps (Day 7)

Decision:
- LightGBM is primary
- LSTM as challenger
- Document decision