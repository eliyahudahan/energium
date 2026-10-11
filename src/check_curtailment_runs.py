"""Debug: check curtailment runs in merged.parquet."""
import pandas as pd

df = pd.read_parquet("data/processed/merged.parquet")
df = df.sort_values("HourUTC").reset_index(drop=True)

ct = df["countertrade_mwh"]

print(f"Total rows: {len(ct)}")
print(f"countertrade > 1700: {(ct > 1700).sum()}")
print(f"countertrade < 25:   {(ct < 25).sum()}")
print(f"countertrade < 0:    {(ct < 0).sum()}")

above = ct > 1700
below = ct < 25

transitions = (above.shift(1) & below).sum()
print(f"\nTransitions above -> below: {transitions}")

print(f"\nFirst 10 runs where ct < 25:")
low_runs = []
in_run = False
for i, val in enumerate(below.values):
    if val and not in_run:
        in_run = True
        start = i
    elif not val and in_run:
        low_runs.append((start, i - 1))
        in_run = False
        if len(low_runs) >= 10:
            break

for start, end in low_runs:
    before = ct.iloc[start - 1] if start > 0 else None
    after = ct.iloc[end + 1] if end < len(ct) - 1 else None
    before_str = f"{before:.1f}" if before is not None else "None"
    after_str = f"{after:.1f}" if after is not None else "None"
    print(f"  run [{start}:{end}] len={end-start+1}, "
          f"before={before_str}, after={after_str}")