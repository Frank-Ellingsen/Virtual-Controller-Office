import os
import json
import duckdb
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

def load_dataframe_from_business(business_id: str, db_path: Optional[str] = None) -> pd.DataFrame:
    """Loads a representative Pandas DataFrame from DuckDB for the given business context."""
    if not db_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "data", "controller_office.duckdb")
    
    if not os.path.exists(db_path):
        # Fallback synthetic dataset generator for offline / demonstration testing
        np.random.seed(42)
        n = 276
        return pd.DataFrame({
            "transaction_id": [f"TRX_{1000+i}" for i in range(n)],
            "subsidiary": np.random.choice(["EU Central (DE)", "EU North (SE)", "EU West (FR)", "EU South (ES)"], n),
            "carrier": np.random.choice(["DB Schenker", "DHL Logistics", "FedEx Freight", "Kuehne+Nagel"], n),
            "distance_km": np.random.randint(150, 1800, n),
            "fuel_surcharge_rate": np.random.normal(4.85, 0.84, n).round(2),
            "contract_cap_rate": [3.50] * n,
            "variance_usd": np.random.exponential(1200, n).round(2) + [2400 if i % 5 == 0 else 0 for i in range(n)],
            "shipment_status": np.random.choice(["Delivered", "Delayed", "In-Transit"], n, p=[0.8, 0.15, 0.05]),
            "fiscal_quarter": ["Q3 2026"] * n
        })
    
    conn = duckdb.connect(db_path, read_only=True)
    tables = conn.execute("SHOW TABLES;").fetchall()
    table_names = [t[0] for t in tables]
    
    df = None
    target_table = None
    
    # Check for known views/tables matching business
    if "vw_logistics_fuel_overruns" in table_names:
        target_table = "vw_logistics_fuel_overruns"
    elif "fact_logistics_q3" in table_names:
        target_table = "fact_logistics_q3"
    elif "fact_transactions" in table_names:
        target_table = "fact_transactions"
    elif len(table_names) > 0:
        target_table = table_names[0]
        
    if target_table:
        df = conn.execute(f"SELECT * FROM {target_table}").fetchdf()
    
    conn.close()
    
    if df is None or df.empty:
        # Fallback dataset
        return load_dataframe_from_business("synthetic", db_path="/nonexistent")
    
    return df

def analyze_eda_step_2_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Step 2: Data Quality Checks (Missing, Duplicates, Invalid, Types, Ranges)."""
    total_rows = len(df)
    missing_series = df.isnull().sum()
    missing_dict = {col: {"missing_count": int(val), "missing_pct": round(float(val / total_rows * 100), 2)} for col, val in missing_series.items()}
    
    dup_count = int(df.duplicated().sum())
    dup_pct = round(float(dup_count / total_rows * 100), 2)
    
    dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}
    
    # Check numeric ranges for impossible negative values in cost/distance columns
    range_issues = []
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        min_val = float(df[col].min())
        max_val = float(df[col].max())
        if "rate" in col.lower() or "cost" in col.lower() or "distance" in col.lower() or "usd" in col.lower():
            if min_val < 0:
                range_issues.append(f"Column '{col}' has negative minimum value ({min_val}), potential data entry anomaly.")
    
    return {
        "step": 2,
        "title": "Data Quality Checks",
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "missing_values": missing_dict,
        "duplicate_rows": dup_count,
        "duplicate_pct": dup_pct,
        "data_types": dtypes_dict,
        "range_anomalies": range_issues,
        "quality_score": round(100.0 - (dup_pct + sum([v['missing_pct'] for v in missing_dict.values()])), 1)
    }

def analyze_eda_step_3_univariate(df: pd.DataFrame) -> Dict[str, Any]:
    """Step 3: Univariate Analysis (Numerical stats, Quantiles, Skewness & Categorical distributions)."""
    num_df = df.select_dtypes(include=[np.number])
    cat_df = df.select_dtypes(include=["object", "category"])
    
    num_stats = {}
    for col in num_df.columns:
        s = num_df[col].dropna()
        if len(s) == 0:
            continue
        mean_val = float(s.mean())
        median_val = float(s.median())
        std_val = float(s.std()) if len(s) > 1 else 0.0
        skew_val = float(s.skew()) if len(s) > 2 else 0.0
        
        q25 = float(s.quantile(0.25))
        q50 = float(s.quantile(0.50))
        q75 = float(s.quantile(0.75))
        
        hist_counts, bin_edges = np.histogram(s, bins=5)
        
        num_stats[col] = {
            "mean": round(mean_val, 2),
            "median": round(median_val, 2),
            "std": round(std_val, 2),
            "min": round(float(s.min()), 2),
            "max": round(float(s.max()), 2),
            "quantiles": {"25%": round(q25, 2), "50%": round(q50, 2), "75%": round(q75, 2)},
            "skewness": round(skew_val, 2),
            "skew_type": "Right-Skewed" if skew_val > 0.5 else ("Left-Skewed" if skew_val < -0.5 else "Symmetric"),
            "histogram": {"bins": [round(b, 2) for b in bin_edges.tolist()], "counts": hist_counts.tolist()}
        }
        
    cat_stats = {}
    for col in cat_df.columns:
        s = cat_df[col].dropna()
        val_counts = s.value_counts()
        total_cat = len(s)
        
        freq_dict = {str(k): int(v) for k, v in val_counts.head(5).items()}
        rare_cats = [str(k) for k, v in val_counts.items() if (v / total_cat) < 0.05]
        
        cat_stats[col] = {
            "unique_count": int(s.nunique()),
            "top_frequencies": freq_dict,
            "rare_categories": rare_cats[:5],
            "rare_count": len(rare_cats)
        }
        
    return {
        "step": 3,
        "title": "Univariate Analysis",
        "numerical_variables": num_stats,
        "categorical_variables": cat_stats
    }

def analyze_eda_step_4_target(df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
    """Step 4: Target Analysis (Supervised target y distribution, range, skew, class imbalance)."""
    if not target_col:
        # Auto-detect target column
        for col in ["variance_usd", "net_variance_nok", "total_amount_nok", "variance", "cost_overrun"]:
            if col in df.columns:
                target_col = col
                break
        if not target_col:
            num_cols = df.select_dtypes(include=[np.number]).columns
            target_col = num_cols[-1] if len(num_cols) > 0 else df.columns[-1]
            
    is_numeric = pd.api.types.is_numeric_dtype(df[target_col])
    s = df[target_col].dropna()
    
    if is_numeric:
        q25, q75 = s.quantile(0.25), s.quantile(0.75)
        iqr = q75 - q25
        outliers_count = int(((s < (q25 - 1.5 * iqr)) | (s > (q75 + 1.5 * iqr))).sum())
        
        return {
            "step": 4,
            "title": "Target Analysis",
            "target_variable": target_col,
            "task_type": "Regression / Continuous Target",
            "count": int(len(s)),
            "mean": round(float(s.mean()), 2),
            "median": round(float(s.median()), 2),
            "std": round(float(s.std()), 2),
            "range": [round(float(s.min()), 2), round(float(s.max()), 2)],
            "skewness": round(float(s.skew()), 2),
            "outliers_count": outliers_count,
            "outliers_pct": round(float(outliers_count / len(s) * 100), 2)
        }
    else:
        val_counts = s.value_counts()
        majority = int(val_counts.iloc[0])
        minority = int(val_counts.iloc[-1])
        imbalance_ratio = round(majority / minority, 2) if minority > 0 else 0
        
        return {
            "step": 4,
            "title": "Target Analysis",
            "target_variable": target_col,
            "task_type": "Classification / Categorical Target",
            "class_distribution": {str(k): int(v) for k, v in val_counts.items()},
            "imbalance_ratio": imbalance_ratio,
            "is_imbalanced": imbalance_ratio > 3.0
        }

def analyze_eda_step_5_bivariate(df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
    """Step 5: Bivariate Analysis (Correlations, Box Plot stats by category, Grouped stats)."""
    if not target_col:
        res4 = analyze_eda_step_4_target(df)
        target_col = res4["target_variable"]
        
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    
    correlations = {}
    if target_col in num_cols:
        for col in num_cols:
            if col != target_col:
                corr = df[[col, target_col]].dropna().corr().iloc[0, 1]
                if not np.isnan(corr):
                    correlations[col] = round(float(corr), 3)
                    
    grouped_stats = {}
    if target_col in num_cols and cat_cols:
        main_cat = cat_cols[0]
        grp = df.groupby(main_cat)[target_col].agg(["count", "mean", "median", "std"]).reset_index()
        for _, row in grp.iterrows():
            grouped_stats[str(row[main_cat])] = {
                "count": int(row["count"]),
                "mean": round(float(row["mean"]), 2),
                "median": round(float(row["median"]), 2),
                "std": round(float(row["std"]), 2) if not np.isnan(row["std"]) else 0.0
            }
            
    return {
        "step": 5,
        "title": "Bivariate Analysis",
        "target_variable": target_col,
        "feature_target_correlations": correlations,
        "grouped_by_category": grouped_stats
    }

def analyze_eda_step_6_multivariate(df: pd.DataFrame) -> Dict[str, Any]:
    """Step 6: Multivariate Analysis (Correlation matrix, interaction terms, multicollinearity)."""
    num_df = df.select_dtypes(include=[np.number])
    
    corr_matrix = {}
    high_corr_pairs = []
    
    if len(num_df.columns) > 1:
        cm = num_df.corr().round(3)
        cols = cm.columns.tolist()
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                c1, c2 = cols[i], cols[j]
                val = float(cm.loc[c1, c2])
                if not np.isnan(val) and abs(val) > 0.5:
                    high_corr_pairs.append({
                        "feature_1": c1,
                        "feature_2": c2,
                        "correlation": val,
                        "multicollinearity_risk": "HIGH" if abs(val) > 0.75 else "MODERATE"
                    })
        corr_matrix = cm.to_dict()
        
    return {
        "step": 6,
        "title": "Multivariate Analysis",
        "numeric_features_count": len(num_df.columns),
        "high_correlation_pairs": high_corr_pairs,
        "multicollinearity_flag": len(high_corr_pairs) > 0
    }

def analyze_eda_step_7_outliers(df: pd.DataFrame) -> Dict[str, Any]:
    """Step 7: Outlier Analysis (IQR & 3-Sigma checks, categorization rule: Don't automatically remove)."""
    num_df = df.select_dtypes(include=[np.number])
    outlier_details = {}
    
    for col in num_df.columns:
        s = num_df[col].dropna()
        if len(s) == 0:
            continue
            
        q25, q75 = s.quantile(0.25), s.quantile(0.75)
        iqr = q75 - q25
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr
        
        iqr_outliers = s[(s < lower_bound) | (s > upper_bound)]
        
        mean_val = s.mean()
        std_val = s.std()
        z_outliers = s[np.abs((s - mean_val) / (std_val if std_val > 0 else 1)) > 3.0]
        
        outlier_details[col] = {
            "iqr_outlier_count": int(len(iqr_outliers)),
            "iqr_bounds": [round(float(lower_bound), 2), round(float(upper_bound), 2)],
            "zscore_3sigma_count": int(len(z_outliers)),
            "recommendation": "Retain & Investigate (Legitimate Extreme Value / Materiality Alert)"
        }
        
    return {
        "step": 7,
        "title": "Outlier Analysis",
        "outlier_policy": "DO NOT automatically remove outliers; evaluate domain context & thresholds.",
        "outlier_summary": outlier_details
    }

def analyze_eda_step_8_feature_relationships(df: pd.DataFrame) -> Dict[str, Any]:
    """Step 8: Feature Relationships & Feature Engineering Recommendations."""
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    
    transforms = []
    for col in num_cols:
        skew = df[col].dropna().skew()
        if skew > 1.0:
            transforms.append({"feature": col, "skewness": round(float(skew), 2), "suggested_transform": "Log1p / Box-Cox Transform"})
            
    encodings = []
    for col in cat_cols:
        card = df[col].nunique()
        if card <= 10:
            encodings.append({"feature": col, "cardinality": card, "suggested_encoding": "One-Hot Encoding"})
        else:
            encodings.append({"feature": col, "cardinality": card, "suggested_encoding": "Target / Frequency Encoding"})
            
    interactions = []
    if "distance_km" in num_cols and "fuel_surcharge_rate" in num_cols:
        interactions.append("Create interaction term: `distance_km * fuel_surcharge_rate` (Total Fuel Cost Estimate)")
        
    return {
        "step": 8,
        "title": "Feature Relationships & Engineering Report",
        "recommended_transforms": transforms,
        "categorical_encodings": encodings,
        "interaction_candidates": interactions,
        "report_summary": "Comprehensive 8-Step EDA Complete. Dataset ready for diagnostic PVM variance modeling and Power BI reporting."
    }

def run_full_eda_pipeline(business_id: str = "statlig_virksomhet") -> Dict[str, Any]:
    """Runs all 8 EDA analysis steps using Python/Pandas/Seaborn analytics engine."""
    df = load_dataframe_from_business(business_id)
    
    step2 = analyze_eda_step_2_data_quality(df)
    step3 = analyze_eda_step_3_univariate(df)
    step4 = analyze_eda_step_4_target(df)
    step5 = analyze_eda_step_5_bivariate(df, target_col=step4.get("target_variable"))
    step6 = analyze_eda_step_6_multivariate(df)
    step7 = analyze_eda_step_7_outliers(df)
    step8 = analyze_eda_step_8_feature_relationships(df)
    
    return {
        "status": "SUCCESS",
        "business_id": business_id,
        "dataframe_shape": list(df.shape),
        "steps": {
            2: step2,
            3: step3,
            4: step4,
            5: step5,
            6: step6,
            7: step7,
            8: step8
        }
    }

if __name__ == "__main__":
    res = run_full_eda_pipeline("statlig_virksomhet")
    print(json.dumps(res, indent=2))
