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