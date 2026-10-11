"""Download ProductionConsumptionSettlement for Energium.

Periods: 2024-01-01 → 2026-02-01
Region: DK1
"""
import json
import requests
from pathlib import Path

URL = "https://api.energidataservice.dk/dataset/ProductionConsumptionSettlement"
OUT_DIR = Path("data/raw/energinet")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PERIODS = [
    ("2024_01", "2024-01-01", "2024-02-01"),
    ("2024",    "2024-01-01", "2025-01-01"),
    ("2025",    "2025-01-01", "2026-01-01"),
    ("2026_jan","2026-01-01", "2026-02-01"),
]

for label, start, end in PERIODS:
    out = OUT_DIR / f"settlement_{label}.json"
    if out.exists():
        print(f"skip {out} (exists)")
        continue
    print(f"fetching {label} {start} → {end}")
    r = requests.get(URL, params={
        "start": start,
        "end": end,
        "filter": json.dumps({"PriceArea": ["DK1"]}),
        "limit": 0,
    }, timeout=180)
    r.raise_for_status()
    data = r.json()
    out.write_text(json.dumps(data))
    print(f"  → {data.get('total', '?')} records, saved to {out}")