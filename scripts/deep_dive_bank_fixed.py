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
            ROUND(COUNT(*) * 100.0 / (SELECT count(*) FROM loan_def), 2) as Loan_Pct,
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

    # 2. credit_train_clean.csv deep dive (Credit Score Dataset)
    conn.execute(f"CREATE TABLE credit_train AS SELECT * FROM read_csv_auto('{BANK_DIR.replace('\\', '/')}/credit_train_clean.csv', ALL_VARCHAR=FALSE, AUTO_DETECT=TRUE)")
    
    credit_metrics = conn.execute("""
        SELECT 
            Credit_Score,
            COUNT(*) as Count,
            ROUND(COUNT(*) * 100.0 / (SELECT count(*) FROM credit_train), 2) as Pct,
            AVG(Annual_Income) as Avg_Annual_Income,
            AVG(Outstanding_Debt) as Avg_Outstanding_Debt,
            AVG(Credit_Utilization_Ratio) as Avg_Credit_Utilization,
            AVG(Num_of_Delayed_Payment) as Avg_Delayed_Payments,
            AVG(Total_EMI_per_month) as Avg_Monthly_EMI
        FROM credit_train
        GROUP BY Credit_Score
        ORDER BY Credit_Score
    """).df().to_dict(orient="records")

    # 3. creditcard.csv deep dive (Fraud Detection Dataset)
    conn.execute(f"CREATE TABLE creditcard AS SELECT * FROM read_csv_auto('{BANK_DIR.replace('\\', '/')}/creditcard.csv', ALL_VARCHAR=FALSE, AUTO_DETECT=TRUE)")
    
    fraud_metrics = conn.execute("""
        SELECT 
            Class,
            COUNT(*) as Tx_Count,
            ROUND(COUNT(*) * 100.0 / (SELECT count(*) FROM creditcard), 4) as Tx_Pct,
            SUM(Amount) as Total_Amount,
            AVG(Amount) as Avg_Amount,
            MAX(Amount) as Max_Amount
        FROM creditcard
        GROUP BY Class
        ORDER BY Class
    """).df().to_dict(orient="records")

    # 4. Income comparison (raw vs clean)
    conn.execute(f"CREATE TABLE income_raw AS SELECT * FROM read_csv_auto('{BANK_DIR.replace('\\', '/')}/income.csv', ALL_VARCHAR=FALSE, AUTO_DETECT=TRUE)")
    conn.execute(f"CREATE TABLE income_clean AS SELECT * FROM read_csv_auto('{BANK_DIR.replace('\\', '/')}/income_clean.csv', ALL_VARCHAR=FALSE, AUTO_DETECT=TRUE)")
    
    income_raw_stat = conn.execute("""
        SELECT SalStat, COUNT(*) as Count, ROUND(COUNT()*100.0/(SELECT count(*) FROM income_raw), 2) as Pct
        FROM income_raw GROUP BY SalStat
    """).df().to_dict(orient="records")
    
    income_clean_stat = conn.execute("""
        SELECT salstat, COUNT(*) as Count, ROUND(COUNT()*100.0/(SELECT count(*) FROM income_clean), 2) as Pct
        FROM income_clean GROUP BY salstat
    """).df().to_dict(orient="records")

    return {
        "loan_default_metrics": loan_metrics,
        "credit_score_train_metrics": credit_metrics,
        "fraud_metrics": fraud_metrics,
        "income_raw_distribution": income_raw_stat,
        "income_clean_distribution": income_clean_stat
    }

if __name__ == "__main__":
    print(json.dumps(deep_dive_bank(), indent=2))
