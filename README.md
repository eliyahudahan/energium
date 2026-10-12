
```markdown
# 🌿 Energium — Denmark Wind Generation Forecast Correction

**Status:** 🚧 In development — Day 6 of 12 (Decision complete)
**Portfolio project. Not deployed in production.**

## Problem

Can machine learning systematically improve on Denmark's official day-ahead wind power forecast?

Energinet — Denmark's transmission system operator — publishes an official day-ahead wind power forecast. This project tests whether an ML model can correct that forecast using weather observations available **before** the forecast is issued.

The task is **not** to predict wind generation from scratch. The task is to predict the **error** in Energinet's forecast and correct it.

## Ground Truth

**ProductionConsumptionSettlement** — settlement-based hourly wind generation (MWh).

| Field | Value |
|---|---|
| Source | Energinet Data Service |
| Earliest data | 2020-01-01 |
| Resolution | Hourly |
| Unit | MWh |
| Status | Verified, complete |

Wind is computed from four settlement fields:

```

Wind_DK1_MWh =
OffshoreWindGe100MW_MWh

· OffshoreWindLt100MW_MWh
· OnshoreWindGe50kW_MWh
· OnshoreWindLt50kW_MWh

```

## Baseline

**ForecastDayAhead** — Energinet's official day-ahead wind forecast.

| Field | Value |
|---|---|
| Source | Energinet Data Service (Forecasts_Hour) |
| Earliest data | 2020-01-01 |
| Resolution | Hourly |
| Unit | MWh |

**Documented limitation:** TimestampUTC reflects the last update time, not the original publication time. The forecast value itself is stable and verified to have no revisions.

## Method

**Residual learning** — the model predicts `error = actual − forecast`, and the final prediction is `forecast + predicted_error`.

Input: [weather features, time features, lag features, official forecast]  
Output: predicted_error  
Final: forecast + predicted_error

## Models

| Model | Role |
|---|---|
| LSTM | Challenger |
| **LightGBM** | **Primary — winner** |

Both use the same information set and the same evaluation metrics.

## Results (Test Set — January 2026, untouched)

| Model | MAE (MWh) | Skill vs Energinet |
|---|---|---|
| Energinet forecast | 637.97 | — |
| Persistence t-1 | 119.89 | +81.2% |
| LSTM | 181.33 | +71.6% |
| **LightGBM** | **100.21** | **+84.3%** 🏆 |

**Winner: LightGBM (MAE = 100.21, Skill = +84.3%).**

## Leakage Fix (Critical)

During development, we found and fixed data leakage in rolling and ramp features. The original features used `.rolling()` and `.diff()` **without** `.shift(1)`, which included the current hour (the target).

**Impact:** 70–80 MWh of fake improvement.

| Model | Before fix (leakage) | After fix (correct) | Δ |
|---|---|---|---|
| LSTM | 103.79 | 181.33 | +77.54 |
| LightGBM | 29.68 | 100.21 | +70.53 |

**Fix:** `actual.shift(1)` before rolling/diff.

**Reference:**
- anofox-forecast: "lag == 0 would include the target value in its own feature window, which is data leakage for any rolling statistic of the target series."
- Azure ML: "Time-point joins help prevent data leakage."

## Top Features (LightGBM)

| Rank | Feature | Importance |
|---|---|---|
| 1 | lag_1h | 1,263 |
| 2 | forecast_wind_da | 1,010 |
| 3 | forecast_lag_1h | 812 |
| 4 | ramp_1h | 659 |
| 5 | hour | 499 |

## Metrics

**Primary:**
- MAE
- Skill Score vs Energinet: `1 − MAE_model / MAE_Energinet`

**Secondary:**
- RMSE
- Bias / Mean Error
- nMAE (normalized by installed capacity)

**Statistical (planned — Day 9):**
- Diebold–Mariano test vs Energinet baseline

**Breakdown by:**
- Month, season
- Wind regime (low / medium / high)
- Forecast horizon

## Data Sources

| Source | Dataset | License |
|---|---|---|
| Energinet Data Service | ProductionConsumptionSettlement, Forecasts_Hour, ElectricityProdex5MinRealtime | CC0 |
| DMI Open Data | metObs observations | CC BY 4.0 |

## Scope

- **Region:** DK1 (Jutland + Fyn)
- **DK2:** Deferred
- **Training period:** 2024-01 → 2025-06
- **Validation period:** 2025-07 → 2025-12
- **Test period:** January 2026 — locked, one-shot

## Leakage Controls

| Control | Implementation |
|---|---|
| Test set locked | January 2026 — never touched until Day 8 |
| Forecast origin | ForecastDayAhead value used as-is; timestamp documented as caveat |
| DMI features | Only lagged observations (t-1h, t-2h, ...) |
| Settlement GT | Never mixed with realtime for training |
| Curtailment | Filtered before training (countertrade > 1700 MW, spot price < 0, 4h padding) |

## Literature Prior

Jørgensen, B.S., Møller, J.K., Nystrup, P., Madsen, H. (2025).
*Sequential methods for error correction of probabilistic wind power forecasts.*
Expert Systems with Applications, Vol. 284, Article 127872.
DOI: 10.1016/j.eswa.2025.127872

**Relevance:** Peer-reviewed, Denmark-specific, LSTM-based forecast correction. Achieved up to 40% MAE improvement on day-ahead wind forecasting.

**Difference from this project:** Jørgensen uses 51 ECMWF ensembles; this project uses a single official forecast from Energinet. Jørgensen provides precedent for LSTM-based correction — not a direct replication.

**Acknowledgments:** Grateful to Dr. Jørgensen for his response to my questions and for making the `nabqr` package open source.

## Documentation

Day-by-day logs in `docs/`:

| File | Content | Status |
|---|---|---|
| docs/DAY_1_FEASIBILITY.md | Feasibility Gate — data sources verified | ✅ |
| docs/DAY_2_PIPELINE.md | Data pipeline | ✅ |
| docs/DAY_3B_FEATURES.md | Feature engineering | ✅ |
| docs/DAY_4_BASELINES.md | Baseline models | ✅ |
| docs/DAY_5_LSTM.md | LSTM training | ✅ |
| docs/DAY_6_LIGHTGBM.md | LightGBM training + leakage fix | ✅ |
| docs/DAY_7_DECISION.md | Model decision | ⏳ |
| docs/DAY_8_FINAL_EVAL.md | Final test evaluation | ⏳ |
| docs/DAY_9_ROBUSTNESS.md | Robustness analysis | ⏳ |
| docs/DAY_12_SUMMARY.md | Project summary | ⏳ |

## Status

- ✅ Day 1: Feasibility Gate passed
- ✅ Day 2: Pipeline (`merged.parquet`)
- ✅ Day 3b: Features (`features.parquet` — 16,992 rows, 23 features)
- ✅ Day 4: Baselines
- ✅ Day 5: LSTM (MAE 181.33)
- ✅ Day 6: LightGBM (MAE 100.21) + Leakage fix
- ✅ Day 6b: Comparison — LightGBM wins
- ⏳ Day 7: Decision (in progress)
- ⏳ Day 8: Final Test Eval
- ⏳ Day 9: Robustness + DM test
- ⏳ Day 10: Dashboard (Streamlit)
- ⏳ Day 11: Production (FastAPI + Docker + Fly.io)
- ⏳ Day 12: Summary + Blog post

## Limitations

- TimestampUTC in Forecasts_Hour reflects update time, not publication time.
- ForecastIntraday is null during night hours — not used.
- Realtime data may contain uncorrected errors — used only for validation, never as GT.
- DMI provides observations, not forecasts — only lagged features are used.
- Installed wind capacity has drifted over the training period — normalized metrics (nMAE) are reported.
- DK2 is out of scope.

## Reproducibility

```bash
git clone https://github.com/eliyahudahan/energium.git
cd energium
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Data is not committed. See docs/DAY_2_PIPELINE.md for download instructions.

Author

Eliyahu Dahan
GitHub: @eliyahudahan
LinkedIn: eliyahu-dahan-684b22294

```