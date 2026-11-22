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

# Hint: The function in duckdb is called sql or execute
result = duckdb.sql(query).df()
print(result.to_string(index=False))
