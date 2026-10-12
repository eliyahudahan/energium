# Day 5 — LSTM

**Date:** 2026-10-12
**Status:** ✅ Complete

## Model Architecture

| Layer | Output Shape | Params |
|---|---|---|
| Input | (24, 23) | 0 |
| LSTM | (256) | 286,720 |
| Dense 1 (sigmoid) | (20) | 5,140 |
| Dense 2 (relu) | (20) | 420 |
| Dense 3 (linear) | (1) | 21 |
| **Total** | | **292,301** |

## Training

- Optimizer: Adam (lr=0.001)
- Loss: MAE
- Early stopping: patience=10
- Stopped at: epoch 26

## Results

| Dataset | MAE (MWh) |
|---|---|
| Train | 89.28 |
| Validation | 109.69 |
| **Test** | **103.79** |

**Overfitting gap:** +14.51 (14.5%)

## Comparison (Test, January 2026)

| Model | MAE (MWh) | Skill vs Energinet |
|---|---|---|
| ForecastDayAhead (Energinet) | 637.97 | — |
| Persistence t-1 | 119.89 | +81.2% |
| **LSTM (ours)** | **103.79** | **+83.73%** |

**Skill Score vs Energinet: +83.73%**
**Skill Score vs Persistence: +13.4%**

## Findings

### 1. Energinet systematically under-forecasts
All 20 test hours show positive `predicted_error` (0 to +1033 MWh).
This is a consistent bias — the model learns to correct it.

### 2. The model works in 90% of hours
- 11 hours: improvement >50%
- 4 hours: improvement 20-50%
- 3 hours: improvement <20%
- 2 hours: the model overcorrects

### 3. Overfitting is present but not severe
- Train MAE 89.28
- Test MAE 103.79
- Gap 14.5%

## Known Limitations

1. **Overfitting** — gap 14.5%. Could be reduced with L2 or fewer units.
2. **Energinet bias unknown source** — why does Energinet under-forecast?
3. **No weather features** — DMI not integrated yet.
4. **No curtailment modeling** — filtered, not modeled.
5. **Single test period** — January 2026 only.

## Baseline Analysis — Why Persistence t-1 Wins Over Energinet

| Model | MAE (test) |
|---|---|
| ForecastDayAhead | 637.97 |
| Persistence t-1 | 119.89 |
| LSTM | 103.79 |

**Persistence t-1 beats Energinet by 81%.**
This suggests Danish wind is highly autocorrelated,
and the official forecast is weak.

## Next Steps

Day 6 — LightGBM challenger:
- Same features
- Same train/val/test
- Same metric (MAE)
- Fair comparison

After Day 6:
- If LightGBM wins → improve LightGBM
- If LSTM wins → improve LSTM (L2, fewer units)
- If similar → ensemble