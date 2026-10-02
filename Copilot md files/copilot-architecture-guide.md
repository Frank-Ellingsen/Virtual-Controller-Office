# Copilot Developer Architecture Guide — Virtual Controller Office

This guide explains how Copilot should assist developers when extending the **Agentic Virtual Controller Office**.

---

## 🏗️ System Components & Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WEB UI DASHBOARD (index.html)                       │
│    (Descriptive EDA + Monthly Close Stepper + HITL Gate + Meta-Builder)    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ REST API / WebSockets
                                   v
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND SERVER (server.py)                     │
│                                                                             │
│   ┌────────────────────────┐  ┌──────────────────────┐  ┌────────────────┐   │
│   │   LangGraph Router     │  │   HITL Checkpointer  │  │ AST Tool Sec.  │   │
│   │  (Agent 1 Supervisor)  │  │ (State Serializer)   │  │ (SQL Validator)│   │
│   └───────────┬────────────┘  └──────────┬───────────┘  └───────┬────────┘   │
│               │                          │                      │            │
│               ▼                          ▼                      ▼            │
│   ┌──────────────────────────────────────────────────────────────────────┐   │
│   │               AGENT 0: LIVE UI ENHANCER (Meta-Builder)               │   │
│   │     Endpoint: /api/agent/enhance-ui -> Injects Tailwind HTML DOM    │   │
│   └──────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                v
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ANALYTICS & EXECUTION LAYER                         │
│   ┌────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐   │
│   │ DuckDB Star-Schema │   │ Serper / Web APIs   │   │ OneDrive / Excel │   │
│   │ (Read-Only Driver) │   │ (External Research) │   │ (Financial Models)│   │
│   └────────────────────┘   └─────────────────────┘   └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 💡 Prompt Guidelines for Copilot Chat

When using Copilot Chat to build new features in this repository, reference these specific prompt patterns:

### 1. Adding a New FastAPI Endpoint
> *"Add a new FastAPI endpoint `/api/close/stage/summary` in `server.py` that queries `controller_close_stages` in `controller_office.duckdb` using safe read-only SQL validated by `sqlglot`."*

### 2. Creating a Seaborn Financial Plot
> *"Write a Python script using `pandas`, `seaborn`, and headless `matplotlib` to plot a waterfall variance bridge for Q3 freight costs. Save the figure to `/workspace/scratch/` with 150 DPI and `bbox_inches='tight'`."*

### 3. Modifying the Web Dashboard Stepper
> *"In `index.html`, add a new status badge to Stage 3 of the 5-stage monthly close stepper that displays the active DuckDB `dim_thresholds` limit (`TH-03` PVM Materiality > $50,000)."*

---

## 🧪 Testing & Validation Commands
* **Run DuckDB Database Seeder**: `python3 seed_data.py`
* **Run FastAPI API Test Suite**: `./test_api-v3.sh`
* **Run Multi-Step Trajectory Evaluator**: `python3 controller_office_eval_suite.py`
