import duckdb
import pandas as pd
import json

DUCKDB_PATH = r"C:\Users\frank\Desktop\Virtual Controller Office\Local Data\Hydro Power\power_market_backoffice.duckdb"

def deep_dive():
    conn = duckdb.connect(DUCKDB_PATH)
    
    # Date Range Check
    date_info = conn.execute("""
        SELECT 
            min(Date) as MinDate, 
            max(Date) as MaxDate, 
            count(distinct Date) as UniqueDays
        FROM dim_time
    """).df().to_dict(orient="records")[0]
    
    # Plant Capacity Breakdown
    plants = conn.execute("""
        SELECT 
            p.PlantID, 
            p.PlantName, 
            p.Region, 
            p.NumAggregates, 
            p.InstalledCapacity_MW,
            SUM(a.MaxOutput_MW) as Aggr_Capacity_Sum_MW,
            string_agg(a.AggrID || ' (' || a.AggrName || ': ' || a.MaxOutput_MW || 'MW)', ', ') as Aggregates
        FROM dim_plant p
        LEFT JOIN dim_aggregate a ON p.PlantID = a.PlantID
        GROUP BY p.PlantID, p.PlantName, p.Region, p.NumAggregates, p.InstalledCapacity_MW
        ORDER BY p.PlantID
    """).df().to_dict(orient="records")

    # Monthly Production & Imbalance Breakdown
    monthly = conn.execute("""
        SELECT 
            t.Month,
            t.MonthName,
            SUM(fp.Measured_MWh) as Measured_MWh,
            SUM(fp.Reported_MWh) as Reported_MWh,
            AVG(fp.SpotPrice_EUR) as Avg_SpotPrice_EUR,
            SUM(fi.ImbalanceCost_EUR) as ImbalanceCost_EUR
        FROM fact_production fp
        JOIN dim_time t ON fp.Date = t.Date
        JOIN fact_imbalance fi ON fp.Date = fi.Date AND fp.PlantID = fi.PlantID
        GROUP BY t.Month, t.MonthName
        ORDER BY t.Month
    """).df().to_dict(orient="records")

    # Top 5 Worst Imbalance Days
    worst_days = conn.execute("""
        SELECT 
            fi.Date,
            fi.PlantID,
            dp.PlantName,
            fi.Allocated_MWh,
            fi.Imbalance_MWh,
            fi.ImbalanceCost_EUR,
            fp.Risk_Flag
        FROM fact_imbalance fi
        JOIN dim_plant dp ON fi.PlantID = dp.PlantID
        JOIN fact_predictions fp ON fi.Date = fp.Date AND fi.PlantID = fp.PlantID
        ORDER BY fi.ImbalanceCost_EUR DESC
        LIMIT 10
    """).df().to_dict(orient="records")

    return {
        "date_info": date_info,
        "plants": plants,
        "monthly": monthly,
        "worst_days": worst_days
    }

if __name__ == "__main__":
    print(json.dumps(deep_dive(), indent=2))
