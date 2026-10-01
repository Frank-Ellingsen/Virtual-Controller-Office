import duckdb
import pandas as pd

conn = duckdb.connect(r'C:\Users\frank\Desktop\Virtual Controller Office\Local Data\Hydro Power\power_market_backoffice.duckdb')

df = conn.execute("""
    SELECT 
        Date, 
        PlantID, 
        Allocated_MWh, 
        Imbalance_MWh, 
        ImbalanceCost_EUR, 
        ROUND(ImbalanceCost_EUR / ABS(NULLIF(Imbalance_MWh, 0)), 2) as Unit_Penalty_EUR_per_MWh
    FROM fact_imbalance 
    WHERE Date LIKE '2026-11%' 
    ORDER BY ImbalanceCost_EUR DESC 
    LIMIT 20
""").df()

print(df.to_string())
