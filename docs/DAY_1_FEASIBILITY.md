# Day 1 — Feasibility Gate

**Date:** 2026-10-07
**Project:** Energium — Denmark Wind Generation Forecast Correction
**Status:** ✅ PASSED

---

## Executive Summary

Energium is **feasible**. All required data sources are available, verified, and documented. The project proceeds to Day 2 (pipeline construction).

**Decision:** Build Energium as a **day-ahead wind forecast correction** project.

---

## 1. Data Sources Verified

### 1.1 Ground Truth — `ProductionConsumptionSettlement`

| Field | Value |
|---|---|
| Dataset | `ProductionConsumptionSettlement` |
| Source | Energinet Data Service |
| Earliest data | **2020-01-01** |
| Resolution | Hourly |
| Unit | MWh |
| Records (Jan 2024, DK1) | 744 (complete) |
| Status | ✅ **Steel GT — verified** |

**Wind components (4 fields):**
- `OffshoreWindGe100MW_MWh`
- `OffshoreWindLt100MW_MWh`
- `OnshoreWindGe50kW_MWh`
- `OnshoreWindLt50kW_MWh`

**Aggregation formula:**
Wind_DK1_MWh =
OffshoreWindGe100MW_MWh

OffshoreWindLt100MW_MWh

OnshoreWindGe50kW_MWh

OnshoreWindLt50kW_MWh

text

**Verification notes:**
- `UnknownProdMWh` is `null` in 2020 but numeric in 2024 — schema evolved. All four wind fields are present and populated across 2020–2026.
- Data source is settlement-based (DataHub), the canonical source for statistics per Energinet.

**Endpoint:**
GET https://api.energidataservice.dk/dataset/ProductionConsumptionSettlement
?start=2024-01-01
&end=2024-02-01
&filter={"PriceArea":["DK1"]}
&limit=0

text

---

### 1.2 Baseline — `Forecasts_Hour` (ForecastDayAhead)

| Field | Value |
|---|---|
| Dataset | `Forecasts_Hour` |
| Source | Energinet Data Service |
| Earliest data | **2020-01-01** |
| Resolution | Hourly |
| Unit | MWh |
| Filter | `ForecastType: ["Offshore Wind", "Onshore Wind"]` |
| Status | ✅ **Verified usable** |

**Forecast types available:**

| Type | Usable as baseline? |
|---|---|
| `ForecastDayAhead` | ✅ **PRIMARY BASELINE** |
| `ForecastIntraday` | ❌ null during night hours |
| `Forecast5Hour` | 🟡 Ablation only |
| `Forecast1Hour` | 🟡 Ablation only |
| `ForecastCurrent` | ❌ Not a forecast — real-time estimate |

**Critical finding — revision check PASSED:**

Compared the same hour across multiple pulls at different times. Values were **identical**:

| `HourUTC` | `ForecastDayAhead` (pull 1) | (pull 2) | (pull 3) |
|---|---|---|---|
| 2026-10-06T08:00 | 340.083344 | 340.083344 | 340.083344 |
| 2026-10-06T09:00 | 313.375000 | 313.375000 | 313.375000 |

**No revision occurred.** `ForecastDayAhead` holds a stable value.

**Critical caveat — timestamp semantics:**

`TimestampUTC` reflects the **last update time**, not the **original publication time**. For a forecast targeting `HourUTC = 2024-01-07T22:00`, the `TimestampUTC` was `2024-01-07T22:00` — nearly identical, not 24 hours earlier.

**Interpretation:** `ForecastDayAhead` holds the true day-ahead forecast value. The timestamp field is misleading but does not affect the value's usability.

**Documented limitation:** Exact forecast origin time is unknown. To be recorded in README.

**Endpoint:**
GET https://api.energidataservice.dk/dataset/Forecasts_Hour
?start=2024-01-01
&end=2024-01-02
&filter={"ForecastType":["Offshore Wind"],"PriceArea":["DK1"]}
&limit=0

text

---

### 1.3 Validation — `ElectricityProdex5MinRealtime`

| Field | Value |
|---|---|
| Dataset | `ElectricityProdex5MinRealtime` |
| Source | Energinet Data Service |
| Earliest data | **2024-01-01** |
| Resolution | 5 minutes |
| Unit | MW |
| Records (Jan 2024, DK1) | 8,928 (complete) |
| Status | ✅ **Available for reconciliation** |

**Wind components:**
- `OffshoreWindPower`
- `OnshoreWindPower`

**Role:** Independent operational measurement. **Not a replacement for GT.** Used only for consistency checks.

**Energinet's own guidance:** Realtime data may contain errors and is generally not corrected. Settlement data is the source for statistics.

**Endpoint:**
GET https://api.energidataservice.dk/dataset/ElectricityProdex5MinRealtime
?start=2024-01-01
&end=2024-02-01
&filter={"PriceArea":["DK1"]}
&limit=0

text

---

### 1.4 Features — DMI metObs

| Field | Value |
|---|---|
| Source | DMI Open Data API v2 |
| Endpoint | `https://opendataapi.dmi.dk/v2/metObs/collections/observation/items` |
| Parameters | `wind_speed`, `wind_gust_always_past1h`, `humidity_past1h`, `temp_soil_max_past1h`, etc. |
| Resolution | 10 min / hourly depending on station |
| Status | ✅ **Working** |

**Leakage warning:** DMI returns **observations**, not forecasts. Must use lagged observations only (e.g., `wind_speed(t-1h)`). Never use `wind_speed(t)` to predict `actual(t)`.

---

## 2. Reconciliation — Settlement vs Realtime

**Purpose:** Verify that the wind variable definition is consistent across sources.

**Method:**

1. Pull Settlement and 5-min Realtime for identical period + DK1.
2. Construct identical wind variable from each source.
3. Aggregate Realtime 5-min data to hourly MWh:
Realtime_Wind_Hourly[h] = mean(Realtime_Wind_5min[t] for t in hour h)

text

4. Align on `HourUTC`.
5. Compare MAE / RMSE / bias and coverage.
6. Document discrepancies.

**Status:** Data pulled for January 2024. Computation pending — to be completed on Day 2.

**Note:** Realtime is a **sanity check**, not a GT replacement.

---

## 3. Leakage Controls

| Control | Implementation |
|---|---|
| Test set locked | January 2026 — never touched until Day 8 |
| Forecast origin | `ForecastDayAhead` value locked; timestamp documented as caveat |
| DMI features | Only lagged observations (t-1h, t-2h, ...) |
| Settlement GT | Never mixed with realtime for training |
| Curtailment | To be filtered in Day 3 (countertrade > 1700 MW, spot price < 0, 4h padding) |

---

## 4. Project Scope — Confirmed

| Field | Value |
|---|---|
| **Target** | Correct Energinet's official day-ahead wind power forecast |
| **Approach** | Residual learning — model the error `actual − forecast` |
| **Primary metric** | MAE + Skill Score vs Energinet baseline |
| **Secondary metrics** | RMSE, Bias, nMAE, Diebold–Mariano test |
| **Primary model** | LSTM (prior from Jørgensen et al. 2025) |
| **Challenger** | LightGBM |
| **Region** | DK1 only. DK2 deferred. |
| **Test period** | January 2026 — locked |
| **Training period** | 2024-01 → 2025-06 |
| **Validation period** | 2025-07 → 2025-12 |

---

## 5. Literature Prior

**Jørgensen, B.S., Møller, J.K., Nystrup, P., Madsen, H. (2025).**
*Sequential methods for error correction of probabilistic wind power forecasts.*
Expert Systems with Applications, Vol. 284, Article 127872.
DOI: [10.1016/j.eswa.2025.127872](https://doi.org/10.1016/j.eswa.2025.127872)

**Relevance:** Peer-reviewed, Denmark-specific, LSTM-based forecast correction. Achieved up to 40% MAE improvement on day-ahead wind forecasting.

**Difference from Energium:** Jørgensen uses 51 ECMWF ensembles; Energium uses a single official forecast. Jørgensen provides precedent for LSTM-based correction — not a direct replication.

---

## 6. Findings Log — Chronological

| Time | Finding | Impact |
|---|---|---|
| 13:40 | Started Day 1 Gate | — |
| 14:00 | GT + Forecasts + DMI confirmed working | ✅ |
| 15:00 | `TimestampUTC` ≈ `HourUTC` — suspicious | ⚠️ |
| 16:00 | Feared revision — possible project threat | 🔴 |
| 17:00 | Confusion resolved — API is historical, not predictive | ✅ |
| 17:30 | Revision check PASSED — identical values across pulls | ✅ |

---

## 7. Open Items (Resolved)

| Item | Status |
|---|---|
| Does `ForecastDayAhead` have revisions? | ✅ No |
| Is `ForecastDayAhead` a true day-ahead forecast? | ✅ Yes |
| Is Settlement GT available from 2020? | ✅ Yes |
| Is Realtime available from 2024? | ✅ Yes |
| Is DMI available? | ✅ Yes |
| Reconciliation | 🟡 Computation pending |

---

## 8. Documented Limitations

1. `TimestampUTC` reflects update time, not publication time.
2. `ForecastIntraday` is null during night hours — not usable.
3. Realtime data may contain uncorrected errors — used only for validation.
4. DMI provides observations, not forecasts — requires lagged features only.
5. Capacity drift (new wind farms) — to be documented in analysis.

---

## 9. Decision

**Energium passes Day 1 Feasibility Gate.**

**Proceeds to Day 2:** Data pipeline construction.

- **Baseline:** `ForecastDayAhead`
- **GT:** `ProductionConsumptionSettlement`
- **Validation:** `ElectricityProdex5MinRealtime`
- **Features:** DMI observations + time + lag + rolling

---

## 10. Day 2 Plan

1. Download 2024–2025 from Energinet (settlement + ForecastDayAhead).
2. Download DMI observations for same period.
3. Merge into `merged.parquet`.
4. Split: train / validation / test.
5. Lock test set.
6. Document in `DAY_2_PIPELINE.md`.

---

**Signed:** Eliyahu Dahan
**Date:** 2026-10-07
**Time:** 17:45
