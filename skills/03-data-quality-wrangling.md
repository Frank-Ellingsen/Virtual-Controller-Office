# SKILL: Data Quality Audit & Wrangling

## Trigger / When to Use
Use after retrieving raw files or database extracts to inspect, clean, and model datasets in DuckDB.

## Instructions
1. **Schema Audit**: Inspect column data types, missing values, duplicate keys, and outliers.
2. **Standardization**:
   - Align date formats to `YYYY-MM-DD`.
   - Normalize currency values to base currency using exchange rate tables.
3. **Dimensional Modeling**: Build star-schema dimensional tables (`dim_products`, `dim_regions`, `fact_financial_transactions`) in DuckDB.
4. **Lineage Documentation**: Document transformation SQL and generate a data health summary score.

## Constraints
- Never overwrite source raw tables; create transformed analytical views (`vw_...`).