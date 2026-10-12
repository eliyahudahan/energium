# Day 3 — Features

**Date:** 2026-10-11
**Status:** Partial

## Completed

### 1. Countertrade Field Verified

- Field: `ExchangeGE_MWh` in `ProductionConsumptionSettlement`
- Verified: January 2024, DK1
- Range: -2506 to +2581 MWh
- Sign: positive = export to Germany

### 2. Curtailment Filter Applied

- Filter per Jørgensen et al. (2025), Section 2.1
- **Result: 0 events matching the full rule**
- Documented in `CURTAILMENT_FILTER.md`
- This is consistent with the paper's prediction that curtailment 
  is fading after 2023-07.

### 3. Merge Complete

- `merged.parquet`: 17,256 rows
- Split: train 12,265 / validation 4,248 / test 743
- 48 rows dropped (null forecast)

## Next Steps (Day 3 continued)

- [ ] Feature engineering: time, lag, rolling, physics
- [ ] DMI integration (pending)
- [ ] Save `features.parquet`

## Notes

- Total processing time: ~1.5 hours
- All raw data downloaded
- All intermediate parquet files saved

# Day 3 — Features

**Date:** 2026-10-12
**Status:** ✅ Complete

## Input
- `data/processed/merged_clean.parquet` — 17,256 rows

## Output
- `data/processed/features.parquet` — 16,992 rows, 29 columns

## Features

| Group | Columns |
|---|---|
| **Target** | `error = actual − forecast` |
| **Time** | hour, day_of_week, month, is_weekend |
| **Lag (actual)** | lag_1h, lag_2h, lag_3h, lag_6h, lag_12h, lag_24h, lag_48h, lag_168h |
| **Rolling** | mean/std: 3h, 6h, 24h |
| **Ramp** | ramp_1h |
| **Forecast lag** | forecast_lag_1h, forecast_lag_2h, forecast_lag_24h |

**AR lags follow Jørgensen et al. (2025):** `[1, 2, 3, 6, 12, 24, 48]`.
We add `168` (weekly) as an experiment.

## Dropped Rows — 264 total

| Reason | Count | Location |
|---|---|---|
| **lag_168h** | 168 | first 168 hours |
| **forecast_wind_da (NaN)** | 48 | 2024-05-31 → 2024-06-01, 2025-02-25 → 2025-02-26 |
| **Overlap** | 48 (?) | (need to verify) |

**All dropped rows are in train split.** No impact on validation/test.

**Root cause of NaN in forecast:** Energinet API did not return data for those 2 days.

## Split Counts

| Split | Rows | % |
|---|---|---|
| **Train** | 12,001 | 70.6% |
| **Validation** | 4,248 | 25.0% |
| **Test** | 743 | 4.4% |

## Next Steps (Day 4)

Baselines — see `src/baselines.py`.