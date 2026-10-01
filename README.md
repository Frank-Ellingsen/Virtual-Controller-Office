# 🏢 Agentic Virtual Controller Office

An enterprise-grade, multi-agent financial controlling architecture built for **Project Controllers**, **Financial Analysts**, and **BI Specialists**. The system automates variance analysis (Price-Volume-Mix decomposition), enforces Human-in-the-Loop (HITL) approval gates, and provides real-time audit traceability with local-first SQL engines (DuckDB/SQLite).

---

## 🗂️ Project Directory Structure

```text
Virtual Controller Office/
├── .github/
│   └── workflows/
│       └── eval.yml                  # GitHub Actions CI/CD planning evaluation pipeline
├── bi/
│   ├── theme.json                    # Power BI custom dark theme (Slate/Indigo/Emerald)
│   └── pvm_variance_measures.dax     # Power BI DAX library for PVM variance analysis
├── data/                             # DuckDB database volume (gitignored)
│   └── .gitkeep
├── docs/                             # Architecture specifications & rubrics
│   ├── GEMINI-v2.md                  # Comprehensive system handbook & onboarding guide
│   ├── planning_eval_rubric.md       # 100-Point 5-axis planning evaluation rubric
│   ├── WEB_UI_AND_BACKEND-v2.md      # Full-stack API & UI architecture specification
│   └── archive/                      # Historical / v1 architecture specs
├── logs/                             # Audit & execution logs (gitignored)
│   └── .gitkeep
├── reports/                          # Audit reports & benchmark deliverables
│   ├── evaluation_benchmark_results.md # Trajectory robustness benchmark (98.25/100)
│   └── q3_diagnostic_variance_report-v2.md # Mitigated Q3 audit report & P1 fuel cap
├── scripts/                          # Deployment & testing utilities
│   ├── deploy.sh                     # Docker deployment bash script
│   ├── test_api.ps1                  # Windows PowerShell API test harness
│   └── test_api.sh                   # Linux/macOS curl API test script
├── skills/                           # Specialist agent playbooks (01–08)
│   ├── 01-audit-scope-decomposition.md
│   ├── 02-hitl-risk-evaluation.md
│   ├── 03-data-quality-wrangling.md
│   ├── 04-diagnostic-variance-analysis.md
│   ├── 05-prognostic-predictive-modeling.md
│   ├── 06-prescriptive-strategy-matrix.md
│   ├── 07-multi-stakeholder-narrative.md
│   └── 08-powerbi-excel-engineering.md
├── web/
│   └── index.html                    # Frontend dashboard template (Tailwind CSS)
├── .env.example                      # Sanitized environment configuration template
├── .gitignore                        # Comprehensive Python / DuckDB / secret exclusions
├── AGENTS.md                         # Hub-and-Spoke agent topology manifest (Agents 0–5)
├── controller_office_eval_suite.py   # Executable multi-step agent planning test runner
├── docker-compose.yml                # Docker Compose multi-service definition
├── Dockerfile                        # Container build definition
├── GEMINI.md                         # Antigravity IDE system instructions
├── HOOKS.md                          # AST SQL security & HITL gate specifications
├── index.html                        # Real-time Web UI dashboard
├── README.md                         # Master documentation & directory index
├── requirements.txt                  # Python production runtime dependencies
├── seed_data.py                      # DuckDB star-schema seeder & view creator
├── server.py                         # FastAPI backend with AST security & HITL endpoints
└── TOOLS.md                          # MCP tool schemas (DuckDB, Serper, Excel, Power BI)
```

---

## 🤖 Hub-and-Spoke Agent Topology

| Agent ID | Agent Role | Core Responsibility | Key Tools / Skills |
| :--- | :--- | :--- | :--- |
| **Agent 0** | **Office Meta-Builder** | Codebase maintenance, runtime tuning, skill playbook updates. | File operations, skill builder, sandbox. |
| **Agent 1** | **Controller Intake Supervisor** | Parses user audit requests, decomposes sub-goals, enforces HITL gates. | `01-audit-scope-decomposition.md`, `02-hitl-risk-evaluation.md` |
| **Agent 2** | **Data Retrieval & Ingestion** | Connects to DuckDB, SQLite, OneDrive, and Serper web benchmarks. | Read-only SQL queries, hybrid Serper API. |
| **Agent 3** | **Data Cleaning & Modeling** | Resolves schema inconsistencies, sanitizes nulls, builds star schemas. | `03-data-quality-wrangling.md`, DuckDB transforms. |
| **Agent 4** | **Controlling Analytics** | Computes Price-Volume-Mix (PVM) variance, forecasts EAC/ETC. | `04-diagnostic-variance-analysis.md`, PVM models. |
| **Agent 5** | **Reporting & BI Specialist** | Produces cognitive-ergonomic dashboards, DAX measures, executive memos. | `07-multi-stakeholder-narrative.md`, `theme.json`, DAX. |

---

## 🚀 Quick-Start Execution Guide

### 1. Environment Setup
Clone the repository and install the dependencies:

```bash
# Optional: create a virtual environment
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure your API keys:
```bash
cp .env.example .env
```

### 2. Seed the Local DuckDB Database
Populate the local star schema (`data/controller_office.duckdb`) with Q3 logistics records and financial transactions:

```bash
python seed_data.py
```

### 3. Launch the FastAPI Backend & Web Dashboard
Start the local server:

```bash
python server.py
# Or with uvicorn directly
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

- **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/) or [http://localhost:8000/index.html](http://localhost:8000/index.html)
- **API Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 4. Run the Planning Evaluation Suite
Verify multi-step trajectory quality and AST security gates:

```bash
python controller_office_eval_suite.py
```

### 5. Run API Integration Tests
**Windows PowerShell**:
```powershell
.\scripts\test_api.ps1
```

**Linux / macOS / Bash**:
```bash
chmod +x scripts/test_api.sh
./scripts/test_api.sh
```

---

## 🛡️ Security, Governance & AST Validation

- **Read-Only SQL Enforcement**: `validate_sql_security` inspects all incoming queries using AST parsing (`sqlglot`/`sqlparse`), strictly disallowing mutating statements (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `TRUNCATE`).
- **Human-in-the-Loop (HITL) Gatekeeper**: High-risk operations (such as budget reallocations or external research executions) halt the supervisor pipeline until explicit confirmation is provided via the Web UI or API.
- **Credential Protection**: Real API keys (`GEMINI_API_KEY`, `SERPER_API_KEY`) and local databases (`*.duckdb`, `*.sqlite`) are gitignored by design.
