import duckdb
import sqlite3
import pandas as pd
import numpy as np
import os
import json

DUCKDB_PATH = r"C:\Users\frank\Desktop\Virtual Controller Office\Local Data\Hydro Power\power_market_backoffice.duckdb"
SQLITE_PATH = r"C:\Users\frank\Desktop\Virtual Controller Office\Local Data\Hydro Power\power_market_backoffice.sqlite"
CSV_DIR = r"C:\Users\frank\Desktop\Virtual Controller Office\Local Data\Hydro Power"

def run_tests():
    conn = duckdb.connect(DUCKDB_PATH)
    results = {
        "integrity_tests": {},
        "quality_tests": {},
        "controlling_reconciliations": {},
        "imbalance_forecast_audit": {},
        "cross_format_parity": {}
    }

    # 1. INTEGRITY TESTS
    # PK Uniqueness
    pk_checks = {
        "dim_plant": ("PlantID", "SELECT count(distinct PlantID) = count(*) FROM dim_plant"),
        "dim_aggregate": ("AggrID", "SELECT count(distinct AggrID) = count(*) FROM dim_aggregate"),
        "dim_time": ("Date", "SELECT count(distinct Date) = count(*) FROM dim_time"),
        "fact_production": ("Timestamp, AggrID", "SELECT count(distinct Timestamp || '_' || AggrID) = count(*) FROM fact_production"),
        "fact_predictions": ("Date, PlantID", "SELECT count(distinct Date || '_' || PlantID) = count(*) FROM fact_predictions"),
        "fact_imbalance": ("Date, PlantID", "SELECT count(distinct Date || '_' || PlantID) = count(*) FROM fact_imbalance"),
        "fact_reporting": ("Date, PlantID", "SELECT count(distinct Date || '_' || PlantID) = count(*) FROM fact_reporting"),
    }
    
    for table, (pk, sql) in pk_checks.items():
        is_unique = conn.execute(sql).fetchone()[0]
        results["integrity_tests"][f"pk_unique_{table}"] = {
            "pk": pk,
            "status": "PASS" if is_unique else "FAIL"
        }

    # FK Integrity
    fk_checks = {
        "dim_aggregate_to_dim_plant": "SELECT count(*) FROM dim_aggregate WHERE PlantID NOT IN (SELECT PlantID FROM dim_plant)",
        "fact_prod_to_dim_plant": "SELECT count(*) FROM fact_production WHERE PlantID NOT IN (SELECT PlantID FROM dim_plant)",
        "fact_prod_to_dim_aggr": "SELECT count(*) FROM fact_production WHERE AggrID NOT IN (SELECT AggrID FROM dim_aggregate)",
        "fact_prod_to_dim_time": "SELECT count(*) FROM fact_production WHERE Date NOT IN (SELECT Date FROM dim_time)",
        "fact_imb_to_dim_plant": "SELECT count(*) FROM fact_imbalance WHERE PlantID NOT IN (SELECT PlantID FROM dim_plant)",
        "fact_pred_to_dim_plant": "SELECT count(*) FROM fact_predictions WHERE PlantID NOT IN (SELECT PlantID FROM dim_plant)",
        "fact_rep_to_dim_plant": "SELECT count(*) FROM fact_reporting WHERE PlantID NOT IN (SELECT PlantID FROM dim_plant)"
    }

    for name, sql in fk_checks.items():
        orphan_count = conn.execute(sql).fetchone()[0]
        results["integrity_tests"][name] = {
            "orphan_records": orphan_count,
            "status": "PASS" if orphan_count == 0 else "FAIL"
        }

    # Capacity Check (Sum Aggr MaxOutput vs Plant InstalledCapacity)
    cap_query = """
        SELECT p.PlantID, p.PlantName, p.InstalledCapacity_MW, 
               COALESCE(SUM(a.MaxOutput_MW), 0) as AggrSum_MW,
               p.InstalledCapacity_MW - COALESCE(SUM(a.MaxOutput_MW), 0) as Diff_MW
        FROM dim_plant p
        LEFT JOIN dim_aggregate a ON p.PlantID = a.PlantID
        GROUP BY p.PlantID, p.PlantName, p.InstalledCapacity_MW
    """
    cap_df = conn.execute(cap_query).df()
    cap_mismatch = cap_df[cap_df['Diff_MW'].abs() > 0.001]
    results["integrity_tests"]["capacity_alignment"] = {
        "details": cap_df.to_dict(orient="records"),
        "status": "PASS" if len(cap_mismatch) == 0 else "WARN"
    }

    # 2. QUALITY TESTS & ANOMALY FLAGS
    flags_query = """
        SELECT 
            count(*) as TotalRows,
            sum(MissingFlag) as MissingCount,
            sum(NegativeFlag) as NegativeCount,
            sum(SpikeFlag) as SpikeCount,
            sum(FrozenSensorFlag) as FrozenSensorCount,
            count(CASE WHEN Measured_MWh < 0 THEN 1 END) as ActualNegMeasured,
            count(CASE WHEN Reported_MWh < 0 THEN 1 END) as ActualNegReported,
            count(CASE WHEN WaterFlow_m3s < 0 THEN 1 END) as ActualNegWaterFlow,
            count(CASE WHEN SpotPrice_EUR < 0 THEN 1 END) as NegSpotPriceCount,
            min(SpotPrice_EUR) as MinSpotPrice,
            max(SpotPrice_EUR) as MaxSpotPrice,
            min(Measured_MWh) as MinMeasured,
            max(Measured_MWh) as MaxMeasured
        FROM fact_production
    """
    q_stats = conn.execute(flags_query).df().to_dict(orient="records")[0]
    results["quality_tests"]["production_flags_and_boundaries"] = q_stats

    # Null value inspection across fact tables
    null_counts = {}
    for t in ['fact_production', 'fact_imbalance', 'fact_predictions', 'fact_reporting']:
        cols = [c[0] for c in conn.execute(f"DESCRIBE {t}").fetchall()]
        null_sqls = [f"sum(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) as {c}" for c in cols]
        null_res = conn.execute(f"SELECT {', '.join(null_sqls)} FROM {t}").df().to_dict(orient="records")[0]
        null_counts[t] = null_res
    results["quality_tests"]["null_value_counts"] = null_counts

    # 3. CONTROLLING RECONCILIATIONS
    # Measured vs Reported in fact_production
    recon_m_r = conn.execute("""
        SELECT 
            PlantID,
            SUM(Measured_MWh) as Total_Measured_MWh,
            SUM(Reported_MWh) as Total_Reported_MWh,
            SUM(Reported_MWh - Measured_MWh) as Variance_MWh,
            ROUND(SUM(Reported_MWh - Measured_MWh) / SUM(Measured_MWh) * 100, 2) as Variance_Pct
        FROM fact_production
        GROUP BY PlantID
        ORDER BY PlantID
    """).df()
    results["controlling_reconciliations"]["measured_vs_reported_production"] = recon_m_r.to_dict(orient="records")

    # fact_production (daily sum of Reported_MWh) vs fact_reporting (Reported_Total_MWh)
    recon_prod_rep = conn.execute("""
        WITH daily_prod AS (
            SELECT Date, PlantID, SUM(Reported_MWh) as Prod_Reported_Sum
            FROM fact_production
            GROUP BY Date, PlantID
        )
        SELECT 
            r.PlantID,
            SUM(dp.Prod_Reported_Sum) as Prod_Table_Sum_MWh,
            SUM(r.Reported_Total_MWh) as Reporting_Table_Sum_MWh,
            SUM(r.Reported_Total_MWh - dp.Prod_Reported_Sum) as Variance_MWh,
            COUNT(CASE WHEN ABS(r.Reported_Total_MWh - dp.Prod_Reported_Sum) > 0.01 THEN 1 END) as Discrepancy_Days
        FROM fact_reporting r
        JOIN daily_prod dp ON r.Date = dp.Date AND r.PlantID = dp.PlantID
        GROUP BY r.PlantID
        ORDER BY r.PlantID
    """).df()
    results["controlling_reconciliations"]["fact_production_vs_fact_reporting"] = recon_prod_rep.to_dict(orient="records")

    # 4. IMBALANCE & FINANCIAL EXPOSURE AUDIT
    # Calculate imbalance financial statistics
    imb_summary = conn.execute("""
        SELECT 
            fi.PlantID,
            dp.PlantName,
            dp.Region,
            SUM(fi.Allocated_MWh) as Total_Allocated_MWh,
            SUM(fi.Imbalance_MWh) as Total_Imbalance_MWh,
            SUM(fi.ImbalanceCost_EUR) as Total_ImbalanceCost_EUR,
            AVG(fi.ImbalanceCost_EUR) as Avg_Daily_ImbalanceCost_EUR,
            MIN(fi.ImbalanceCost_EUR) as Min_ImbalanceCost_EUR,
            MAX(fi.ImbalanceCost_EUR) as Max_ImbalanceCost_EUR
        FROM fact_imbalance fi
        JOIN dim_plant dp ON fi.PlantID = dp.PlantID
        GROUP BY fi.PlantID, dp.PlantName, dp.Region
        ORDER BY fi.PlantID
    """).df()
    results["imbalance_forecast_audit"]["plant_imbalance_summary"] = imb_summary.to_dict(orient="records")

    # Check relation between Allocated_MWh, Imbalance_MWh, and Actual Daily Production
    imb_formula_check = conn.execute("""
        WITH daily_actual AS (
            SELECT Date, PlantID, SUM(Reported_MWh) as Actual_Reported_MWh
            FROM fact_production
            GROUP BY Date, PlantID
        )
        SELECT 
            fi.Date, fi.PlantID, fi.Allocated_MWh, fi.Imbalance_MWh, fi.ImbalanceCost_EUR,
            da.Actual_Reported_MWh,
            (fi.Allocated_MWh - da.Actual_Reported_MWh) as Calculated_Imbalance_MWh,
            ROUND(fi.Imbalance_MWh - (fi.Allocated_MWh - da.Actual_Reported_MWh), 4) as Imbalance_Formula_Diff
        FROM fact_imbalance fi
        JOIN daily_actual da ON fi.Date = da.Date AND fi.PlantID = da.PlantID
    """).df()
    
    formula_mismatch_count = len(imb_formula_check[imb_formula_check['Imbalance_Formula_Diff'].abs() > 0.01])
    results["imbalance_forecast_audit"]["imbalance_formula_check"] = {
        "mismatch_days_count": formula_mismatch_count,
        "sample_mismatch": imb_formula_check[imb_formula_check['Imbalance_Formula_Diff'].abs() > 0.01].head(5).to_dict(orient="records") if formula_mismatch_count > 0 else []
    }

    # Prediction risk flag efficacy
    pred_risk_eval = conn.execute("""
        SELECT 
            fp.Risk_Flag,
            COUNT(*) as Day_Count,
            AVG(fi.ImbalanceCost_EUR) as Avg_ImbalanceCost_EUR,
            SUM(fi.ImbalanceCost_EUR) as Total_ImbalanceCost_EUR,
            AVG(ABS(fi.Imbalance_MWh)) as Avg_Abs_Imbalance_MWh
        FROM fact_predictions fp
        JOIN fact_imbalance fi ON fp.Date = fi.Date AND fp.PlantID = fi.PlantID
        GROUP BY fp.Risk_Flag
        ORDER BY fp.Risk_Flag
    """).df()
    results["imbalance_forecast_audit"]["risk_flag_efficacy"] = pred_risk_eval.to_dict(orient="records")

    # 5. CROSS-FORMAT PARITY (DuckDB vs SQLite vs CSV)
    parity_results = {}
    
    # Compare row counts with CSV
    for csv_file in ["dim_plant.csv", "dim_aggregate.csv", "dim_time.csv", "fact_production.csv", "fact_predictions.csv", "fact_imbalance.csv", "fact_reporting.csv"]:
        table_name = csv_file.replace(".csv", "")
        csv_path = os.path.join(CSV_DIR, csv_file)
        csv_df = pd.read_csv(csv_path)
        duck_count = conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        csv_count = len(csv_df)
        parity_results[table_name] = {
            "duckdb_rows": duck_count,
            "csv_rows": csv_count,
            "match": duck_count == csv_count
        }
    
    # Compare with SQLite
    if os.path.exists(SQLITE_PATH):
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        sqlite_parity = {}
        for table in ["dim_plant", "dim_aggregate", "dim_time", "fact_production", "fact_predictions", "fact_imbalance", "fact_reporting"]:
            sq_count = sqlite_conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            duck_count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            sqlite_parity[table] = {
                "sqlite_rows": sq_count,
                "duckdb_rows": duck_count,
                "match": sq_count == duck_count
            }
        sqlite_conn.close()
        parity_results["sqlite_parity"] = sqlite_parity

    results["cross_format_parity"] = parity_results

    return results

if __name__ == "__main__":
    res = run_tests()
    print(json.dumps(res, indent=2))
