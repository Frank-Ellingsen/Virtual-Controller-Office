# GitHub Copilot Custom Instructions — Agentic Virtual Controller Office

These instructions provide project-level context, architectural rules, code conventions, and safety guardrails for GitHub Copilot when working in this repository.

---

## 🏢 Project Overview
The **Virtual Controller Office** is an enterprise-grade multi-agent financial controlling platform built for variance analysis, automated monthly close orchestration, AST-validated SQL retrieval over DuckDB, and real-time Web UI telemetry.

### Tech Stack
* **Language**: Python 3.12+
* **Backend Framework**: FastAPI (`server.py`), Uvicorn, Pydantic v2
* **Database & Analytical Engine**: DuckDB (`controller_office.duckdb`), SQLite, Pandas, Polars
* **SQL Parsing & AST Security**: `sqlglot` (Abstract Syntax Tree validator enforcing `SELECT`-only execution)
* **Frontend Web UI**: HTML5, Tailwind CSS, Vanilla JavaScript (`index.html` / `index_dashboard_v4.html.txt`)
* **Visualization & EDA**: Seaborn, Matplotlib (headless `Agg` backend), Plotly
* **External APIs**: Serper REST API for external web research benchmarks

---

## 🤖 Multi-Agent Hub-and-Spoke Architecture
When generating or editing agentic code, strictly maintain the 6-Agent hub-and-spoke topology:

1. **Agent 1 (Supervisor / Intake Router)**: Parses user financial prompts, decomposes multi-step audit plans, and enforces Human-In-The-Loop (HITL) gates.
2. **Agent 2 (Data Retrieval Worker)**: Manages local DuckDB RAG queries and loads `Skill 4` (Serper API) for external market benchmarking when local anomalies occur.
3. **Agent 3 (Data Modeling Worker)**: Handles data hygiene, ETL, and star-schema views (`dim_regions`, `dim_cost_centers`, `dim_accounts`, `fact_financial_transactions`, `fact_logistics_q3`).
4. **Agent 4 (Controlling Analytics Worker)**: Executes Price-Volume-Mix (PVM) variance decomposition and updates Q4 Estimate at Completion (EAC) forecasts.
5. **Agent 5 (Stakeholder Reporting Worker)**: Renders 3-tier financial reports, Power BI DAX libraries (`pvm_variance_measures.dax`), and Excel export models.
6. **Agent 0 (Office Meta-Builder)**: Listens on `/api/agent/enhance-ui` to dynamically inspect DOM structures, generate Tailwind CSS components, and inject live widgets.

---

## 🛡️ Mandatory Safety & Coding Guardrails

### 1. AST SQL Security Validation
* **All SQL queries executed against DuckDB MUST pass AST validation using `sqlglot`**.
* Only read-only `SELECT` statements are permitted.
* Disallow mutating clauses (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `TRUNCATE`).
* Example implementation rule:
  ```python
  import sqlglot

  def validate_sql_security(sql_query: str) -> bool:
      try:
          parsed = sqlglot.parse_one(sql_query)
          if not isinstance(parsed, sqlglot.exp.Select):
              return False
          sql_upper = sql_query.upper()
          for forbidden in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]:
              if f" {forbidden} " in f" {sql_upper} ":
                  return False
          return True
      except Exception:
          return False
  ```

### 2. Human-In-The-Loop (HITL) Gate Enforcement
* High-risk actions (*updating forecasts, enforcing vendor fuel caps, modifying thresholds*) **MUST** trigger an HITL pause (`AWAITING_HITL_APPROVAL`).
* State updates must persist to `STATE_STORE` or DuckDB (`controller_close_stages`) before advancing.

### 3. Matplotlib & Seaborn Visualization Rules
* **ALWAYS set headless backend before importing pyplot**:
  ```python
  import matplotlib
  matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  import seaborn as sns
  ```
* **NEVER call `plt.show()`** as it blocks the headless environment. Always save using `plt.savefig(path, dpi=150, bbox_inches='tight')` followed by `plt.close()`.
* Every chart title must state an insight with a verb and a number (*e.g., "Fuel Surcharges Drove $1.26M Overrun (+41.8%)"*).

---

## 📅 Monthly Close 5-Stage Cadence
When extending backend workflows or UI components, map tasks to the 5 close stages:
* **Stage 1 (Days -5..0)**: Pre-Close Cutoff & PO Reconciliation (`TH-01` cutoff threshold).
* **Stage 2 (Days 1..3)**: Month-End Close & GL Subledger Reconciliation (`TH-02` GL threshold).
* **Stage 3 (Days 3..5)**: Diagnostic PVM Variance Analysis (`TH-03` PVM materiality & `TH-04` fuel cap).
* **Stage 4 (Days 4..6)**: Forecast Update & Q4 EAC Mitigation Plan (`TH-05` EAC tolerance).
* **Stage 5 (Days 6..7)**: Executive Board Pack & Power BI Delivery.

---

## 📁 File Naming & Directory Structure
* FastAPI backend code: `server.py`
* Web Dashboard HTML template: `index.html` (or `index_dashboard_v4.html.txt`)
* DuckDB Seeder: `seed_data.py`
* Test Suits: `test_api-v3.sh`, `controller_office_eval_suite.py`
