import os
import duckdb
import pandas as pd
import json

BANK_DIR = r"C:\Users\frank\Desktop\Virtual Controller Office\Local Data\Bank"

def deep_dive_bank():
    conn = duckdb.connect()
    
    # 1. Loan_Default.csv deep dive
    conn.execute(f"CREATE TABLE loan_def AS SELECT * FROM read_csv_auto('{BANK_DIR.replace('\\', '/')}/Loan_Default.csv', ALL_VARCHAR=FALSE, AUTO_DETECT=TRUE)")
    
    loan_metrics = conn.execute("""
        SELECT 
            Status,
            COUNT(*) as Loan_Count,
            SUM(loan_amount) as Total_Loan_Volume,
            AVG(loan_amount) as Avg_Loan_Amount,
            AVG(property_value) as Avg_Property_Value,
            AVG(rate_of_interest) as Avg_Interest_Rate,
            AVG(LTV) as Avg_LTV,
            MAX(LTV) as Max_LTV,
            COUNT(CASE WHEN LTV > 100 THEN 1 END) as High_LTV_Count,
            COUNT(CASE WHEN LTV > 500 THEN 1 END) as Severe_LTV_Outlier_Count
        FROM loan_def
        GROUP BY Status
    """).df().to_dict(orient="records")

    # 2. credit_train_clean.csv deep dive
    conn.execute(f"CREATE TABLE credit_train AS SELECT * FROM read_csv_auto('{BANK_DIR.replace('\\', '/')}/credit_train_clean.csv', ALL_VARCHAR=FALSE, AUTO_DETECT=TRUE)")
    
    credit_metrics = conn.execute("""
        SELECT 
            "Loan Status" as Loan_Status,
            COUNT(*) as Loan_Count,
            COUNT(CASE WHEN "Current Loan Amount" = 99999999 THEN 1 END) as Placeholder_99M_Count,
            AVG(CASE WHEN "Current Loan Amount" < 99999999 THEN "Current Loan Amount" END) as Real_Avg_Loan_Amount,
            SUM(CASE WHEN "Current Loan Amount" < 99999999 THEN "Current Loan Amount" END) as Real_Total_Loan_Volume,
            COUNT(CASE WHEN "Credit Score" > 850 THEN 1 END) as Scaled_Credit_Score_Outliers,
            AVG(CASE WHEN "Credit Score" <= 850 THEN "Credit Score" ELSE "Credit Score"/10.0 END) as Clean_Avg_Credit_Score
        FROM credit_train
        GROUP BY "Loan Status"
    """).df().to_dict(orient="records")

    # 3. creditcard.csv deep dive
    conn.execute(f"CREATE TABLE creditcard AS SELECT * FROM read_csv_auto('{BANK_DIR.replace('\\', '/')}/creditcard.csv', ALL_VARCHAR=FALSE, AUTO_DETECT=TRUE)")
    
    fraud_metrics = conn.execute("""
        SELECT 
            Class,
            COUNT(*) as Tx_Count,
            SUM(Amount) as Total_Amount,
            AVG(Amount) as Avg_Amount,
            MAX(Amount) as Max_Amount
        FROM creditcard
        GROUP BY Class
    """).df().to_dict(orient="records")

    # 4. Income comparison (raw vs clean)
    conn.execute(f"CREATE TABLE income_raw AS SELECT * FROM read_csv_auto('{BANK_DIR.replace('\\', '/')}/income.csv', ALL_VARCHAR=FALSE, AUTO_DETECT=TRUE)")
    conn.execute(f"CREATE TABLE income_clean AS SELECT * FROM read_csv_auto('{BANK_DIR.replace('\\', '/')}/income_clean.csv', ALL_VARCHAR=FALSE, AUTO_DETECT=TRUE)")
    
    income_comp = {
        "raw_count": conn.execute("SELECT count(*) FROM income_raw").fetchone()[0],
        "raw_duplicates": conn.execute("SELECT count(*) FROM income_raw") .fetchone()[0] - conn.execute("SELECT count(*) FROM (SELECT DISTINCT * FROM income_raw)").fetchone()[0],
        "clean_count": conn.execute("SELECT count(*) FROM income_clean").fetchone()[0],
        "clean_duplicates": conn.execute("SELECT count(*) FROM income_clean").fetchone()[0] - conn.execute("SELECT count(*) FROM (SELECT DISTINCT * FROM income_clean)").fetchone()[0]
    }

    return {
        "loan_default_metrics": loan_metrics,
        "credit_train_metrics": credit_metrics,
        "fraud_metrics": fraud_metrics,
        "income_comparison": income_comp
    }

if __name__ == "__main__":
    print(json.dumps(deep_dive_bank(), indent=2))
