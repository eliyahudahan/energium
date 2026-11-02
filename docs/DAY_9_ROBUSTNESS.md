# Day 9 — Robustness & Statistical Significance

**Date:** 2026-10-25 (original) · **Updated:** 2026-11-02
**Status:** ✅ Complete

## 1. Diebold-Mariano Test

To verify that the improvement over Energinet is not due to chance (e.g., a lucky month), we performed a Diebold-Mariano test on the squared errors.

- **Null hypothesis:** Energinet and LightGBM have equal forecast accuracy.
- **DM statistic:** 25.9466
- **p-value:** < 0.000001

**Result:** We reject the null hypothesis. The improvement is highly statistically significant. LightGBM's forecast is consistently and measurably better than Energinet's official forecast.

## 2. Robustness (Daily MAE)

We checked the daily Mean Absolute Error (MAE) across January 2026 to ensure the model doesn't "break" on specific days.

**Canonical model:** `src/check_mae.py` — MAE = 97.29 MWh.

| Metric | Energinet (MWh) | LightGBM (MWh) |
|---|---|---|
| Worst Day (Highest Error) | 1221.65 (Jan 31) | 155.03 (Jan 31) |
| Best Day (Lowest Error) | 220.59 (Jan 5) | 48.44 (Jan 4) |
| Overall MAE | 637.97 | **97.29** |

**Insight:** Energinet's error fluctuates wildly (from 221 to 1222 MWh). Our model's error is not only lower on average but also highly stable (fluctuating only between 48 and 155 MWh). Even on Energinet's worst days (e.g., Jan 31), our model maintains a low error (155.03 MWh), proving it correctly identifies and corrects the baseline's major failures.

## 3. Final Canonical Result

- **Canonical script:** `src/check_mae.py`
- **MAE:** 97.29 MWh
- **Skill vs Energinet:** +84.7%
- **Test set:** January 2026 (743 rows, untouched)

## Update Note

This document was originally written on 2026-10-25 with an earlier model (MAE 100.21). It has been updated to reflect the canonical model (`check_mae.py`, MAE 97.29). The earlier number was not wrong — it reflected the model at that time. The canonical result supersedes it.

## Conclusion

The model is both robust (stable across days) and statistically superior to the baseline. It is ready for production deployment (Day 11).