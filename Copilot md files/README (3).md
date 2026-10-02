# 🏢 Agentic Virtual Controller Office — Master Project Index & Directory

Welcome to the **Agentic Virtual Controller Office**, an enterprise-grade multi-agent architecture built for financial controlling, variance analysis, automated audit logging, and supply chain diagnostics.

---

## 🛠️ Complete Project Artifact Registry (26 Deliverables)

Below is the structured inventory of all configuration manifests, backend code, evaluation harnesses, report artifacts, UI templates, and GitHub Copilot guides built for this project.

### 1. 🤖 GitHub Copilot Configuration & Prompt Guides
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`copilot-instructions.md`** | **GitHub Copilot Repository Rules**: Placed at `.github/copilot-instructions.md` to teach Copilot system architecture, AST SQL security rules, and headless rendering standards. | Studio Panel / `.github/` |
| **`copilot-architecture-guide.md`** | **Copilot Chat Architecture Reference**: System data flows, component relationships, and interactive chat prompt recipes. | Studio Panel |
| **`copilot-prompt-templates.md`** | **Copilot DAX & DuckDB Prompt Recipes**: Ready-to-use prompt templates for generating Price-Volume-Mix DAX measures, KPI status colors, and DuckDB analytical views. | Studio Panel |

---

### 2. 📋 Core Architecture & Agent Topology Manifests
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`GEMINI-v2.md`** | **Master Project Onboarding Guide**: Comprehensive handbook detailing the 6-agent hub-and-spoke topology, MCP protocols, security gates, and execution steps. | Studio Panel |
| **`GEMINI.md`** | **Google Antigravity System Instruction**: Context file loaded directly by Gemini CLI / Antigravity IDE at workspace initialization. | Studio Panel |
| **`AGENTS.md`** | **Hub-and-Spoke Topology Spec**: Defines Agent 1 (Supervisor), Agents 2–5 (Specialist Workers), and Agent 0 (Meta-Builder). | Studio Panel |
| **`TOOLS.md`** | **MCP Tool Manifest**: JSON schemas for DuckDB queries, Serper web search, Excel processing, and Power BI theme generators. | Studio Panel |
| **`HOOKS.md`** | **Security Hooks & Policy Spec**: Code-enforced AST SQL validators (`SELECT`-only) and Human-In-The-Loop (`HITL_Approval_Gate`) specifications. | Studio Panel |
| **`antigravity_controller_office_setup.zip`** | **Playbook & Skill Bundle**: Zip file containing all 8 specialist skill playbooks (`01-audit-scope-decomposition.md` to `08-powerbi-excel-engineering.md`). | Studio Panel |

---

### 3. ⚡ Backend Engine & Web UI Interface
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`index_dashboard_v4.html.txt`** | **Full Dashboard UI (v4)**: Web application featuring Section 1 EDA module, 5-stage close stepper, manual approval gates, and Agent 0 directive bar. | Studio Panel |
| **`WEB_UI_AND_BACKEND-v5.md`** | **FastAPI Backend Spec (v5)**: Complete `server.py` specification with DuckDB `dim_thresholds` evaluator, stage approval persistence, and Agent 0 UI enhancer endpoints. | Studio Panel |
| **`test_api-v3.sh`** | **API Integration Test Harness**: Shell script testing `/api/health`, `/api/close/stages`, `/api/agent/enhance-ui`, and threshold evaluation endpoints. | Studio Panel |
| **`deploy.sh`** | **Docker Container Deployment Script**: Automated bash launcher building the Docker image and provisioning persistent DuckDB volumes. | Studio Panel |

---

### 4. 📊 Data Layer, Exploratory Data Analysis & Analytics
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`seed_data.py`** | **DuckDB Analytical Database Seeder**: Generates star-schema tables (`fact_logistics_q3`, `fact_financial_transactions`, `dim_thresholds`) in `controller_office.duckdb`. | Studio Panel |
| **`eda_outliers_boxplot.png`** | **Carrier Outlier Boxplot**: Seaborn visualization identifying carrier rate overrun spikes up to $12K per shipment. | Studio Panel |
| **`eda_correlation_heatmap.png`** | **Variance Correlation Matrix**: Heatmap proving actual fuel surcharges drive net variance ($r = +0.88$). | Studio Panel |
| **`eda_value_counts_barplots.png`** | **Categorical Distribution Barplots**: Value counts across active logistics carriers and departmental overruns. | Studio Panel |
| **`eda_pairplot_logistics.png`** | **Multivariate Feature Pairplot**: Pairwise relationships with diagonal KDE curves for volume and surcharge variables. | Studio Panel |
| **`q3_diagnostic_variance_report-v2.md`** | **Mitigated Audit Report**: Price-Volume-Mix analysis reflecting approved **Priority Action P1** ($354,000 Q4 savings). | Studio Panel |

---

### 5. 📈 Power BI Assets & DAX Modeling
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`theme.json`** | **Power BI Custom Dark Theme**: JSON color palette matching the Virtual Web UI dashboard. | Studio Panel |
| **`pvm_variance_measures.dax`** | **Power BI DAX Measure Library**: Production DAX code for PVM variance decomposition, fuel surcharge overruns, and status color formatting. | Studio Panel |

---

### 6. 🧪 Evaluation Framework & CI/CD Testing
| Filename | Description / Purpose | Location / Access |
| :--- | :--- | :--- |
| **`planning_eval_rubric.md`** | **5-Axis Planning Rubric Specification**: 100-point rubric assessing Control Gate Calibration, Step Efficiency, Safety, and Deliberation Economics. | Studio Panel |
| **`controller_office_eval_suite.py`** | **Executable Benchmark Harness**: Python evaluation engine scoring multi-step agent execution trajectories. | Studio Panel |
| **`monthly_close_5stage_eval_report.md`** | **5-Stage Close Benchmark (100/100 Score)**: Evaluation report documenting ideal planning robustness across the 5-stage monthly close cycle. | Studio Panel |
| **`eval.yml`** | **GitHub Actions CI/CD Pipeline**: Automated workflow running DuckDB seeding, AST security checks, and trajectory evaluation on every PR. | Studio Panel |

---

## 🚀 Quick-Start Execution Guide

1. **Set Up GitHub Copilot Instructions**:
   ```bash
   mkdir -p .github && cp copilot-instructions.md .github/copilot-instructions.md
   ```
2. **Seed Local Analytics Database**:
   ```bash
   python3 seed_data.py
   ```
3. **Launch Local Server via Docker**:
   ```bash
   chmod +x deploy.sh && ./deploy.sh
   ```
4. **Run 5-Stage Monthly Close Evaluation Suite**:
   ```bash
   python3 controller_office_eval_suite.py
   ```
5. **Execute Backend Integration Tests**:
   ```bash
   chmod +x test_api-v3.sh && ./test_api-v3.sh
   ```
