# SKILL: Power BI & Excel Engineering Standards

## Trigger / When to Use
Use when generating downloadable artifacts (Power BI theme JSON, DAX measures, or automated Excel workbooks).

## Instructions
1. **Power BI Theme JSON**: Generate structured JSON specifying palette tokens, font sizes, card border radii, and visual defaults.
2. **DAX Measures**: Provide formatted, performant DAX code for time-intelligence calculations (`YTD Sales`, `Prior Year Variance`, `Rolling 3M Avg`).
3. **Excel Automation**: Generate Python (`openpyxl`) scripts to build formatted financial workbooks with dynamic PivotTables, conditional formatting, and KPI summary sheets.

## Constraints
- Ensure DAX code avoids `CALCULATE` performance anti-patterns.