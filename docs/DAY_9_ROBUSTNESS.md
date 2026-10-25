# Day 9 — Robustness & Statistical Significance

**Date:** 2026-10-25
**Status:** ✅ Complete

## 1. Diebold-Mariano Test

To verify that the improvement over Energinet is not due to chance (e.g., a lucky month), we performed a Diebold-Mariano test on the squared errors.

- **Null hypothesis:** Energinet and LightGBM have equal forecast accuracy.
- **DM statistic:** 25.9466
- **p-value:** < 0.000001

**Result:** We reject the null hypothesis. The improvement is highly statistically significant. LightGBM's forecast is consistently and measurably better than Energinet's official forecast.

## 2. Robustness (Daily MAE)

We checked the daily Mean Absolute Error (MAE) across January 2026 to ensure the model doesn't "break" on specific days.

| Metric | Energinet (MWh) | LightGBM (MWh) |
|---|---|---|
| Worst Day (Highest Error) | 1269.90 (Jan 21) | 154.35 (Jan 31) |
| Best Day (Lowest Error) | 164.36 (Jan 18) | 46.52 (Jan 4) |
| Average (MAE) | 637.97 | 100.21 |

**Insight:** Energinet's error fluctuates wildly (from 164 to 1269 MWh). Our model's error is not only lower on average but also highly stable (fluctuating only between 46 and 154 MWh). Even on Energinet's worst days (e.g., Jan 21), our model maintains a low error (98.49 MWh), proving it correctly identifies and corrects the baseline's major failures.

## Conclusion

The model is both robust (stable across days) and statistically superior to the baseline. It is ready for production deployment (Day 11).