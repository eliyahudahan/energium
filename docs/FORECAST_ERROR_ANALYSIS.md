# Forecast Error Analysis — Jan 2024, DK1, Onshore Wind

**Scope:** Total Wind (Onshore + Offshore) — final decision 2026-10-08.
Onshore-only numbers kept below for reference.

**Date:** 2026-10-08
**Status:** Verified

## Setup
- Forecast source:  Forecasts_Hour / ForecastDayAhead
- GT source:        ProductionConsumptionSettlement
                    (OnshoreWindGe50kW_MWh + OnshoreWindLt50kW_MWh)
- Period:           Jan 2024
- Region:           DK1
- Matched hours:    744

## Error magnitude
| Metric | |GT - DayAhead| | |GT - Current| |
|--------|---|---|
| Mean   | 352.6 MWh | 89.1 MWh |
| Median | 242.4 MWh | 61.1 MWh |
| Max    | 1531.9 MWh | (TBD) |

## Bias
- GT - DayAhead: +298.6 MWh (DayAhead under-forecasts)
- GT - Current:  -31.5 MWh (near zero)
- Distribution: 583 hours positive (78%), 161 hours negative (22%)

## Extreme events
### Positive (DayAhead << GT)
- 2024-01-22T06:00: err=+1531.9, DA=1860, GT=3391
- 2024-01-03T06:00: err=+1478.2, DA=1872, GT=3350
- 2024-01-22T05:00: err=+1439.6, DA=1930, GT=3369

### Negative (DayAhead >> GT)
- 2024-01-15T12:00: err=-935.1, DA=1219, GT=284
- 2024-01-15T11:00: err=-870.1, DA=1308, GT=438
- 2024-01-15T13:00: err=-777.6, DA=1026, GT=249

## Conclusion
- The forecast error is REAL and LARGE.
- It is SYSTEMATIC (bias, not just noise).
- Extreme events occur in clusters (hours 11-13, 05-06).
- ForecastCurrent is ~4x more accurate than ForecastDayAhead.
- Target for Energium: reduce MAE below 89 MWh (Current benchmark).
- Minimum: beat 352 MWh (DayAhead).

## Not EnumKraft
- GT is from Energinet official dataset.
- Baseline is Energinet official forecast.
- Problem is measurable, systematic, and documented.

## Total Wind (Onshore + Offshore) — for comparison

| Metric | |GT - DayAhead| | |GT - Current| |
|--------|---|---|
| Mean   | 529.6 MWh | 130.0 MWh |
| Gap    | 399.6 MWh | — |

## Derived: Offshore only (Total - Onshore)
- |GT - DayAhead| mean: 177.0 MWh
- |GT - Current|  mean:  40.9 MWh
- Gap:                 136.1 MWh

## Observation
- Bias / MAE ratio: 84.7% (Onshore), 86.9% (Total).
- Bias dominates. Simple bias correction must be a baseline.

## Bias correction baseline (Jan 2024, Onshore)

- Naive MAE:                  352.6 MWh
- After constant bias corr:   308.2 MWh
- Improvement:                 44.4 MWh (12.6%)
- Current benchmark:           89.1 MWh
- Residual gap:               219.1 MWh

Conclusion: bias is time-varying, not constant.
A trivial ML baseline is insufficient.
