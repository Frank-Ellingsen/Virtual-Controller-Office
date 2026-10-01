import duckdb
import pandas as pd

conn = duckdb.connect(r'C:\Users\frank\Desktop\Virtual Controller Office\Local Data\Hydro Power\power_market_backoffice.duckdb')

piv = conn.execute("""
    SELECT 
        t.Month,
        t.MonthName,
        SUM(CASE WHEN fi.PlantID = 'SKK01' THEN fi.ImbalanceCost_EUR ELSE 0 END) as SKK01_Sundsbarm,
        SUM(CASE WHEN fi.PlantID = 'SKK02' THEN fi.ImbalanceCost_EUR ELSE 0 END) as SKK02_Hjartdola,
        SUM(CASE WHEN fi.PlantID = 'SKK03' THEN fi.ImbalanceCost_EUR ELSE 0 END) as SKK03_Mar,
        SUM(CASE WHEN fi.PlantID = 'SKK04' THEN fi.ImbalanceCost_EUR ELSE 0 END) as SKK04_Tokke,
        SUM(CASE WHEN fi.PlantID = 'SKK05' THEN fi.ImbalanceCost_EUR ELSE 0 END) as SKK05_Nore,
        SUM(fi.ImbalanceCost_EUR) as Total_EUR
    FROM fact_imbalance fi
    JOIN dim_time t ON fi.Date = t.Date
    GROUP BY t.Month, t.MonthName
    ORDER BY t.Month
""").df()

print(piv.to_string())
