# SKILL: Audit Scope & Request Decomposition

## Trigger / When to Use
Use when a new natural-language controlling or audit request is submitted through the Virtual Web UI.

## Instructions
1. **Analyze Objective**: Parse user intent, business unit, time horizon, and target KPIs.
2. **Decompose Sub-tasks**:
   - Data Ingestion target (databases, OneDrive, APIs)
   - Data Wrangling requirements (null handling, currency alignment)
   - Analytical Scope (Variance analysis, forecasting, root-cause diagnosis)
   - Reporting Requirements (Executive 1-pager, Power BI theme, Web UI dashboard)
3. **Draft Execution Plan**: Format output as a structured JSON plan with step dependencies and estimated token budget.
4. **Formulate HITL Approval Card**: Highlight required permissions and sensitive data access points for human confirmation.

## Constraints
- Never execute data ingestion or transformations before human approval.
- Keep execution plan steps to <= 6 distinct stages.