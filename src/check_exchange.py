import json
import requests

url = "https://api.energidataservice.dk/dataset/ProductionConsumptionSettlement"
params = {
    "start": "2024-01-01",
    "end": "2024-02-01",
    "filter": json.dumps({"PriceArea": ["DK1"]}),
    "limit": 0,
}

r = requests.get(url, params=params, timeout=60)
r.raise_for_status()
data = r.json()
records = data["records"]

print(f"Total records: {len(records)}")

values = [r["ExchangeGE_MWh"] for r in records if r.get("ExchangeGE_MWh") is not None]
print(f"\nExchangeGE_MWh:")
print(f"  min:  {min(values):.2f}")
print(f"  max:  {max(values):.2f}")
print(f"  mean: {sum(values)/len(values):.2f}")

above_1700 = sum(1 for v in values if v > 1700)
below_25 = sum(1 for v in values if v < 25)
negative = sum(1 for v in values if v < 0)

print(f"\n  > 1700: {above_1700}")
print(f"  < 25:   {below_25}")
print(f"  < 0:    {negative}")