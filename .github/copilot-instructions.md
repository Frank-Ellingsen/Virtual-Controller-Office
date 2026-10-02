# GitHub Copilot Custom Instructions — Agentic Virtual Controller Office

These instructions provide project-level context, architecture rules, code conventions, and safety guardrails for GitHub Copilot when working in this repository.

---

## Project Overview

The Virtual Controller Office combines a FastAPI backend, DuckDB data ingestion/query services, and an HTML/JavaScript dashboard for controlling and audit workflows.

### Tech Stack
- **Backend:** Python, FastAPI, Uvicorn, Pydantic v2 (`server.py`)
- **Data:** DuckDB, Pandas; Excel ingestion via `openpyxl`/`xlrd`
- **SQL validation:** `sqlglot`, with a `sqlparse` fallback in the current backend
- **Frontend:** HTML, Tailwind CSS, vanilla JavaScript, SheetJS (`index.html`)
- **Tests:** pytest (`tests/`)
- **External research:** optional Serper REST API

## Multi-Agent Roles

Maintain the project’s hub-and-spoke role model when extending workflows:

1. **Agent 1 — Supervisor/Router:** scopes requests, prepares plans, and enforces human approval gates.
2. **Agent 2 — Data Retrieval:** retrieves local data and approved external research.
3. **Agent 3 — Data Modeling:** validates, cleans, and documents data transformations.
4. **Agent 4 — Controlling Analytics:** performs variance analysis and forecasting.
5. **Agent 5 — Reporting:** prepares stakeholder-facing summaries, dashboards, and BI outputs.
6. **Agent 0 — Meta-Builder:** handles dashboard/UI enhancements.

Treat these as architectural roles and intended workflow responsibilities. Verify implementation in `server.py` before claiming a workflow is backed by a live agent runtime.

## Mandatory Safety and Coding Guardrails

### SQL and Data Access
- Keep database reads read-only wherever the task only requires inspection or analytics.
- All SQL submitted through the query API must pass the existing read-only validation path in `server.py`; do not weaken or bypass it.
- Validate generated SQL as a single read-only `SELECT`. Reject mutating statements and multi-statement payloads.
- Use parameterized values for user-supplied data. Do not interpolate untrusted values into SQL identifiers or expressions.
- Check the actual DuckDB schema before using table or column names; names in docs and prompt templates may be examples.

### Human Approval
- High-risk or state-changing operations must pause for explicit human approval before execution.
- Keep approval decisions and resulting state changes auditable. Do not describe a simulated browser-mode response as a real backend execution.

### Python and Tests
- Follow `requirements.txt` and existing project patterns when changing dependencies.
- Add or update pytest coverage for backend behavior and run relevant tests after code changes.
- Keep data-processing steps reproducible and document lineage where practical.

### Plots
- For headless Matplotlib work, select the `Agg` backend before importing `pyplot`; save figures and close them instead of calling `plt.show()`.
- Titles should communicate the finding, not merely name the chart.

## Repository-Specific Conventions

- `server.py` is the FastAPI API entry point; `scripts/file_processor.py` handles business discovery and ingestion.
- `index.html` is the primary dashboard served by FastAPI. Keep `web/index.html` synchronized with it when changing the UI.
- The dashboard can also run as a static page. On GitHub Pages, uploads/results use browser-local storage; there is no FastAPI/DuckDB service hosted by GitHub Pages.
- Browser-mode HITL/trajectory behavior is a local demo flow. Confirm the active backend path before describing data as shared or server-persisted.
- `tests/` contains the pytest suite. `scripts/` contains utility and integration scripts.
- `.env` is ignored by Git. Never commit real API keys or credentials.

## Monthly Close Design Reference

The documented 5-stage cadence is a design reference for close workflows:
1. Pre-close cutoff and PO reconciliation.
2. Month-end close and GL reconciliation.
3. Diagnostic PVM variance analysis.
4. Forecast/EAC update and mitigation planning.
5. Executive reporting and BI delivery.

Threshold names such as `TH-01` through `TH-05` and close-stage tables must be verified against the current database and API before use; documentation examples do not guarantee those objects exist in the active runtime.
