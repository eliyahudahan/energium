# Energium
**Denmark Wind Generation Forecast Correction**

Can machine learning systematically improve on Denmark's official day-ahead wind power forecast?

---

## Problem

Energinet — Denmark's transmission system operator — publishes an official day-ahead wind power forecast. This project tests whether a machine learning model can correct that forecast using weather observations available **before** the forecast is issued.

The task is not to predict wind generation from scratch. The task is to **predict the error in Energinet's forecast** and correct it.

---

## Ground Truth

**`ProductionConsumptionSettlement`** — settlement-based hourly wind generation (MWh).

| Field | Value |
|---|---|
| Source | Energinet Data Service |
| Earliest data | 2020-01-01 |
| Resolution | Hourly |
| Unit | MWh |
| Status | Verified, complete |

Wind is computed from four settlement fields:
Wind_DK1_MWh =
OffshoreWindGe100MW_MWh

OffshoreWindLt100MW_MWh

OnshoreWindGe50kW_MWh

OnshoreWindLt50kW_MWh

text

---

## Baseline

**`ForecastDayAhead`** — Energinet's official day-ahead wind forecast.

| Field | Value |
|---|---|
| Source | Energinet Data Service (`Forecasts_Hour`) |
| Earliest data | 2020-01-01 |
| Resolution | Hourly |
| Unit | MWh |

**Documented limitation:** `TimestampUTC` reflects the last update time, not the original publication time. The forecast value itself is stable and has been verified to have no revisions.

---

## Method

**Residual learning** — the model predicts `error = actual − forecast`, and the final prediction is `forecast + predicted_error`.
Input: [weather features, time features, lag features, official forecast]
Output: predicted_error
Final: forecast + predicted_error

text

---

## Models

| Model | Role |
|---|---|
| LSTM | Primary (prior: Jørgensen et al. 2025) |
| LightGBM | Challenger |

Both use the same information set and the same evaluation metrics.

---

## Metrics

**Primary:**
- MAE
- Skill Score vs Energinet (`1 − MAE_model / MAE_Energinet`)

**Secondary:**
- RMSE
- Bias / Mean Error
- nMAE (normalized by installed capacity)

**Statistical:**
- Diebold–Mariano test vs Energinet baseline

**Breakdown by:**
- Month, season
- Wind regime (low / medium / high)
- Forecast horizon

---

## Data Sources

| Source | Dataset | License |
|---|---|---|
| Energinet Data Service | `ProductionConsumptionSettlement`, `Forecasts_Hour`, `ElectricityProdex5MinRealtime` | CC0 |
| DMI Open Data | `metObs` observations | CC BY 4.0 |

---

## Scope

- **Region:** DK1 (Jutland + Fyn)
- **DK2:** Deferred
- **Training period:** 2024-01 → 2025-06
- **Validation period:** 2025-07 → 2025-12
- **Test period:** January 2026 — **locked, one-shot**

---

## Leakage Controls

| Control | Implementation |
|---|---|
| Test set locked | January 2026 — never touched until Day 8 |
| Forecast origin | `ForecastDayAhead` value used as-is; timestamp documented as caveat |
| DMI features | Only lagged observations (t-1h, t-2h, ...) |
| Settlement GT | Never mixed with realtime for training |
| Curtailment | Filtered before training (countertrade > 1700 MW, spot price < 0, 4h padding) |

---

## Literature Prior

Jørgensen, B.S., Møller, J.K., Nystrup, P., Madsen, H. (2025).
*Sequential methods for error correction of probabilistic wind power forecasts.*
Expert Systems with Applications, Vol. 284, Article 127872.
DOI: [10.1016/j.eswa.2025.127872](https://doi.org/10.1016/j.eswa.2025.127872)

**Relevance:** Peer-reviewed, Denmark-specific, LSTM-based forecast correction. Achieved up to 40% MAE improvement on day-ahead wind forecasting.

**Difference from this project:** Jørgensen uses 51 ECMWF ensembles; this project uses a single official forecast from Energinet. Jørgensen provides precedent for LSTM-based correction — not a direct replication.

---

## Documentation

Day-by-day logs in [`docs/`](docs/):

| File | Content |
|---|---|
| [`docs/DAY_1_FEASIBILITY.md`](docs/DAY_1_FEASIBILITY.md) | Feasibility Gate — data sources verified |
| `docs/DAY_2_PIPELINE.md` | Data pipeline |
| `docs/DAY_7_DECISION.md` | Model decision |
| `docs/DAY_8_FINAL_EVAL.md` | Final test evaluation |
| `docs/DAY_9_ROBUSTNESS.md` | Robustness analysis |
| `docs/DAY_12_SUMMARY.md` | Project summary |

---

## Status

🚧 **In development** — Day 1 complete (Feasibility Gate passed).

---

## Limitations

1. `TimestampUTC` in `Forecasts_Hour` reflects update time, not publication time.
2. `ForecastIntraday` is null during night hours — not used.
3. Realtime data may contain uncorrected errors — used only for validation, never as GT.
4. DMI provides observations, not forecasts — only lagged features are used.
5. Installed wind capacity has drifted over the training period — normalized metrics (nMAE) are reported.
6. DK2 is out of scope.

---

## Reproducibility

```bash
git clone https://github.com/eliyahudahan/energium.git
cd energium
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Data is not committed. See docs/DAY_2_PIPELINE.md for download instructions.

Author
Eliyahu Dahan
GitHub · LinkedIn
