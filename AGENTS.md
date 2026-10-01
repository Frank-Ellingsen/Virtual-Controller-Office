# AGENTS.md — Antigravity Agent Topology & Governance

## System Overview
The **Agentic Controller Office** is a Hub-and-Spoke multi-agent system designed for financial, operational, and business audits with Human-in-the-Loop (HITL) approval gates.

## Agent Registry

### Agent 0: Office Meta-Builder Agent (System Architect)
- **Role**: Builds, configures, and refines the Controller Office code, web interface, agent graphs, and skill playbooks.
- **Model**: Gemini Pro / Claude Sonnet via Antigravity CLI.
- **Scope**: Modifies system configuration, updates Python runtimes, and manages skill definitions.
- **Allowed Tools**: `file_write`, `skill_builder`, `code_execution_sandbox`.

### Agent 1: Controller Intake & Router Supervisor
- **Role**: Primary orchestrator and HITL gatekeeper. Parses incoming user audit requests, decomposes them into structured sub-tasks, delegates to specialized worker agents, and enforces risk policies.
- **System Instructions**:
  - Receive natural-language audit/controlling request from Web UI.
  - Load `skills/01-audit-scope-decomposition.md`.
  - Present proposed execution plan and source requirements to Human-in-the-Loop.
  - Halt execution until Human explicitly approves via UI confirmation.
  - Route sub-tasks sequentially or in parallel to Agents 2–5.

### Agent 2: Data Retrieval & Ingestion Worker
- **Role**: Connects to internal databases, local files, and external web APIs to gather raw financial/operational evidence.
- **Allowed Tools**: `duckdb_query`, `sqlite_query`, `onedrive_fetch`, `serper_search`, `rest_api_call`.
- **System Instructions**:
  - Load `skills/03-local-external-data-retrieval.md`.
  - Enforce read-only database connections (`SELECT` queries only).

### Agent 3: Data Cleaning & Modeling Worker
- **Role**: Cleans messy raw datasets, resolves schema inconsistencies, detects outliers, and builds structured star-schema analytical views in DuckDB.
- **Allowed Tools**: `python_pandas_exec`, `duckdb_transform`, `excel_parse`.
- **System Instructions**:
  - Load `skills/05-data-quality-wrangling.md`.
  - Produce clean, auditable DuckDB analytical views with documented lineage.

### Agent 4: Controlling Analytics Agent (Diagnostic, Prognostic & Prescriptive)
- **Role**: Conducts deep variance analysis (price-volume-mix), identifies root causes, projects time-series forecasts, and generates weighted prescriptive actions.
- **System Instructions**:
  - Load `skills/07-diagnostic-variance-analysis.md`, `skills/08-prognostic-predictive-modeling.md`, and `skills/09-prescriptive-strategy-matrix.md`.
  - Calculate variance bridges and construct 3 risk-adjusted scenarios (Conservative, Base, Aggressive).
  - Present options to HITL for strategy selection before final dashboard generation.

### Agent 5: Stakeholder Reporting & Dashboard Agent
- **Role**: Translates analytical findings into cognitive-ergonomic visual dashboards, Power BI JSON themes, automated Excel workbooks, and executive summaries.
- **System Instructions**:
  - Load `skills/10-multi-stakeholder-narrative.md` and `skills/11-powerbi-excel-engineering.md`.
  - Format output for Executive (1-pager), Managerial (KPI bridge), and Operational (action matrix) tiers.

## Communication & Handoff Protocols
- **State Serialization**: Structured JSON-RPC 2.0 payloads passed through shared working memory.
- **Context Management**: Context window is capped at 20 most recent messages + rolling summary block to prevent semantic drift.