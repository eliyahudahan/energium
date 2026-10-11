"""Apply the curtailment filter from Jørgensen et al. (2025), Section 2.1.

The paper mandates REMOVAL, not flagging:
  "Observations are removed wherever the filter value is zero."
"""
import pandas as pd
from pathlib import Path

PROC = Path("data/processed")


def find_low_runs(countertrade: pd.Series, threshold: float = 25.0):
    """Find contiguous runs where countertrade < threshold.
    
    Returns list of (start_idx, end_idx) inclusive tuples.
    """
    below = countertrade < threshold
    runs = []
    in_run = False
    start = None
    for i, val in enumerate(below.values):
        if val and not in_run:
            in_run = True
            start = i
        elif not val and in_run:
            runs.append((start, i - 1))
            in_run = False
    if in_run:
        runs.append((start, len(below) - 1))
    return runs


def flag_curtailment(countertrade: pd.Series) -> pd.Series:
    """Return boolean mask: True = remove (per paper)."""
    n = len(countertrade)
    mask = pd.Series(False, index=countertrade.index)
    runs = find_low_runs(countertrade, threshold=25.0)
    print(f"  Low-countertrade runs found: {len(runs)}")
    
    flagged_count = 0
    for start, end in runs:
        before_ok = (start > 0) and (countertrade.iloc[start - 1] > 1700.0)
        after_ok = (end < n - 1) and (countertrade.iloc[end + 1] > 1700.0)
        
        if before_ok and after_ok:
            mask.iloc[start:end + 1] = True
            flagged_count += 1
    
    print(f"  Runs matching paper's rule: {flagged_count}")
    
    # Padding: 2 observations each side = 5-observation window
    mask = mask.rolling(5, center=True, min_periods=1).max().fillna(0).astype(bool)
    return mask


def main():
    print("Loading merged.parquet...")
    df = pd.read_parquet(PROC / "merged.parquet")
    df = df.sort_values("HourUTC").reset_index(drop=True)
    print(f"  Original rows: {len(df)}")
    
    print("\nApplying curtailment filter (paper definition)...")
    mask = flag_curtailment(df["countertrade_mwh"])
    
    removed = mask.sum()
    pct = removed / len(df) * 100
    print(f"\nFlagged for removal: {removed} ({pct:.2f}%)")
    
    # REMOVE — per paper
    df_clean = df[~mask].copy()
    df_clean["curtailment"] = False  # all kept rows are not curtailment
    df_clean.to_parquet(PROC / "merged_clean.parquet")
    
    print(f"\nKept: {len(df_clean)}")
    print(f"Removed: {removed}")
    print(f"\nSaved to {PROC / 'merged_clean.parquet'}")
    
    # By split
    print(f"\nBy split (after removal):")
    print(df_clean.groupby("split").size())


if __name__ == "__main__":
    main()