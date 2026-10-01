import os
import duckdb
import pandas as pd
import numpy as np
import json

BANK_DIR = r"C:\Users\frank\Desktop\Virtual Controller Office\Local Data\Bank"

def inspect_bank_data():
    conn = duckdb.connect()
    
    files = [f for f in os.listdir(BANK_DIR) if f.endswith(".csv")]
    results = {}
    
    for f in sorted(files):
        file_path = os.path.join(BANK_DIR, f)
        tname = f"t_{f.replace('.', '_').replace('-', '_').replace(' ', '_')}"
        
        # Load CSV into DuckDB
        conn.execute(f"CREATE TABLE {tname} AS SELECT * FROM read_csv_auto('{file_path.replace('\\', '/')}', ALL_VARCHAR=FALSE, AUTO_DETECT=TRUE)")
        
        row_count = conn.execute(f"SELECT count(*) FROM {tname}").fetchone()[0]
        col_info = conn.execute(f"DESCRIBE {tname}").fetchall()
        col_names = [c[0] for c in col_info]
        col_types = {c[0]: c[1] for c in col_info}
        
        # Check null counts
        null_sqls = [f'sum(CASE WHEN "{c}" IS NULL THEN 1 ELSE 0 END) as "{c}"' for c in col_names]
        null_res = conn.execute(f"SELECT {', '.join(null_sqls)} FROM {tname}").df().to_dict(orient="records")[0]
        
        # Exact duplicate row count
        distinct_count = conn.execute(f"SELECT count(*) FROM (SELECT DISTINCT * FROM {tname})").fetchone()[0]
        dup_count = row_count - distinct_count
        
        # Statistical summary for numeric columns
        num_cols = [c for c, t in col_types.items() if t in ('DOUBLE', 'BIGINT', 'FLOAT', 'INTEGER', 'HUGEINT', 'DECIMAL')]
        
        stat_summary = {}
        for c in num_cols[:15]: # Limit to top 15 numeric cols for summary
            s = conn.execute(f"""
                SELECT 
                    min("{c}") as min_val,
                    approx_quantile("{c}", 0.25) as q25,
                    median("{c}") as median_val,
                    approx_quantile("{c}", 0.75) as q75,
                    max("{c}") as max_val,
                    avg("{c}") as mean_val,
                    stddev_samp("{c}") as std_val
                FROM {tname}
            """).df().to_dict(orient="records")[0]
            stat_summary[c] = s

        # Target class distributions if applicable
        class_dist = {}
        possible_target_cols = ['Class', 'Default', 'Status', 'Loan_Status', 'loan_status', 'default', 'target', 'Target', 'Loan_Default', 'status']
        for target_col in col_names:
            if target_col in possible_target_cols or 'default' in target_col.lower() or 'status' in target_col.lower() or 'class' in target_col.lower():
                dist = conn.execute(f'SELECT "{target_col}", count(*) as cnt, ROUND(count(*)*100.0/{row_count}, 4) as pct FROM {tname} GROUP BY "{target_col}"').df().to_dict(orient="records")
                class_dist[target_col] = dist

        results[f] = {
            "file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2),
            "row_count": row_count,
            "column_count": len(col_names),
            "duplicate_rows": dup_count,
            "null_summary": {k: v for k, v in null_res.items() if v > 0},
            "columns": col_names,
            "column_types": col_types,
            "target_distributions": class_dist,
            "numeric_stats_sample": stat_summary
        }
        
    return results

if __name__ == "__main__":
    res = inspect_bank_data()
    print(json.dumps(res, indent=2))
