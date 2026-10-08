# Vintage Check & GT Verification — Forecasts_Hour

**Date:** 2026-10-08
**Status:** Verified

## Query
GET https://api.energidataservice.dk/dataset/Forecasts_Hour
  ?start=2024-01-01&end=2024-02-01
  &filter={"PriceArea":["DK1"]}

## Findings

### Structure (verified)
- 2232 records = 744 hours × 3 ForecastTypes
- ForecastType = energy type (Offshore Wind, Onshore Wind, Solar)
- 5 forecast horizons per record:
  - ForecastDayAhead
  - ForecastIntraday
  - Forecast5Hour
  - Forecast1Hour
  - ForecastCurrent

### Vintage status
- Duplicate (HourUTC, ForecastType): 0
- Unique TimestampUTC: 2227 / 2232
- Delta (TimestampUTC - HourUTC): 2-6 minutes for ALL records
- CONCLUSION: TimestampUTC reflects the latest write, not per-horizon publish time.
- The API returns a final snapshot, not the vintage.
- Vintage reconstruction NOT possible from this endpoint.
- Documented as a limitation. Not fatal.

### ForecastCurrent is a MODEL, not GT
- Evidence: Solar on 2024-01-31 22:00 = 0.000417 at midnight (should be ~0)
- Values are model outputs (6-decimal floats)
- CONCLUSION: ForecastCurrent is NOT a ground truth.
- GT remains ProductionConsumptionSettlement (Day 1 decision confirmed).

### Forecast error magnitude (Onshore Wind, Jan 2024)
- |GT - DayAhead| mean:   352.6 MWh
- |GT - DayAhead| median: 242.4 MWh
- |GT - DayAhead| max:    1531.9 MWh
- |GT - Current|  mean:    89.1 MWh
- |GT - Current|  median:  61.1 MWh

### GT source (verified)
- ProductionConsumptionSettlement returns 744 hourly records for Jan 2024, DK1.
- Fields present (verified):
  - OnshoreWindGe50kW_MWh
  - OnshoreWindLt50kW_MWh
  - OffshoreWindGe100MW_MWh
  - OffshoreWindLt100MW_MWh
  - SolarPowerLt10kW_MWh, SolarPowerGe10Lt40kW_MWh, SolarPowerGe40kW_MWh
  - ExchangeNO_MWh, ExchangeSE_MWh, ExchangeGE_MWh, ExchangeNL_MWh, ExchangeGB_MWh
  - GrossConsumptionMWh, PowerToHeatMWh, etc.
- HourUTC aligns 1:1 with Forecasts_Hour.

## Next steps
- Download Forecasts_Hour for 2024-2025 full range
- Download ProductionConsumptionSettlement for 2024-2025 full range
- Download ProductionConsumptionSettlement for 2026-01 (test set)
