"""Merge Energinet settlement + forecast into one DataFrame.

Steps:
1. Load settlement → extract GT (Total Wind)
2. Load forecast → extract ForecastDayAhead (Offshore + Onshore)
3. Merge by HourUTC
4. Add curtailment flag from ExchangeGE_MWh
5. Save to data/processed/merged.parquet
"""
import json
import pandas as pd
from pathlib import Path

RAW = Path("data/raw/energinet")
PROC = Path("data/processed")
PROC.mkdir(parents=True, exist_ok=True)

WIND_FIELDS = [
    "OffshoreWindGe100MW_MWh",
    "OffshoreWindLt100MW_MWh",
    "OnshoreWindGe50kW_MWh",
    "OnshoreWindLt50kW_MWh",
]


def load_settlement():
    """Load all settlement files, return hourly Total Wind + countertrade."""
    frames = []
    for f in sorted(RAW.glob("settlement_20*.json")):
        # דלג על settlement_2024_01.json (כפילות עם 2024)
        if "2024_01" in f.name:
            continue
        data = json.loads(f.read_text())
        df = pd.DataFrame(data["records"])
        frames.append(df)
    
    df = pd.concat(frames, ignore_index=True)
    df["HourUTC"] = pd.to_datetime(df["HourUTC"])
    
    # Total Wind
    df["actual_wind_mwh"] = df[WIND_FIELDS].sum(axis=1, skipna=True)
    
    # Countertrade
    df["countertrade_mwh"] = df["ExchangeGE_MWh"]
    
    # Keep only needed columns
    return df[[
        "HourUTC", "PriceArea", "actual_wind_mwh", "countertrade_mwh"
    ]].sort_values("HourUTC").drop_duplicates("HourUTC")


def load_forecast():
    """Load all forecast files, return ForecastDayAhead Total Wind."""
    frames = []
    for f in sorted(RAW.glob("forecast_20*.json")):
        data = json.loads(f.read_text())
        df = pd.DataFrame(data["records"])
        frames.append(df)
    
    df = pd.concat(frames, ignore_index=True)
    df["HourUTC"] = pd.to_datetime(df["HourUTC"])
    
    # Filter to relevant types
    df = df[df["ForecastType"].isin(["Offshore Wind", "Onshore Wind"])]
    
    # Pivot: one row per HourUTC, columns = ForecastType
    pivot = df.pivot_table(
        index="HourUTC",
        columns="ForecastType",
        values="ForecastDayAhead",
        aggfunc="first",
    ).reset_index()
    pivot.columns.name = None
    pivot = pivot.rename(columns={
        "Offshore Wind": "forecast_offshore_da",
        "Onshore Wind": "forecast_onshore_da",
    })
    
    pivot["forecast_wind_da"] = (
        pivot["forecast_offshore_da"] + pivot["forecast_onshore_da"]
    )
    
    return pivot.sort_values("HourUTC")


def main():
    print("Loading settlement...")
    settlement = load_settlement()
    print(f"  → {len(settlement)} hourly records")
    print(f"  → range: {settlement['HourUTC'].min()} to {settlement['HourUTC'].max()}")
    
    print("Loading forecast...")
    forecast = load_forecast()
    print(f"  → {len(forecast)} hourly records")
    print(f"  → range: {forecast['HourUTC'].min()} to {forecast['HourUTC'].max()}")
    
    print("Merging...")
    merged = settlement.merge(forecast, on="HourUTC", how="inner")
    print(f"  → {len(merged)} rows after merge")
    
    # Split
    merged["split"] = "train"
    merged.loc[merged["HourUTC"] >= "2025-07-01", "split"] = "validation"
    merged.loc[merged["HourUTC"] >= "2026-01-01", "split"] = "test"
    
    # Save
    out = PROC / "merged.parquet"
    merged.to_parquet(out)
    print(f"\nSaved to {out}")
    print(f"  Train:      {sum(merged['split'] == 'train')}")
    print(f"  Validation: {sum(merged['split'] == 'validation')}")
    print(f"  Test:       {sum(merged['split'] == 'test')}")
    
    # Reconciliation
    print("\nFirst 5 rows:")
    print(merged.head())


if __name__ == "__main__":
    main()