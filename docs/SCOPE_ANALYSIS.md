# Scope Analysis — Onshore vs Total Wind

**Date:** 2026-10-08
**Status:** Draft, awaiting decision

## Numbers (Jan 2024, DK1)

| Metric | Onshore | Total Wind | Delta |
|--------|---------|------------|-------|
| Baseline MAE (DayAhead) | 352.6 MWh | 529.6 MWh | +177.0 |
| Benchmark MAE (Current) | 89.1 MWh | 130.0 MWh | +40.9 |
| Gap (Baseline - Benchmark) | 263.5 MWh | 399.6 MWh | +136.1 |
| Bias (DayAhead) | +298.6 MWh | +460.0 MWh | +161.4 |
| Bias / MAE | 84.7% | 86.9% | +2.2pp |
| Gap / Baseline | 74.7% | 75.4% | +0.7pp |

## Derived: Offshore only
- Baseline MAE: 177.0 MWh
- Benchmark MAE: 40.9 MWh
- Gap: 136.1 MWh

## Key findings
1. The RELATIVE gap is nearly identical (~75% in both).
   Choice between Onshore/Total does not change the challenge size.
2. The BIAS dominates the error (85% in both).
   A simple bias correction may capture most "improvement".
   A naive-bias baseline must precede any ML model.
3. Offshore error is SMALLER in absolute terms (177 vs 352).
   But Energinet's Current handles it better (40.9 vs 89.1).
   Onshore is where the larger problem sits.
4. NMAE (Onshore, approximate): 8.4% with assumed 4,200 MWh/h capacity.
   Capacity value MUST be verified from Energinet official data.

## Open items before decision
- [ ] Verify DK1 installed capacity (Onshore, Offshore, Total) from Energinet
- [ ] Compute NMAE with verified capacity
- [ ] Compute NRMSE for both scopes
- [ ] Run bias-correction baseline: MAE_after_constant_bias_correction
- [ ] Compare with IEC TS 63531 requirements

## Industry context (IEC TS 63531)
- NMAE is the required metric, not MAE.
- Skill Score vs official baseline is required.
- Bias must be reported.
- No standard prescribes scope (Onshore vs Total).

## Bias correction baseline — RESULT

Tested on Jan 2024, Onshore DK1:

- MAE DayAhead (naive):           352.6 MWh
- MAE after constant bias corr:   308.2 MWh
- Improvement:                     44.4 MWh (12.6%)
- Current benchmark:               89.1 MWh
- Remaining gap after bias corr:  219.1 MWh (83% of original gap)

## Conclusion — bias is NOT constant

The bias varies hour-to-hour. A constant correction captures only 12.6%
of the improvement. This means:
1. A trivial ML approach (learn mean bias) will NOT beat the baseline.
2. Real ML (time-varying correction) is required.
3. The challenge is real, not a "learn-bias" exercise.

## Revised decision criteria
- Skill to beat (bias corr only): 12.6%
- Skill target (Current): 74.7%
- ML must exceed 12.6% to be worthwhile.

## FINAL DECISION (2026-10-08)

**Total Wind (Onshore + Offshore) selected.**

Reason: operational relevance to grid operators + larger signal.
Trade-off: DMI feature misalignment on offshore component (accepted).

See DAY_2_DECISIONS.md for full rationale.
