# Day 7 — Model Decision

**Date:** 2026-10-25
**Status:** ✅ Complete

## Decision

**Primary model: LightGBM.**
**Challenger: LSTM.**

## Rationale

Both models were trained on the exact same feature set, the same training data, and evaluated on the exact same locked test set (January 2026).

| Model | MAE (MWh) | Skill vs Energinet | Complexity | Inference Time |
|---|---|---|---|---|
| Energinet forecast | 637.97 | — | — | — |
| LSTM | 181.33 | +71.6% | High | ~10 min |
| **LightGBM** | **100.21** | **+84.3%** 🏆 | **Low** | **~1 min** |

LightGBM beats LSTM by **81.12 MWh** in MAE. Since the input is tabular (engineered features), LightGBM's tree-based architecture captures the non-linear relationships better than the LSTM, which struggles to find long-term sequential dependencies in this specific event-based dataset.

## Why LightGBM Wins (Again)

This is the second time LightGBM beats LSTM on this type of data:
- **Metrodorf:** LightGBM F1=0.9252 vs LSTM F1=0.9110
- **Energium:** LightGBM MAE=100.21 vs LSTM MAE=181.33

**Reference:** Jørgensen 2025 — "Feature engineering beats representation learning on tabular data."

## Model Architecture

**LightGBM:**
- n_estimators: 500
- learning_rate: 0.05
- max_depth: 6
- num_leaves: 31
- Best iteration: 291 (early stopping)

## Top Features

1. lag_1h (1263)
2. forecast_wind_da (1010)
3. forecast_lag_1h (812)
4. ramp_1h (659)
5. hour (499)

## Decision Impact

- **LSTM:** Kept as a documented challenger. Shows that we tested Deep Learning and it didn't justify the added complexity.
- **LightGBM:** Deployed for final evaluation (Day 8) and will be used in the final API.
- Both are documented in `docs/PREDICTIONS_COMPARISON.md`.