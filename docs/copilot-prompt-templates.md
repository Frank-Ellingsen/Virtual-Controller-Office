# GitHub Copilot Prompt Templates — Virtual Controller Office

Use these prompts as starting points for Power BI DAX and DuckDB SQL work.

> **Schema check required:** Table and column names below are illustrative. Inspect the current semantic model or DuckDB database and adjust names before using any template. Route DuckDB queries through the existing read-only validation policy; do not execute write statements from generated analytical SQL.

---

## 1. Power BI DAX Measure Templates

### Template 1: Price-Volume-Mix (PVM) Variance Decomposition

```text
Context: Inspect the current Power BI model and identify its actual fact and account tables.
Goal: Write a DAX measure set that decomposes net cost variance into price, volume, and mix effects.
Requirements:
- Calculate base budget cost, actual cost, and total variance using verified model columns.
- Price effect: (actual unit cost - budget unit cost) * actual volume.
- Volume effect: (actual volume - budget volume) * budget unit cost.
- Use HASONEVALUE or ISINSCOPE where needed for matrix drill-down behavior.
- Format currency consistently with the model's locale and reporting currency.
- Explain assumptions and include a reconciliation check against total variance.
```

### Template 2: Contractual Fuel Surcharge Overrun and Cap Savings

```text
Context: Inspect the current model for actual fuel surcharge, budget surcharge, and the applicable cap threshold.
Goal: Create measures for surcharge variance and potential savings at the verified contractual cap.
Requirements:
- Use the model's real table/column names and active filter context.
- Distinguish a fixed percentage-point cap from a percentage increase over budget.
- Avoid row-context/filter-context errors; use SUMX only when row-level evaluation is required.
- State how missing or zero budgets are handled.
```

### Template 3: Dynamic KPI Status Color Formatting

```text
Context: Inspect the model's variance measure and controlling thresholds.
Goal: Return a hex color for conditional formatting.
Requirements:
- Use the verified threshold values and clearly define whether values are absolute or percentage variances.
- Use the project's palette where appropriate: rose #F87171, amber #FBBF24, emerald #34D399.
- Handle BLANK() and boundary values explicitly.
```

## 2. DuckDB SQL Prompt Templates

### Template 1: Variance Aggregation View (Design Only)

```text
Context: Inspect DuckDB's actual tables and columns before proposing a query.
Goal: Propose an aggregation of budget, actual, variance, and variance percentage by the requested dimensions.
Requirements:
- Keep the query read-only and SELECT-only; do not issue CREATE VIEW or other DDL through the query API.
- Filter on verified date columns and requested reporting periods.
- Use NULLIF for division-by-zero protection.
- Include the exact source tables and join keys in the explanation.
- If a persistent view is required, provide the DDL separately and only for an authorized write workflow.
```

### Template 2: Threshold Evaluation Query

```text
Context: Inspect the real fact table, dimension tables, and threshold schema.
Goal: Summarize surcharge variance and compare it with the applicable threshold.
Requirements:
- Use verified join keys and threshold identifiers.
- Report numerator, denominator, variance percentage, threshold, and status separately.
- Avoid hard-coding a threshold when the database provides an active value.
- Submit only a read-only SELECT to the query endpoint.
```

## 3. Using These Templates

1. Open GitHub Copilot Chat in VS Code.
2. Use `@workspace` with the relevant template and the task's reporting context.
3. Ask Copilot to inspect the current schema/model before generating final code.
4. Review the result for correctness, security, and unit consistency; run the relevant tests or DAX validation before release.
