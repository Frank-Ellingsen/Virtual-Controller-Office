# 🤖 GitHub Copilot Prompt Templates & Recipes
## Virtual Controller Office — Power BI DAX & DuckDB SQL Generation

This guide provides specialized, production-tested prompt templates for GitHub Copilot Chat when building analytical views, DAX measures, and financial data pipelines for the Virtual Controller Office.

---

## 1. 📊 Power BI DAX Measure Prompt Templates

### Template 1: Price-Volume-Mix (PVM) Variance Decomposition
```markdown
Context: Power BI Star Schema with `fact_financial_transactions` and `dim_accounts`.
Goal: Write a DAX measure that decomposes Net Cost Variance into Price Effect, Volume Effect, and Mix Effect.
Requirements:
- Calculate Base Budget Cost, Actual Cost, and Total Variance.
- Price Effect: (Actual Unit Cost - Budget Unit Cost) * Actual Volume.
- Volume Effect: (Actual Volume - Budget Volume) * Budget Unit Cost.
- Format output as Currency ($) with 2 decimal places.
- Use HASONEVALUE or ISINSCOPE for matrix drill-down safety.
```

### Template 2: Contractual Fuel Surcharge Overrun & Cap Savings
```markdown
Context: `fact_logistics_q3` with `fuel_surcharge_actual`, `fuel_surcharge_budget`, and `dim_thresholds`.
Goal: Write DAX measures calculating total fuel overruns and capped savings under Priority Action P1 (15% max cap).
Requirements:
- `Fuel_Surcharge_Actual_Sum` = SUM(fact_logistics_q3[fuel_surcharge_actual])
- `Fuel_Surcharge_Budget_Sum` = SUM(fact_logistics_q3[fuel_surcharge_budget])
- `Fuel_Surcharge_Variance` = Actual - Budget
- `Fuel_Cap_Max_Allowed` = Budget * 1.15
- `P1_Contractual_Savings` = SUMX(fact_logistics_q3, IF([fuel_surcharge_actual] > [Fuel_Cap_Max_Allowed], [fuel_surcharge_actual] - [Fuel_Cap_Max_Allowed], 0))
```

### Template 3: Dynamic KPI Status Color Formatting
```markdown
Context: Power BI Matrix or Card Visuals displaying departmental cost variances.
Goal: Write a DAX measure returning Hex color codes for conditional formatting based on active controlling thresholds.
Requirements:
- If Variance % > +10.0% (Over budget): Return "#F87171" (Rose / Alert)
- If Variance % between +5.0% and +10.0%: Return "#FBBF24" (Amber / Warning)
- If Variance % < +5.0% (Under or on budget): Return "#34D399" (Emerald / Normal)
```

---

## 2. 🦆 DuckDB SQL View Prompt Templates

### Template 1: Star-Schema Variance Aggregation View
```markdown
Context: DuckDB database containing `fact_financial_transactions`, `dim_regions`, `dim_cost_centers`, and `dim_accounts`.
Goal: Create an analytical SQL view `vw_q3_variance_summary`.
Requirements:
- Ensure the query is strict SELECT-only (AST security compliant).
- Filter transaction dates between '2026-07-01' and '2026-09-30'.
- Group by region_name, department, and account_name.
- Calculate `total_budget`, `total_actual`, `total_variance` (actual - budget), and `variance_pct`.
- Handle division by zero safely using NULLIF(total_budget, 0).
```

### Template 2: Automated Threshold Overrun Evaluator View
```markdown
Context: DuckDB tables `fact_logistics_q3`, `dim_regions`, and `dim_thresholds`.
Goal: Create a view `vw_carrier_threshold_evaluations` that flags carrier surcharge overruns.
Requirements:
- Join carrier logistics data with region dimensions.
- Calculate carrier-level fuel surcharge variance % = ((actual_fuel - budget_fuel) / budget_fuel) * 100.
- Compare against `dim_thresholds` where threshold_id = 'TH-04' (15.0%).
- Assign `trigger_action` = CASE WHEN variance_pct > 15.0 THEN 'ENFORCE_P1_SAVINGS' ELSE 'NORMAL' END.
- Sort descending by total fuel variance.
```

---

## 3. 🚀 How to Use in Copilot Chat

1. Open **Copilot Chat** in VS Code (`Ctrl+Alt+I` / `Cmd+Option+I`).
2. Type `@workspace` and paste one of the prompt templates above.
3. Copilot will automatically utilize your `.github/copilot-instructions.md` to generate syntax-perfect DAX code or DuckDB SQL queries matching your workspace conventions!
