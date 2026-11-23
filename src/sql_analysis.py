import duckdb

query = """
SELECT 
    MONTH(HourUTC) AS month,
    is_big_ramp,
    COUNT(*) AS total_hours,
    ROUND(AVG(ABS(error)), 2) AS mae
FROM 'data/processed/features.parquet'
WHERE YEAR(HourUTC) = 2025
GROUP BY MONTH(HourUTC), is_big_ramp
ORDER BY month ASC, is_big_ramp ASC;
"""

result = duckdb.sql(query).df()
print("--- Monthly Error by Wind Ramp ---")
print(result.to_string(index=False))

query_hour = """
SELECT 
    HOUR(HourUTC) AS hour,
    COUNT(*) AS total_hours,
    ROUND(AVG(ABS(error)), 2) AS mae,
    ROUND(AVG(error), 2) AS bias
FROM 'data/processed/features.parquet'
WHERE YEAR(HourUTC) = 2025
GROUP BY HOUR(HourUTC)
ORDER BY mae DESC;
"""

result_hour = duckdb.sql(query_hour).df()
print("\n--- Hourly Forecast Error & Bias (2025) ---")
print(result_hour.to_string(index=False))
