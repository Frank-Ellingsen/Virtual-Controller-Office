# 🏢 Agentic Virtual Controller Office — Master Project Index & Directory

Welcome to the **Agentic Virtual Controller Office**, an enterprise-grade multi-agent architecture built for financial controlling, variance analysis, automated audit logging, and supply chain diagnostics.

---

## 🛠️ Complete Project Artifact Registry (25 Deliverables)

Below is the structured inventory of all configuration manifests, backend code, evaluation harnesses, report artifacts, and UI templates built for this project.

### 1. 📋 Core Architecture & Agent Topology Manifests
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`GEMINI-v2.md`** | **Master Project Onboarding Guide**: Comprehensive handbook detailing the 6-agent hub-and-spoke topology, MCP protocols, security gates, and execution steps. | Studio Panel |
| **`GEMINI.md`** | **Google Antigravity System Instruction**: Context file loaded directly by Gemini CLI / Antigravity IDE at workspace initialization. | Studio Panel |
| **`AGENTS.md`** | **Hub-and-Spoke Topology Spec**: Defines Agent 1 (Supervisor), Agents 2–5 (Specialist Workers), and Agent 0 (Meta-Builder). | Studio Panel |
| **`TOOLS.md`** | **MCP Tool Manifest**: JSON schemas for DuckDB queries, Serper web search, Excel processing, and Power BI theme generators. | Studio Panel |
| **`HOOKS.md`** | **Security Hooks & Policy Spec**: Code-enforced AST SQL validators (`SELECT`-only) and Human-In-The-Loop (`HITL_Approval_Gate`) specifications. | Studio Panel |
| **`antigravity_controller_office_setup.zip`** | **Playbook & Skill Bundle**: Zip file containing all 8 specialist skill playbooks (`01-audit-scope-decomposition.md` to `08-powerbi-excel-engineering.md`). | Studio Panel |

---

### 2. ⚡ Backend Engine & Web UI Interface
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`WEB_UI_AND_BACKEND-v3.md`** | **Full-Stack Spec v3 (Agent 0 Meta-UI Builder)**: Complete Python FastAPI server (`server.py`) featuring `/api/agent/enhance-ui`, dynamic HTML DOM component injection, AST SQL security, and interactive dashboard (`index.html`). | Studio Panel |
| **`WEB_UI_AND_BACKEND-v2.md`** | **Full-Stack Spec v2 (Hybrid Serper Research)**: Includes Serper web benchmarking API integration and offline DuckDB fallback mode. | Studio Panel |
| **`WEB_UI_AND_BACKEND.md`** | **Initial Backend Architecture Spec**: Original baseline version of the FastAPI and Web UI specifications. | Studio Panel |
| **`test_api-v2.sh`** | **Extended API Test Suite**: `curl` test harness covering `/api/health`, `/api/audit/request`, `/api/audit/hitl/respond`, `/api/research/serper`, and `/api/agent/enhance-ui`. | Studio Panel |
| **`test_api.sh`** | **Initial API Test Harness**: Baseline `curl` integration testing script for core REST endpoints. | Studio Panel |
| **`deploy.sh`** | **Docker Container Deployment Script**: Automated bash launcher building the Docker image, provisioning persistent volumes, and running `docker-compose`. | Studio Panel |

---

### 3. 📊 Data Layer, Database Seeder & Analytics
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`seed_data.py`** | **DuckDB Analytical Database Seeder**: Generates star-schema tables (`fact_logistics_q3`, `fact_financial_transactions`) and analytical views in `controller_office.duckdb`. | Studio Panel |
| **`q3_diagnostic_variance_report.md`** | **Initial Audit Report**: Diagnostic Price-Volume-Mix (PVM) analysis of the $1.26M Q3 European logistics cost overrun. | Studio Panel |
| **`q3_diagnostic_variance_report-v2.md`** | **Mitigated Audit Report**: Updated report reflecting approved **Priority Action P1** (contractual fuel caps enforced, saving $354,000 in Q4). | Studio Panel |

---

### 4. 📈 Power BI BI Assets & DAX Modeling
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`theme.json`** | **Power BI Custom Dark Theme**: JSON color palette matching the Virtual Web UI dashboard (Slate/Indigo/Emerald/Amber/Rose). | Studio Panel |
| **`pvm_variance_measures.dax`** | **Power BI DAX Measure Library**: Production DAX code for PVM variance decomposition, fuel surcharge overruns, YTD logic, and dynamic KPI status color formatting. | Studio Panel |

---

### 5. 🧪 Evaluation Framework & CI/CD Testing
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`planning_eval_rubric.md`** | **5-Axis Planning Rubric Specification**: Detailed 100-point rubric assessing Control Gate Calibration, Step Efficiency, Safety, Error Recovery, and Deliberation Economics. | Studio Panel |
| **`controller_office_eval_suite.py`** | **Executable Benchmark Harness**: Python evaluation engine scoring multi-step agent execution trajectories across complex controlling test cases. | Studio Panel |
| **`evaluation_benchmark_results.md`** | **Benchmark Report (98.25/100 Score)**: Comprehensive evaluation results across 4 complex audit scenarios. | Studio Panel |
| **`eval.yml`** | **GitHub Actions CI/CD Pipeline**: Automated workflow running DuckDB seeding, AST security checks, and trajectory evaluation on every PR/push. | Studio Panel |

---

### 6. 🗺️ Studio Visual Apps & Mindmaps
* **`Agent Mindmap`**: Visual overview of AI agent system design.
* **`Dashboard Mindmap`**: Design taxonomy for executive and operational dashboards.
* **`Storytelling Mindmap`**: Quantitative data storytelling frameworks.
* **`Chart Taxonomy`**: Guide to selecting optimal chart types for business data.
* **`Data Mindmap`**: Analytics engineering, data modeling, and reporting structures.
* **`Agentic Map`**: Ecosystem map for agentic RAG and autonomous systems.

---

## 🚀 Quick-Start Execution Guide

1. **Seed Local Analytics Database**:
   ```bash
   python3 seed_data.py
   ```
2. **Launch Local Server via Docker**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
3. **Run Multi-Step Agent Evaluation Suite**:
   ```bash
   python3 controller_office_eval_suite.py
   ```
4. **Test Backend API Endpoints (with Agent 0 UI Enhancer)**:
   ```bash
   chmod +x test_api-v2.sh
   ./test_api-v2.sh
   ```
