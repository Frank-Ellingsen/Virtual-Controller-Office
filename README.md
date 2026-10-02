# 🏢 Agentic Virtual Controller Office — Master Project Index & Directory

Welcome to the **Agentic Virtual Controller Office**, an enterprise-grade multi-agent architecture built for financial controlling, variance analysis, automated audit logging, and supply chain diagnostics.

---

## 🛠️ Complete Project Artifact Registry (25 Deliverables)

Below is the structured inventory of all configuration manifests, backend code, evaluation harnesses, report artifacts, and UI templates built for this project.

### 1. 📋 Core Architecture & Agent Topology Manifests

| Filename                                      | Description / Purpose                                                                                                                                         | Location / Access |
| :-------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------ | :---------------- |
| **`GEMINI-v2.md`**                            | **Master Project Onboarding Guide**: Comprehensive handbook detailing the 6-agent hub-and-spoke topology, MCP protocols, security gates, and execution steps. | Studio Panel      |
| **`GEMINI.md`**                               | **Google Antigravity System Instruction**: Context file loaded directly by Gemini CLI / Antigravity IDE at workspace initialization.                          | Studio Panel      |
| **`AGENTS.md`**                               | **Hub-and-Spoke Topology Spec**: Defines Agent 1 (Supervisor), Agents 2–5 (Specialist Workers), and Agent 0 (Meta-Builder).                                   | Studio Panel      |
| **`TOOLS.md`**                                | **MCP Tool Manifest**: JSON schemas for DuckDB queries, Serper web search, Excel processing, and Power BI theme generators.                                   | Studio Panel      |
| **`HOOKS.md`**                                | **Security Hooks & Policy Spec**: Code-enforced AST SQL validators (`SELECT`-only) and Human-In-The-Loop (`HITL_Approval_Gate`) specifications.               | Studio Panel      |
| **`antigravity_controller_office_setup.zip`** | **Playbook & Skill Bundle**: Zip file containing all 8 specialist skill playbooks (`01-audit-scope-decomposition.md` to `08-powerbi-excel-engineering.md`).   | Studio Panel      |

---

### 2. ⚡ Backend Engine & Web UI Interface

| Filename                            | Description / Purpose                                                                                                                                                                   | Location / Access      |
| :---------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------- |
| **`docs/WEB_UI_AND_BACKEND-v5.md`** | **Full-Stack Spec v5 (Dynamic Threshold Reader)**: FastAPI server (`server.py`) featuring `dim_thresholds` evaluation, `/api/thresholds`, API Provider config, and Agent 0 UI Enhancer. | Studio Panel / `docs/` |
| **`WEB_UI_AND_BACKEND-v3.md`**      | **Full-Stack Spec v3 (Agent 0 Meta-UI Builder)**: Complete Python FastAPI server (`server.py`) and interactive dashboard (`index.html`).                                                | Root                   |
| **`scripts/test_api-v3.sh`**        | **5-Stage API Integration Test Harness**: `curl` shell script testing health, HITL gates, 5-stage close approvals, threshold evaluation, and Serper research.                           | `scripts/`             |
| **`scripts/deploy.sh`**             | **Docker Container Deployment Script**: Automated bash launcher building the Docker image, provisioning persistent volumes, and running `docker-compose`.                               | `scripts/`             |

---

### 3. 📊 Data Layer, Database Seeder & Analytics

| Filename                                          | Description / Purpose                                                                                                                                           | Location / Access |
| :------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------- |
| **`seed_data.py`**                                | **DuckDB Analytical Database Seeder**: Generates star-schema tables (`fact_logistics_q3`, `dim_thresholds`) and analytical views in `controller_office.duckdb`. | Root              |
| **`reports/monthly_close_5stage_eval_report.md`** | **5-Stage Close Benchmark Report**: Benchmark results for TC-05 simulation achieving a 100/100 score.                                                           | `reports/`        |
| **`reports/q3_diagnostic_variance_report-v2.md`** | **Mitigated Audit Report**: Updated report reflecting approved **Priority Action P1** (contractual fuel caps enforced, saving $354,000 in Q4).                  | `reports/`        |

---

### 4. 📈 Power BI BI Assets & DAX Modeling

| Filename                        | Description / Purpose                                                                                                                                              | Location / Access |
| :------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------- |
| **`theme.json`**                | **Power BI Custom Dark Theme**: JSON color palette matching the Virtual Web UI dashboard (Slate/Indigo/Emerald/Amber/Rose).                                        | `bi/`             |
| **`pvm_variance_measures.dax`** | **Power BI DAX Measure Library**: Production DAX code for PVM variance decomposition, fuel surcharge overruns, YTD logic, and dynamic KPI status color formatting. | `bi/`             |

---

### 5. 🧪 Evaluation Framework & CI/CD Testing

| Filename                                      | Description / Purpose                                                                                                                                                        | Location / Access    |
| :-------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------- |
| **`docs/planning_eval_rubric.md`**            | **5-Axis Planning Rubric Specification**: Detailed 100-point rubric assessing Control Gate Calibration, Step Efficiency, Safety, Error Recovery, and Deliberation Economics. | `docs/`              |
| **`controller_office_eval_suite.py`**         | **Executable Benchmark Harness**: Python evaluation engine scoring multi-step agent execution trajectories across complex controlling test cases.                            | Root                 |
| **`reports/evaluation_benchmark_results.md`** | **Benchmark Report (98.25/100 Score)**: Comprehensive evaluation results across 4 complex audit scenarios.                                                                   | `reports/`           |
| **`eval.yml`**                                | **GitHub Actions CI/CD Pipeline**: Automated workflow running DuckDB seeding, AST security checks, and trajectory evaluation on every PR/push.                               | `.github/workflows/` |

---

### 6. 🗺️ Studio Visual Apps & Mindmaps

- **`Agent Mindmap`**: Visual overview of AI agent system design.
- **`Dashboard Mindmap`**: Design taxonomy for executive and operational dashboards.
- **`Storytelling Mindmap`**: Quantitative data storytelling frameworks.
- **`Chart Taxonomy`**: Guide to selecting optimal chart types for business data.
- **`Data Mindmap`**: Analytics engineering, data modeling, and reporting structures.
- **`Agentic Map`**: Ecosystem map for agentic RAG and autonomous systems.

---

## 🚀 Quick-Start Execution Guide

1. **Seed Local Analytics Database**:
   ```bash
   python3 seed_data.py
   ```
2. **Launch Local Server via Docker**:
   ```bash
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```
3. **Run Multi-Step Agent Evaluation Suite**:
   ```bash
   python3 controller_office_eval_suite.py
   ```
4. **Test Backend API & 5-Stage Close Endpoints**:
   ```bash
   chmod +x scripts/test_api-v3.sh
   ./scripts/test_api-v3.sh
   ```

## GitHub Pages / Browser Mode

The static dashboard can be opened directly from [GitHub Pages](https://frank-ellingsen.github.io/Virtual-Controller-Office/). Select **Premier League & Sports Analytics**, upload `Local Data/Sports/premier_league_games.xlsx`, and the dashboard calculates match counts, home-win rate, goals per match, and season-level results in the browser. Uploaded rows and results persist in that browser profile.

GitHub Pages does not run the FastAPI/DuckDB backend. In browser mode, uploads are not sent to a shared database and the audit/HITL trajectory is a local demo flow; deploy the API separately if you need shared storage or server-backed agent execution.
