# Day 2 — Decisions

**Date:** 2026-10-08
**Status:** Final

## Region
DK1 only.

## Scope Decision — TOTAL WIND
**Decision:** Energium targets Total Wind (Onshore + Offshore) for DK1.

### Rationale
1. Operational relevance: grid operators balance total wind, not components.
2. Larger absolute error: baseline MAE 529.6 MWh vs 352.6 (Onshore).
3. Larger benchmark gap: 399.6 MWh vs 263.5 (Onshore).
4. Portfolio strength: bigger scope, more mature framing.
5. Bias correction test shows the challenge is real regardless of scope.

### Accepted trade-offs
- DMI metObs stations are onshore-only => weaker physical alignment for
  the offshore component. This will be documented as a limitation.
- Higher modeling complexity (two-component structure).
- 3-week scope risk: acknowledged. Scope is fixed, not expandable.

### Out of scope
- Solar (different physics, no DMI wind feature)
- DK2 (different region)

## Periods
- Train:      2024-01-01 -> 2025-06-30
- Validation: 2025-07-01 -> 2025-12-31
- Test:       2026-01-01 -> 2026-01-31 (LOCKED until Day 8)

## Data Sources
| Role | Dataset |
|------|---------|
| GT | ProductionConsumptionSettlement |
| Baseline | Forecasts_Hour / ForecastDayAhead |
| Benchmark | Forecasts_Hour / ForecastCurrent |
| Features | DMI metObs (planned, Day 3) |

## Variable definitions (Total Wind)

### GT
GT(t) = OnshoreWindGe50kW_MWh(t) + OnshoreWindLt50kW_MWh(t)

OffshoreWindGe100MW_MWh(t) + OffshoreWindLt100MW_MWh(t)

text
Source: ProductionConsumptionSettlement (Energinet official)

### Baseline
baseline(t) = ForecastDayAhead(Onshore Wind) + ForecastDayAhead(Offshore Wind)

text
Source: Forecasts_Hour, filter PriceArea=DK1, HourUTC aligned

### Benchmark
benchmark(t) = ForecastCurrent(Onshore Wind) + ForecastCurrent(Offshore Wind)

text

### Target for ML
error(t) = GT(t) - baseline(t)
corrected(t) = baseline(t) + model(error(t))

text

## Verified metrics (Jan 2024, DK1, Total Wind)
- Baseline MAE (DayAhead):      529.6 MWh
- Benchmark MAE (Current):      130.0 MWh
- Gap:                          399.6 MWh
- Bias (DayAhead):              +460.0 MWh
- Bias / MAE:                   86.9%
- Constant bias correction:     TBD (Day 3 — rerun for Total)

## Time handling
- Split uses HourDK.
- Storage uses HourUTC.
- Forecast and GT align 1:1 by HourUTC (verified for Jan 2024).

## Limitations (documented)
1. Vintage: API returns final snapshot, not per-horizon publishes.
2. ForecastCurrent is a MODEL, not ground truth.
3. DMI metObs is onshore-only => offshore features are indirect.
4. Constant bias correction is insufficient (time-varying bias).

## Test set lock
2026-01-01 -> 2026-01-31. Never touched until Day 8.
