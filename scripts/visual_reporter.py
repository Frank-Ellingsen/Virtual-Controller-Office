import os
import io
import base64
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import eda_engine

# -----------------------------------------------------------------------------
# Edward Tufte Dark Slate Styling Preset
# -----------------------------------------------------------------------------
plt.style.use('dark_background')
DARK_BG = "#0f172a"
PANEL_BG = "#1e293b"
TEXT_COLOR = "#e2e8f0"
ACCENT_BLUE = "#6366f1"
ACCENT_GREEN = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED = "#f43f5e"

def apply_tufte_styling(ax, title=""):
    """Applies Tufte Data-Ink principles: removes vertical gridlines, borders, drop shadows."""
    ax.set_facecolor(PANEL_BG)
    if ax.figure:
        ax.figure.patch.set_facecolor(DARK_BG)
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#334155')
    ax.spines['bottom'].set_color('#334155')
    
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    
    # Remove vertical gridlines, keep subtle horizontal gridlines only
    ax.grid(True, axis='y', linestyle='--', alpha=0.2, color='#475569')
    ax.grid(False, axis='x')
    
    if title:
        ax.set_title(title, color=TEXT_COLOR, fontsize=11, fontweight='bold', pad=12)

def fig_to_base64_svg(fig) -> str:
    """Converts a Matplotlib figure into a base64-encoded SVG image string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='svg', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    svg_str = buf.read().decode('utf-8')
    plt.close(fig)
    return f"data:image/svg+xml;base64,{base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')}"

# -----------------------------------------------------------------------------
# Exploratory Chart Generators
# -----------------------------------------------------------------------------
def generate_univariate_distribution_chart(df: pd.DataFrame, num_col: Optional[str] = None) -> Dict[str, Any]:
    """Generates Tufte-styled Histogram + KDE distribution chart."""
    if not num_col:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        num_col = num_cols[0] if num_cols else "distance_km"
        
    s = df[num_col].dropna()
    
    fig, ax = plt.subplots(figsize=(6.5, 3.5), dpi=100)
    sns.histplot(s, kde=True, color=ACCENT_BLUE, ax=ax, bins=12, edgecolor="#334155")
    
    mean_val = s.mean()
    median_val = s.median()
    
    ax.axvline(mean_val, color=ACCENT_AMBER, linestyle='--', linewidth=1.5, label=f"Mean: {mean_val:.2f}")
    ax.axvline(median_val, color=ACCENT_GREEN, linestyle='-', linewidth=1.5, label=f"Median: {median_val:.2f}")
    
    apply_tufte_styling(ax, title=f"Univariate Distribution: {num_col}")
    ax.legend(facecolor=PANEL_BG, edgecolor='#334155', fontsize=8)
    
    b64_image = fig_to_base64_svg(fig)
    return {
        "column": num_col,
        "chart_type": "histogram_kde",
        "svg_image": b64_image,
        "chart_data": {
          "mean": round(float(mean_val), 2),
          "median": round(float(median_val), 2),
          "std": round(float(s.std()), 2)
        }
    }

def generate_multivariate_correlation_heatmap(df: pd.DataFrame) -> Dict[str, Any]:
    """Generates Tufte-styled Pearson Correlation Heatmap."""
    num_df = df.select_dtypes(include=[np.number])
    if len(num_df.columns) < 2:
        return {"status": "error", "message": "Not enough numeric columns for correlation matrix."}
        
    corr = num_df.corr().round(2)
    
    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=100)
    cmap = sns.diverging_palette(220, 20, as_cmap=True)
    
    sns.heatmap(
        corr, 
        annot=True, 
        fmt=".2f", 
        cmap=cmap, 
        center=0, 
        ax=ax, 
        cbar=True,
        square=True,
        linewidths=0.5,
        linecolor='#0f172a',
        annot_kws={"size": 8, "weight": "bold", "color": TEXT_COLOR}
    )
    
    apply_tufte_styling(ax, title="Multivariate Feature Correlation Matrix (Pearson r)")
    b64_image = fig_to_base64_svg(fig)
    
    return {
        "chart_type": "correlation_heatmap",
        "svg_image": b64_image,
        "correlation_matrix": corr.to_dict()
    }

def generate_outlier_boxplot_chart(df: pd.DataFrame, num_col: Optional[str] = None) -> Dict[str, Any]:
    """Generates Outlier Boxplot & Stripplot displaying IQR boundaries."""
    if not num_col:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        num_col = num_cols[-1] if num_cols else "variance_usd"
        
    s = df[num_col].dropna()
    
    fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=100)
    sns.boxplot(x=s, ax=ax, color='#312e81', boxprops=dict(alpha=0.7), fliersize=0)
    sns.stripplot(x=s, ax=ax, color=ACCENT_RED, size=5, jitter=0.2, alpha=0.8)
    
    apply_tufte_styling(ax, title=f"Outlier & Dispersion Profile: {num_col}")
    b64_image = fig_to_base64_svg(fig)
    
    q25, q75 = s.quantile(0.25), s.quantile(0.75)
    iqr = q75 - q25
    
    return {
        "column": num_col,
        "chart_type": "outlier_boxplot",
        "svg_image": b64_image,
        "iqr_bounds": [round(float(q25 - 1.5*iqr), 2), round(float(q75 + 1.5*iqr), 2)]
    }

def generate_pvm_bridge_waterfall_chart() -> Dict[str, Any]:
    """Generates Price-Volume-Mix (PVM) Variance Waterfall Bridge chart."""
    components = ["Base Budget", "Price Variance", "Volume Variance", "Mix Variance", "Actual Spend"]
    values = [2400000, 163200, 48000, 28800, 2640000]
    
    fig, ax = plt.subplots(figsize=(6.5, 3.5), dpi=100)
    colors = [ACCENT_BLUE, ACCENT_RED, ACCENT_AMBER, ACCENT_AMBER, ACCENT_GREEN]
    
    bars = ax.bar(components, values, color=colors, width=0.55, edgecolor='#334155')
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"${height:,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  
                    textcoords="offset points",
                    ha='center', va='bottom', color=TEXT_COLOR, fontsize=8, fontweight='bold')
                    
    apply_tufte_styling(ax, title="Price-Volume-Mix (PVM) Controlling Variance Waterfall")
    plt.xticks(rotation=15)
    
    b64_image = fig_to_base64_svg(fig)
    return {
        "chart_type": "pvm_waterfall",
        "svg_image": b64_image,
        "components": components,
        "values": values
    }

def generate_all_eda_visuals(business_id: str = "statlig_virksomhet") -> Dict[str, Any]:
    """Generates a complete suite of EDA exploratory visual charts."""
    df = eda_engine.load_dataframe_from_business(business_id)
    
    univariate_chart = generate_univariate_distribution_chart(df)
    heatmap_chart = generate_multivariate_correlation_heatmap(df)
    outlier_chart = generate_outlier_boxplot_chart(df)
    pvm_chart = generate_pvm_bridge_waterfall_chart()
    
    return {
        "status": "SUCCESS",
        "business_id": business_id,
        "visuals": {
            "univariate": univariate_chart,
            "multivariate": heatmap_chart,
            "outliers": outlier_chart,
            "pvm_bridge": pvm_chart
        }
    }

if __name__ == "__main__":
    res = generate_all_eda_visuals("statlig_virksomhet")
    print("Generated EDA Visuals Suite successfully! SVG Images created.")
