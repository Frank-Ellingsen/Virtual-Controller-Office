# SKILL: Exploratory Visual Reporting & Tufte Ergonomic Design Standards

## Trigger / When to Use
Use when generating exploratory visualizations, Python Seaborn/Matplotlib chart artifacts, interactive Web UI Canvas dashboards, Price-Volume-Mix (PVM) variance bridges, or Power BI JSON themes.

## Instructions
1. **Data-Ink Ratio Enforcement (Edward Tufte)**:
   - Remove vertical gridlines from all bar charts, histograms, and Gantt views.
   - Delete background drop shadows, heavy borders, and decorative icons.
   - Align text columns to the left, numeric columns to the right, and decimal points vertically.
   - Use direct data labels on charts instead of detached legend boxes wherever possible.

2. **Color Palette & Visual Callouts**:
   - Use sleek dark slate background colors (`#0f172a` / `#1e293b`).
   - Use muted slate text (`#94a3b8`) for context and baseline metrics.
   - Reserve bright accent colors (`#f43f5e` / `#f59e0b` / `#10b981`) exclusively for active financial variances, threshold overruns, or risk alerts.

3. **Exploratory Visual Types**:
   - **Data Quality Matrix**: Heatmap of missing values and duplicate ratios across feature columns.
   - **Univariate Distribution**: Histogram + KDE (Kernel Density Estimate) curve with mean/median reference lines.
   - **Target Profile**: Regression/Classification target distribution with IQR outlier boundaries.
   - **Bivariate Cross-Tab**: Feature vs Target scatter plot with linear trend fit and category box plots.
   - **Multivariate Correlation Matrix**: Tufte dark-slate heatmap displaying Pearson $r$ correlation values.
   - **Outlier Box Plot**: Box & whisker plot highlighting $3\sigma$ and $1.5\cdot\text{IQR}$ anomalies without automatic deletion.
   - **PVM Variance Bridge**: Price-Volume-Mix waterfall/bridge chart decomposing budget overruns.

4. **Power BI Theme JSON**:
   - Generate structured JSON with custom color palettes, font definitions (Inter / Outfit / Roboto), and zero-border card properties.
