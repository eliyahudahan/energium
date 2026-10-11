# Curtailment Filter

**Reference:** Jørgensen et al. (2025), Section 2.1.

## What the Paper Mandates

The paper is explicit:
> "We exclude observations using a filter under the following conditions: 
> If the countertrade volume exceeds 1700 MW before and after a period 
> where it drops below 25 MW, or if the spot price is negative."

> "Observations are removed wherever the filter value is zero."

**This is a removal, not a flag.** We implement it as specified.

## Period Used in the Paper

- **Paper's period:** 2022-01-01 → 2024-10-12
- **Our period:** 2024-01-31 → 2026-01-31
- **Overlap:** 2024-01-31 → 2024-10-12 (~9 months)

The paper's filter was designed for a period when curtailment was 
frequent. Our period is later, and the paper itself predicts fewer 
events:

> "Going forward the curtailment issue will be less pronounced and is 
> already fading due to new installations and expansions in the German 
> energy network since July 2023."

## Filter Definition (from the Paper)

Two conditions (OR):
1. countertrade > 1700 → drops below 25 → countertrade > 1700 again
2. spot price < 0

- **Padding:** 2 observations each side = 4 hours (on hourly data)
- **Spot price condition:** Not applied. The paper says it was only 
  used 01-2022 to 07-2023 (special regulation data unavailable after).

## Data Source

- **Field:** `ExchangeGE_MWh` from `ProductionConsumptionSettlement`
- **Meaning:** Net exchange between DK1 and Germany (MWh)
- **Sign:** positive = export from DK to Germany, negative = import
- **Verified:** January 2024, DK1

## Implementation Decisions

The paper specifies the rule but not the algorithm. Our decisions:

- **"Period"** = contiguous run of observations where countertrade < 25 MW.
- **"Before/after"** = the immediate observation before/after the run.
- **Padding** = `rolling(5, center=True).max()` on the boolean mask.

**Rationale:** A "period" in natural language is a continuous stretch. 
"Before/after" in the singular suggests the immediate neighbor.

## What We Observe in the Data (2024-2026, DK1)

**Dataset:** merged.parquet, 17,256 hourly observations.

| Metric | Value | % |
|---|---|---|
| Total rows | 17,256 | 100.0 |
| countertrade > 1700 | 1,010 | 5.9 |
| countertrade < 25 | 12,017 | 69.6 |
| countertrade < 0 | 11,607 | 67.3 |
| Low-countertrade runs | 928 | — |
| Transitions above → below | 9 | — |
| **Runs matching the paper's full rule** | **0** | **0.00** |

## The Finding

**No events in 2024-2026 satisfy the paper's filter exactly.**

The 9 transitions from high countertrade to low countertrade did 
not complete the pattern: they did not return to > 1700 MW 
immediately after the low period.

This is **consistent with the paper's own prediction** that curtailment 
is fading after July 2023. Our period (2024-2026) is entirely after 
that date.

## Comparison with the Paper

| Aspect | Paper (2022-2024) | Energium (2024-2026) |
|---|---|---|
| Period | 2022-01 to 2024-10 | 2024-01 to 2026-01 |
| Curtailment events | Frequent | **0 matching full rule** |
| Spot price condition | Applied until 2023-07 | Not applicable |
| Context | Pre-fading | Post-fading |

**Note:** The paper's quantitative results are not directly comparable 
to ours because the periods differ and the curtailment regime has 
changed. Our work applies the paper's *methodology* to a *different 
period*, not the same data.

## Our Decision

**Apply the paper's filter as specified. The result is 0 removals.**

**Rationale:**
- The paper mandates removal of matching events. There are none.
- The data confirms the paper's own prediction of fading curtailment.
- Flagging 0 events is equivalent to no filtering — the dataset 
  remains complete.
- Any deviation from the paper's rule would require justification 
  we do not have.

## What We Do NOT Claim

- We do not claim the absence of curtailment events means the 
  phenomenon does not exist — only that it does not match the 
  paper's specific rule in our period.
- We do not alter the paper's rule to produce more removals.
- We do not use this result to criticize the paper — the paper 
  anticipated this fading.

## Implementation

Implemented in `src/apply_curtailment_filter.py`:
1. Identifies all runs where countertrade < 25 MW.
2. Checks whether the observation before/after exceeds 1700 MW.
3. Flags matching runs with 2-observation padding on each side.
4. Removes flagged rows.

**Result:** 0 rows removed. Dataset unchanged.

## Reference

Jørgensen, B.S., Møller, J.K., Nystrup, P., Madsen, H. (2025).
Sequential methods for error correction of probabilistic wind power forecasts.
Expert Systems with Applications, Vol. 284, Article 127872.