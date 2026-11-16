# Day 15 Summary — 2026-11-15

## What was done
1. Full file review: check_mae.py, dashboard.py, api/main.py, README.md
2. Fixed invalid bias correction in API
3. Upgraded dashboard ACF to full-series + test comparison
4. Corrected README (ACF, bias correction, feature count)

## Key findings
- **Bias Correction was harmful:** validation showed +0.27 MWh bias at
  high wind (3000-5000). The 71.89 correction added -71.62 MWh. Removed.
- **Test ACF ≠ full ACF:** 0.219 vs 0.108. January 2026 is not representative.
- **Weak seasonality:** lag-24 = 0.062, lag-168 = 0.018. No full seasonal
  model justified.
- **is_big_ramp is dead:** rank 18/19. Candidate for removal.
- **lag_1h is strong:** rank 2/19. Confirms residual learning.

## Decisions made
- Removed BIAS_CORRECTION from api/main.py
- Updated health check MAE: 92.10 → 102.14 (honest validation number)
- ACF computed on full series, not test only

## Next steps
- Dockerfile review (Day 11b)
- Walk-forward CV: AR(1) baseline, seasonal features, is_big_ramp removal
- Update README with walk-forward results