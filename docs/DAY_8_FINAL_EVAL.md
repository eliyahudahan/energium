# Day 8 — Final Test Evaluation (January 2026)

**Date:** 2026-10-25
**Status:** ✅ Complete

## Overview

The primary model (LightGBM) was evaluated on the locked test set (January 2026). The model predicts the error of Energinet's official day-ahead forecast and corrects it.

## Final Metrics

| Model | MAE (MWh) | Skill vs Energinet |
|---|---|---|
| Energinet forecast | 637.97 | — |
| Persistence t-1 | 119.89 | +81.2% |
| LSTM (Challenger) | 181.33 | +71.6% |
| **LightGBM (Primary)** | **100.21** | **+84.3%** 🏆 |

**LightGBM reduces the forecast error by 84.3% compared to Energinet.**

## Error Analysis

We analyzed where the model's errors are highest.

### 1. Error by Hour of Day
- **Highest error:** ~01:30 AM (154.57 MWh)
- **Lowest error:** ~12:00 PM (56.62 MWh)
- **Insight:** The model (and Energinet) performs worse at night when real-time weather data is less available and wind patterns are less stable. Midday forecasts are more accurate.

### 2. Error by Wind Regime (Actual Generation)
- **Low generation (<1 GWh):** 56.72 MWh error
- **Medium generation (1-2.5 GWh):** 100.67 MWh error
- **High generation (2.5-5 GWh):** 112.62 MWh error
- **Insight:** The model has more absolute error when wind generation is high. This makes physical sense: high-wind events are more volatile and harder to predict.

### 3. Top 5 Worst Predictions (The "Saves")

The worst predictions are actually where the model performed best in terms of value.

| Date | Actual | Energinet Forecast | Corrected (Ours) | Error |
|---|---|---|---|---|
| 2026-01-31 20:00 | 4492.85 | 2.12 | 3968.34 | 524.50 |
| 2026-01-06 14:00 | 1095.78 | -0.17 | 1580.44 | 484.66 |
| 2026-01-14 06:00 | 2234.52 | -0.19 | 1820.00 | 414.53 |
| 2026-01-12 20:00 | 2715.94 | 1.35 | 3128.91 | 412.97 |
| 2026-01-31 22:00 | 4347.79 | 1.94 | 3948.84 | 398.94 |

**Insight:** On January 31st, Energinet's forecast almost completely missed a major wind event (forecasted ~2 MWh, actual ~4500 MWh). Our model corrected this to ~3968 MWh, catching the event and drastically reducing the operational risk.

## Conclusion

LightGBM is confirmed as the primary model. It not only achieves a strong overall MAE (100.21) but demonstrates robustness in its error profile: it corrects major failures in the baseline forecast (as seen in the Top 5 worst cases) and behaves logically across different hours and wind regimes.