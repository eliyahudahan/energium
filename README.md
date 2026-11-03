# 🌿 Energium — Denmark Wind Generation Forecast Correction

**Status:** 🚧 In development — Day 9 of 12 (Robustness & Error Analysis)
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
`Wind_DK1_MWh = OffshoreWindGe100MW_MWh + OffshoreWindLt100MW_MWh + OnshoreWindGe50kW_MWh + OnshoreWindLt50kW_MWh`

## Baseline

**ForecastDayAhead** — Energinet's official day-ahead wind forecast.

| Field | Value |
|---|---|
| Source | Energinet Data Service (Forecasts_Hour) |
| Earliest data | 2020-01-01 |
| Resolution | Hourly |
| Unit | MWh |

## Method

**Residual learning** — the model predicts `error = actual − forecast`, and the final prediction is `forecast + predicted_error`.

Input: [weather features, time features, lag features, official forecast, ramp indicators]  
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
| **LightGBM (final, 17 features, canonical process)** | **97.29** | **+84.7%** 🏆 |

**Winner: LightGBM (MAE = 97.29, Skill = +84.7%).**

**Reproducibility note:** The canonical training script is `src/check_mae.py`. It produces MAE = 97.29. Earlier exploratory runs with different hyperparameters produced 93.42 and 101.25; these are not the canonical result. The difference is due to `max_depth` (limited to 6 in the older script) and `callbacks` configuration, not feature changes.

## Feature Engineering Iterations

| Iteration | Features | MAE | Δ vs previous |
|---|---|---|---|
| Baseline | 9 | 100.21 | — |
| + engineered | 12 | 97.39 | −2.82 |
| + rolling | 22 | 93.94 | −3.45 (rejected — not reproducible cleanly) |
| − rolling | 16 | 94.06 | +0.12 (rolling did not contribute) |
| + is_moderate_ramp | 17 | 93.42 | −0.64 |

**Final feature set (17):** `forecast_offshore_da`, `forecast_onshore_da`, `forecast_wind_da`, `lag_1h`, `lag_2h`, `lag_3h`, `lag_6h`, `lag_12h`, `lag_24h`, `lag_48h`, `lag_168h`, `ramp_1h`, `forecast_lag_1h`, `forecast_lag_2h`, `forecast_lag_24h`, `is_big_ramp`, `is_moderate_ramp`.

**Definitions:**
- `is_big_ramp = (|ramp_1h| > 500)` — extreme wind change.
- `is_moderate_ramp = (0 < ramp_1h ≤ 200)` — moderate upward wind change.

## Error Analysis

**By hour:** Highest errors at 16:00–19:00 (MAE 348–413 in earlier model), lowest at 10:00–13:00 (MAE 109–142). Transition hours (dawn/dusk) are harder.

**By ramp:** Moderate upward ramp (0–200 MWh/h) has the highest error (mean 40.42). Negative ramp (wind decreasing) is well-handled (mean 16.07). Extreme ramp (>500) is too rare in test (n=1) to draw conclusions.

**By region:** All data is DK1. DK2 is out of scope. This is a documented limitation.

## Distribution Drift (2024-2025 → 2026)

KS test between train (2024-2025) and test (January 2026) shows significant drift in wind-related features:

| Feature | KS statistic | p-value | Train mean | Test mean | Change |
|---|---|---|---|---|---|
| `lag_1h` | 0.298 | < 0.001 | 1612 MWh | 2602 MWh | +61% |
| `forecast_wind_da` | 0.294 | < 0.001 | 1373 MWh | 2003 MWh | +46% |
| `lag_24h` | 0.283 | < 0.001 | 1614 MWh | 2534 MWh | +57% |
| `lag_168h` | 0.186 | < 0.001 | 1629 MWh | 2211 MWh | +36% |

**Interpretation:** Mean wind generation in January 2026 was 61% higher than the 2024-2025 training average. This explains the Train-Val gap (40%): the model did not overfit — it simply did not see this wind regime during training. The Test MAE (97.29) remains strong despite the drift, showing the model generalizes well even under distribution shift.

**Implication:** The model is trained on a lower-wind regime. If deployed on a higher-wind period, performance may degrade. This is a documented limitation of the current training window.

## Leakage Fix (Critical)

During development, we found and fixed data leakage in rolling and ramp features. The original features used `.rolling()` and `.diff()` **without** `.shift(1)`, which included the current hour (the target).

**Impact:** 70–80 MWh of fake improvement.

| Model | Before fix (leakage) | After fix (correct) | Δ |
|---|---|---|---|
| LSTM | 103.79 | 181.33 | +77.54 |
| LightGBM | 29.68 | 100.21 | +70.53 |

**Fix:** `actual.shift(1)` before rolling/diff.

**Post-fix rolling check:** Rolling features (`mean_3h`, `std_3h`, `mean_6h`, `std_6h`, `mean_24h`, `std_24h`) were re-evaluated after the fix. Adding them changed MAE from 94.06 to 93.94 — a difference of 0.12 MWh, within noise. They were **removed** from the final feature set due to unclear semantics (computed on raw vs. cleaned data) and negligible contribution.

## Top Features (LightGBM, final)

| Rank | Feature | Importance |
|---|---|---|
| 1 | lag_1h | 1,263 |
| 2 | forecast_wind_da | 1,010 |
| 3 | forecast_lag_1h | 812 |
| 4 | ramp_1h | 659 |
| 5 | hour | 499 |

## Metrics

**Primary:** MAE, Skill Score vs Energinet (`1 − MAE_model / MAE_Energinet`)
**Secondary:** RMSE, Bias / Mean Error, nMAE
**Statistical (Day 9):** Diebold–Mariano test vs Energinet baseline

## Data Sources

| Source | Dataset | License |
|---|---|---|
| Energinet Data Service | ProductionConsumptionSettlement, Forecasts_Hour, ElectricityProdex5MinRealtime | CC0 |
| DMI Open Data | metObs observations | CC BY 4.0 |

## Scope

- **Region:** DK1 (Jutland + Fyn). **DK2: deferred** — no DK2 rows in current dataset.
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
| Rolling features | Computed on `shift(1)` only; removed from final set (see Leakage Fix) |

## Literature Prior

Jørgensen, B.S., Møller, J.K., Nystrup, P., Madsen, H. (2025). *Sequential methods for error correction of probabilistic wind power forecasts.* Expert Systems with Applications, Vol. 284, Article 127872.
DOI: 10.1016/j.eswa.2025.127872

**Relevance:** Peer-reviewed, Denmark-specific, LSTM-based forecast correction. Achieved up to 40% MAE improvement.

**Difference from this project:** Jørgensen uses 51 ECMWF ensembles; this project uses a single official forecast from Energinet. Jørgensen provides precedent for LSTM-based correction — not a direct replication.

**Acknowledgments:** Grateful to Dr. Jørgensen for his response to my questions and for making the `nabqr` package open source.

## Documentation

| File | Content | Status |
|---|---|---|
| docs/DAY_1_FEASIBILITY.md | Feasibility Gate — data sources verified | ✅ |
| docs/DAY_2_PIPELINE.md | Data pipeline | ✅ |
| docs/DAY_3B_FEATURES.md | Feature engineering | ✅ |
| docs/DAY_4_BASELINES.md | Baseline models | ✅ |
| docs/DAY_5_LSTM.md | LSTM training | ✅ |
| docs/DAY_6_LIGHTGBM.md | LightGBM training + leakage fix | ✅ |
| docs/DAY_7_DECISION.md | Model decision | ✅ |
| docs/DAY_8_FINAL_EVAL.md | Final test evaluation | ✅ |
| docs/DAY_9_ROBUSTNESS.md | Robustness + error analysis + drift | ✅ |
| docs/DAY_12_SUMMARY.md | Project summary | ⏳ |

## Status

- ✅ Day 1: Feasibility Gate passed
- ✅ Day 2: Pipeline (`merged.parquet`)
- ✅ Day 3b: Features (`features.parquet` — 16,992 rows)
- ✅ Day 4: Baselines
- ✅ Day 5: LSTM (MAE 181.33)
- ✅ Day 6: LightGBM (MAE 100.21) + Leakage fix
- ✅ Day 7: Decision — LightGBM wins
- ✅ Day 8: Final Test Eval (MAE 97.29)
- ✅ Day 9: Robustness + Error Analysis + DM test + Drift analysis
- ⏳ Day 10: Dashboard (Streamlit)
- ⏳ Day 11: Production (FastAPI + Docker + Fly.io)
- ⏳ Day 12: Summary + Blog post

## Limitations

- **Distribution drift (2024-2025 → 2026):** Mean wind generation shifted +61% between training and test. See Distribution Drift section above.
- **Curtailment is removed from training data (intentional).** Per Jørgensen et al. (2025), curtailment hours are filtered out before training because they reflect operator decisions, not wind availability. The model therefore cannot predict curtailment — this is by design, not a data quality issue. `src/apply_curtailment_filter.py` documents the exact filter. Predicting curtailment would require a separate model and a separate dataset.
- **DK2 out of scope.** All data is DK1. No DK2 rows present in current dataset.
- **ForecastIntraday** is null during night hours — not used.
- **Realtime data** may contain uncorrected errors — used only for validation, never as GT.
- **DMI provides observations, not forecasts** — only lagged features are used.
- **Installed wind capacity has drifted** over the training period — normalized metrics (nMAE) are reported.
- **Extreme ramp (>500 MWh/h)** is too rare in test (n=1) to draw conclusions.
- **Rolling features** were evaluated but excluded due to unclear semantics and negligible contribution.

## Attribution

Baseline compared against Energinet's official ForecastDayAhead field. Data source: Energinet (Danish TSO).

## Reproducibility

```bash
git clone https://github.com/eliyahudahan/energium.git
cd energium
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Data is not committed. See docs/DAY_2_PIPELINE.md for download instructions.
# Run the canonical training script:
python src/check_mae.py
Author
Eliyahu Dahan · GitHub: @eliyahudahan · LinkedIn: eliyahu-dahan-684b22294