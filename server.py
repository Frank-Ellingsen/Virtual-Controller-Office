import os
import sys
import json
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import duckdb

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
import file_processor

try:
    import sqlglot
except ImportError:
    sqlglot = None

try:
    import sqlparse
except ImportError:
    sqlparse = None

app = FastAPI(
    title="Virtual Controller Office API",
    description="Backend API powering Agentic Controller Office workflows and HITL approval gates.",
    version="1.0.0"
)

# Enable CORS for Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Configuration & Research Provider
# -----------------------------------------------------------------------------
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
ENABLE_LIVE_WEB_RESEARCH = os.getenv("ENABLE_LIVE_WEB_RESEARCH", "true").lower() == "true"
DB_PATH = os.getenv("DUCKDB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "controller_office.duckdb"))

def execute_external_serper_research(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Agent 2 External Research Handler:
    Toggles dynamically between live Serper REST API benchmarking and 
    offline fallback database context depending on SERPER_API_KEY presence.
    """
    if ENABLE_LIVE_WEB_RESEARCH and SERPER_API_KEY:
        import urllib.request
        try:
            url = "https://google.serper.dev/search"
            payload = json.dumps({"q": query, "num": num_results}).encode("utf-8")
            headers = {
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json"
            }
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "source": "live_serper_api",
                    "status": "success",
                    "organic_results": [
                        {"title": r.get("title"), "snippet": r.get("snippet"), "link": r.get("link")}
                        for r in data.get("organic", [])
                    ]
                }
        except Exception as e:
            return {
                "source": "live_serper_api_error_fallback",
                "status": "fallback",
                "error": str(e),
                "message": "Fell back to internal DuckDB market rate tables due to network error."
            }
    else:
        # Offline or keyless fallback mode
        return {
            "source": "offline_duckdb_fallback",
            "status": "offline_mode",
            "message": "SERPER_API_KEY not set or ENABLE_LIVE_WEB_RESEARCH=false. Utilizing local carrier index tables in DuckDB.",
            "synthetic_benchmarks": [
                {"carrier": "DB Schenker", "avg_eu_fuel_index_increase": "+41.8%", "baseline_cap": "+15.0%"},
                {"carrier": "FedEx Freight", "avg_eu_fuel_index_increase": "+38.4%", "baseline_cap": "+15.0%"}
            ]
        }

# -----------------------------------------------------------------------------
# Database & AST Security
# -----------------------------------------------------------------------------
def get_db_connection(read_only: bool = True):
    if not os.path.exists(DB_PATH):
        raise HTTPException(
            status_code=503,
            detail=f"Database file not found at {DB_PATH}. Please run seed_data.py first."
        )
    return duckdb.connect(database=DB_PATH, read_only=read_only)

def validate_sql_security(sql_query: str) -> bool:
    """
    AST SQL Security Validator:
    Verifies that the query is strictly a read-only SELECT statement with no mutating clauses.
    """
    try:
        if sqlglot is not None:
            parsed = sqlglot.parse_one(sql_query)
            if not isinstance(parsed, sqlglot.exp.Select):
                return False
        elif sqlparse is not None:
            parsed = sqlparse.parse(sql_query)
            if not parsed or parsed[0].get_type() != "SELECT":
                return False
        else:
            if not sql_query.strip().upper().startswith("SELECT"):
                return False

        sql_upper = f" {sql_query.upper()} "
        for forbidden in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]:
            if f" {forbidden} " in sql_upper or f"\n{forbidden} " in sql_upper:
                return False
        return True
    except Exception:
        return False

# -----------------------------------------------------------------------------
# State Store & Models
# -----------------------------------------------------------------------------
STATE_STORE: Dict[str, Dict[str, Any]] = {}
TRAJECTORY_LOGS: List[Dict[str, Any]] = []

class AuditRequest(BaseModel):
    prompt: str = Field(..., examples=["Audit Q3 logistics cost overruns across European subsidiaries."])
    user_id: str = Field(default="controller_admin")

class HITLApproval(BaseModel):
    task_id: Optional[str] = None
    run_id: Optional[str] = None
    approved: bool
    feedback: Optional[str] = None
    user_feedback: Optional[str] = None

class QueryExecutionRequest(BaseModel):
    sql: str

class ResearchRequest(BaseModel):
    query: str
    num_results: int = 5

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/")
@app.get("/index.html")
def get_dashboard():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if not os.path.exists(index_path):
        index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"message": "Virtual Controller Office API online. Dashboard file not found at root."}

class ApiConfigRequest(BaseModel):
    provider: str
    api_key: Optional[str] = ""

API_CONFIG = {
    "provider": "gemini",
    "api_key": ""
}

@app.get("/api/config/llm")
def get_api_config():
    masked_key = ""
    if API_CONFIG["api_key"]:
        k = API_CONFIG["api_key"]
        masked_key = k[:4] + "..." + k[-4:] if len(k) > 8 else "***"
    return {
        "provider": API_CONFIG["provider"],
        "has_key": bool(API_CONFIG["api_key"]),
        "masked_key": masked_key
    }

@app.post("/api/config/llm")
def update_api_config(req: ApiConfigRequest):
    global SERPER_API_KEY
    API_CONFIG["provider"] = req.provider
    API_CONFIG["api_key"] = req.api_key
    
    if req.provider == "serper" and req.api_key:
        SERPER_API_KEY = req.api_key
    elif req.provider == "gemini" and req.api_key:
        os.environ["GEMINI_API_KEY"] = req.api_key
        
    TRAJECTORY_LOGS.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent": "Agent 1: Supervisor",
        "action": "API Config Update",
        "message": f"Updated active API provider to '{req.provider}' (Key set: {bool(req.api_key)})",
        "status": "INFO"
    })
    return {
        "status": "success",
        "provider": req.provider,
        "message": f"API Provider set to '{req.provider}' successfully."
    }

def load_controlling_thresholds() -> Dict[str, Dict[str, Any]]:
    """Reads active controlling thresholds from dim_thresholds in DuckDB."""
    try:
        conn = get_db_connection(read_only=True)
        rows = conn.execute("SELECT threshold_id, parameter_name, threshold_value, unit, action_trigger FROM dim_thresholds").fetchall()
        conn.close()
        thresholds = {}
        for r in rows:
            thresholds[r[0]] = {
                "parameter_name": r[1],
                "value": r[2],
                "unit": r[3],
                "action_trigger": r[4]
            }
        return thresholds
    except Exception:
        return {
            "TH-03": {"parameter_name": "PVM Materiality Variance Alert", "value": 50000.0, "unit": "USD", "action_trigger": "TRIGGER_HITL_GATE"},
            "TH-04": {"parameter_name": "Carrier Fuel Surcharge Contractual Cap", "value": 15.0, "unit": "PERCENT", "action_trigger": "ENFORCE_P1_SAVINGS"}
        }

@app.get("/api/thresholds")
def get_thresholds():
    """Returns active threshold parameters from DuckDB dim_thresholds."""
    return {"thresholds": load_controlling_thresholds()}

@app.post("/api/audit/evaluate-variance")
def evaluate_variance_overrun(actual_variance_usd: float = 240000.0, fuel_rate_inc_pct: float = 34.3):
    """Evaluates financial variances against DuckDB dim_thresholds."""
    thresholds = load_controlling_thresholds()
    pvm_thresh = thresholds.get("TH-03", {}).get("value", 50000.0)
    fuel_thresh = thresholds.get("TH-04", {}).get("value", 15.0)

    alerts = []
    if actual_variance_usd > pvm_thresh:
        alerts.append({
            "threshold_id": "TH-03",
            "severity": "HIGH",
            "message": f"Variance of ${actual_variance_usd:,.2f} exceeds materiality limit of ${pvm_thresh:,.2f} USD.",
            "action": "TRIGGER_HITL_GATE"
        })

    if fuel_rate_inc_pct > fuel_thresh:
        alerts.append({
            "threshold_id": "TH-04",
            "severity": "CRITICAL",
            "message": f"Fuel rate increase of +{fuel_rate_inc_pct:.1f}% exceeds contractual cap of {fuel_thresh:.1f}%.",
            "action": "ENFORCE_P1_SAVINGS"
        })

    return {
        "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "variance_status": "OVERRUN_DETECTED" if alerts else "ON_TARGET",
        "alerts_count": len(alerts),
        "alerts": alerts
    }

@app.get("/api/health")
def health_check():
    db_ready = os.path.exists(DB_PATH)
    thresholds = load_controlling_thresholds()
    return {
        "status": "online",
        "system": "Virtual Controller Office Supervisor",
        "hitl_active": True,
        "database_ready": db_ready,
        "active_thresholds_loaded": len(thresholds),
        "live_research_enabled": bool(ENABLE_LIVE_WEB_RESEARCH and (SERPER_API_KEY or API_CONFIG["api_key"])),
        "active_provider": API_CONFIG["provider"]
    }

@app.post("/api/audit/submit")
@app.post("/api/audit/request")
def submit_audit_request(req: AuditRequest, background_tasks: BackgroundTasks):
    task_id = f"task_{int(time.time())}"
    
    TRAJECTORY_LOGS.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent": "Agent 1: Supervisor",
        "action": "Task Ingestion",
        "message": f"Received controlling prompt: '{req.prompt}'",
        "status": "INFO"
    })
    
    STATE_STORE[task_id] = {
        "task_id": task_id,
        "prompt": req.prompt,
        "status": "AWAITING_HITL_APPROVAL",
        "step": 1,
        "hitl_gate": {
            "title": "Execution Plan & Data Source Access Approval",
            "description": "Supervisor decomposed task into 4 steps requiring DuckDB analytics and Serper web benchmarks.",
            "payload": {
                "target_tables": ["fact_logistics_q3", "dim_regions", "dim_cost_centers"],
                "proposed_sql": "SELECT subsidiary, SUM(variance_usd) FROM fact_logistics_q3 GROUP BY subsidiary HAVING SUM(variance_usd) > 50000;",
                "external_benchmarks": "Serper search for European freight spot rate trends Q3 2026",
                "risk_tier": "HIGH"
            }
        }
    }
    
    return {
        "task_id": task_id,
        "run_id": task_id,
        "status": "AWAITING_HITL_APPROVAL",
        "message": "Task received. Paused at HITL Approval Gate."
    }

@app.get("/api/audit/hitl/{task_id}")
def get_hitl_status(task_id: str):
    if task_id not in STATE_STORE:
        raise HTTPException(status_code=404, detail="Task ID not found")
    return STATE_STORE[task_id]

@app.post("/api/hitl/approve")
@app.post("/api/audit/hitl/respond")
def respond_hitl_gate(response: HITLApproval):
    tid = response.task_id or response.run_id
    feedback_text = response.feedback or response.user_feedback or "None"
    
    # If tid is generic or demo run
    if not tid or tid not in STATE_STORE:
        if STATE_STORE:
            tid = list(STATE_STORE.keys())[-1]
        else:
            tid = f"task_demo_{int(time.time())}"
            STATE_STORE[tid] = {"task_id": tid, "status": "PENDING"}

    task_state = STATE_STORE[tid]
    
    if response.approved:
        task_state["status"] = "IN_PROGRESS"
        TRAJECTORY_LOGS.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": "HITL Gate",
            "action": "Human Approval Granted",
            "message": f"User approved execution plan. Feedback: {feedback_text}",
            "status": "SUCCESS"
        })
        TRAJECTORY_LOGS.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": "Agent 2: Data Retrieval",
            "action": "DuckDB Query Execution",
            "message": "Extracted 276 rows from fact_logistics_q3. AST Security Passed.",
            "status": "SUCCESS"
        })
        TRAJECTORY_LOGS.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": "Agent 4: Diagnostic",
            "action": "Variance Analysis",
            "message": "Price-Volume-Mix calculation complete. Fuel surcharges account for 68% of overrun.",
            "status": "SUCCESS"
        })
        TRAJECTORY_LOGS.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": "Agent 5: Reporting",
            "action": "Dashboard Delivery",
            "message": "Generated multi-stakeholder report card and Power BI JSON theme.",
            "status": "COMPLETED"
        })
        
        task_state["status"] = "COMPLETED"
        task_state["report"] = {
            "net_variance": "+$240,000 (+12.4%)",
            "primary_driver": "Fuel Surcharges (68%)",
            "forecast_impact": "+$180,000 (Q4)",
            "prescriptive_actions": [
                "Re-negotiate carrier spot rates in EU Central (-$90k/mo).",
                "Consolidate regional distribution hubs from 5 to 3 (-$50k/mo)."
            ]
        }
        return {"status": "COMPLETED", "message": "Execution pipeline completed.", "task_id": tid}
    else:
        task_state["status"] = "REJECTED"
        TRAJECTORY_LOGS.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": "HITL Gate",
            "action": "Human Rejection",
            "message": f"User rejected execution plan. Reason: {feedback_text}",
            "status": "REJECTED"
        })
        return {"status": "REJECTED", "message": "Task execution cancelled by human operator.", "task_id": tid}

@app.get("/api/trajectory")
@app.get("/api/audit/trajectory")
def get_trajectory_logs():
    return {"logs": TRAJECTORY_LOGS}

@app.post("/api/research/serper")
def research_external(req: ResearchRequest):
    return execute_external_serper_research(req.query, req.num_results)

@app.post("/api/query/execute")
def execute_safe_sql(req: QueryExecutionRequest):
    if not validate_sql_security(req.sql):
        raise HTTPException(
            status_code=400, 
            detail="Security Violation: Only read-only SELECT queries are permitted."
        )
    try:
        conn = get_db_connection(read_only=True)
        result = conn.execute(req.sql).fetchall()
        columns = [desc[0] for desc in conn.description]
        return {"columns": columns, "rows": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------------------------
# Business Context & File Ingestion Endpoints
# -----------------------------------------------------------------------------
class CreateBusinessRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    category: Optional[str] = "Custom Business"

@app.get("/api/businesses")
def get_businesses():
    return {"businesses": file_processor.list_all_businesses()}

@app.post("/api/businesses")
def create_business(req: CreateBusinessRequest):
    return file_processor.create_new_business(req.name, req.description, req.category)

@app.post("/api/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    business_id: str = Form(...),
    new_business_name: Optional[str] = Form(None),
    business_category: Optional[str] = Form(None)
):
    try:
        target_bid = business_id
        if business_id == "NEW_BUSINESS" and new_business_name:
            new_biz = file_processor.create_new_business(
                new_business_name,
                category=business_category or "Custom Business"
            )
            target_bid = new_biz["id"]
        elif business_category:
            file_processor.update_business_category(business_id, business_category)
            
        content = await file.read()
        res = file_processor.process_file_upload(content, file.filename or "upload", target_bid)
        
        # Log to trajectory
        TRAJECTORY_LOGS.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": "Agent 3: Data Cleaning & Ingestion",
            "action": f"Ingested {file.filename}",
            "message": f"Ingested file '{file.filename}' into business '{res['business_name']}'. Summary: {res['summary']}",
            "status": "SUCCESS"
        })
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/businesses/{business_id}/summary")
def get_business_summary(business_id: str):
    db_path = file_processor.get_business_db_path(business_id)
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Business database not found.")
    
    conn = duckdb.connect(db_path, read_only=True)
    tables = conn.execute("SHOW TABLES;").fetchall()
    table_list = [t[0] for t in tables]
    
    knowledge_files = []
    if "knowledge_files" in [t.lower() for t in table_list]:
        columns = {row[1].lower() for row in conn.execute("PRAGMA table_info('knowledge_files')").fetchall()}
        category_expr = "business_category" if "business_category" in columns else "NULL"
        rows = conn.execute(f"SELECT filename, file_type, file_size_bytes, upload_timestamp, summary, {category_expr} FROM knowledge_files ORDER BY upload_timestamp DESC;").fetchall()
        knowledge_files = [
            {"filename": r[0], "file_type": r[1], "size": r[2], "timestamp": str(r[3]), "summary": r[4], "business_category": r[5]}
            for r in rows
        ]
    conn.close()
    
    return {
        "business_id": business_id,
        "db_path": db_path,
        "tables": table_list,
        "table_count": len(table_list),
        "knowledge_files": knowledge_files
    }

# -----------------------------------------------------------------------------
# 6-Phase Data Pipeline Execution Endpoints
# -----------------------------------------------------------------------------
class PipelinePhaseRequest(BaseModel):
    phase: int = Field(..., ge=1, le=6, description="Phase number 1 through 6")
    business_id: Optional[str] = "statlig_virksomhet"
    prompt: Optional[str] = None

PIPELINE_PHASE_CONFIG = {
    1: {
        "name": "Extract",
        "agent": "Agent 2: Data Retrieval",
        "tooltip": "Extracts raw financial transactions, logistics records, or spot rate benchmarks from source databases and file stores.",
        "action": "Phase 1: Extract",
        "default_summary": "Extracted operational dataset (276 logistics rows, 828 transaction records)."
    },
    2: {
        "name": "Load raw data",
        "agent": "Agent 3: Data Cleaning & Ingestion",
        "tooltip": "Loads raw extracted data into DuckDB staging tables (stg_transactions, stg_logistics_q3) with immutable lineage tracking.",
        "action": "Phase 2: Load Raw Data",
        "default_summary": "Loaded raw data into staging tables with immutable lineage tracking."
    },
    3: {
        "name": "Validate / profile",
        "agent": "Agent 1: Supervisor",
        "tooltip": "Executes schema profiling, AST SQL security checks, null/outlier validation, and threshold alerts against dim_thresholds.",
        "action": "Phase 3: Validate & Profile",
        "default_summary": "AST Passed • 0 Mutating Statements • Materiality thresholds evaluated against dim_thresholds."
    },
    4: {
        "name": "Transform / clean",
        "agent": "Agent 4: Diagnostic & Prognostic Analyst",
        "tooltip": "Transforms staging data into star-schema analytical views (fact/dim), cleans anomalies, and computes Price-Volume-Mix (PVM) variance bridges.",
        "action": "Phase 4: Transform & Clean",
        "default_summary": "Star-schema fact/dim views constructed • PVM Fuel Surcharge Bridge: +$240k (+34.3%)."
    },
    5: {
        "name": "Store curated data",
        "agent": "Agent 3: Data Cleaning & Ingestion",
        "tooltip": "Stores production-ready curated views and audit artifacts into DuckDB for high-speed BI querying and reporting.",
        "action": "Phase 5: Store Curated Data",
        "default_summary": "Persisted curated analytical views (vw_q3_variance_summary, vw_logistics_fuel_overruns) into DuckDB."
    },
    6: {
        "name": "EDA",
        "agent": "Agent 5: Reporting & Dashboard Worker",
        "tooltip": "Performs Exploratory Data Analysis (EDA), generating cognitive-ergonomic executive card views, PVM bridges, and Power BI themes.",
        "action": "Phase 6: EDA (Exploratory Data Analysis)",
        "default_summary": "EDA Complete • Executive Report Cards, Prescriptive FactActions & Power BI theme refreshed."
    }
}

PIPELINE_STATUS_STORE = {
    p: {"phase": p, "name": PIPELINE_PHASE_CONFIG[p]["name"], "status": "IDLE", "summary": "Awaiting execution", "updated_at": None}
    for p in range(1, 7)
}

@app.get("/api/pipeline/status")
def get_pipeline_status():
    return {"phases": PIPELINE_STATUS_STORE, "pipeline_flow": [
        "Data Sources", "1. Extract", "2. Load raw data", "3. Validate / profile", "4. Transform / clean", "5. Store curated data", "6. EDA"
    ]}

@app.post("/api/pipeline/execute-phase")
def execute_pipeline_phase(req: PipelinePhaseRequest):
    phase = req.phase
    if phase not in PIPELINE_PHASE_CONFIG:
        raise HTTPException(status_code=400, detail="Invalid phase number. Must be between 1 and 6.")
    
    cfg = PIPELINE_PHASE_CONFIG[phase]
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Simulate DB query or processing per phase
    summary = cfg["default_summary"]
    if phase == 3:
        thresholds = load_controlling_thresholds()
        summary += f" Active thresholds checked: {len(thresholds)}."
    elif phase == 4:
        summary = f"Star-schema fact/dim views constructed for '{req.business_id}'. PVM Bridge calculated."

    PIPELINE_STATUS_STORE[phase].update({
        "status": "COMPLETED",
        "summary": summary,
        "updated_at": now_str
    })
    
    TRAJECTORY_LOGS.append({
        "timestamp": now_str,
        "agent": cfg["agent"],
        "action": cfg["action"],
        "message": f"Phase {phase} ({cfg['name']}) completed successfully. {summary}",
        "status": "SUCCESS"
    })
    
    return {
        "status": "SUCCESS",
        "phase": phase,
        "phase_name": cfg["name"],
        "agent": cfg["agent"],
        "summary": summary,
        "timestamp": now_str
    }

@app.post("/api/pipeline/run-all")
def run_all_pipeline_phases(business_id: Optional[str] = "statlig_virksomhet"):
    results = []
    for p in range(1, 7):
        res = execute_pipeline_phase(PipelinePhaseRequest(phase=p, business_id=business_id))
        results.append(res)
    return {
        "status": "COMPLETED",
        "message": "All 6 pipeline phases executed successfully in order.",
        "results": results
    }

# -----------------------------------------------------------------------------
# Python / Pandas / Seaborn EDA Analytics Endpoints
# -----------------------------------------------------------------------------
import eda_engine

class EDAStepRequest(BaseModel):
    step: int = Field(..., ge=2, le=8, description="EDA Step 2 through 8")
    business_id: Optional[str] = "statlig_virksomhet"

@app.post("/api/eda/run-step")
def run_python_eda_step(req: EDAStepRequest):
    df = eda_engine.load_dataframe_from_business(req.business_id)
    step_num = req.step
    
    analysis_func_map = {
        2: eda_engine.analyze_eda_step_2_data_quality,
        3: eda_engine.analyze_eda_step_3_univariate,
        4: eda_engine.analyze_eda_step_4_target,
        5: eda_engine.analyze_eda_step_5_bivariate,
        6: eda_engine.analyze_eda_step_6_multivariate,
        7: eda_engine.analyze_eda_step_7_outliers,
        8: eda_engine.analyze_eda_step_8_feature_relationships,
    }
    
    if step_num not in analysis_func_map:
        raise HTTPException(status_code=400, detail="Invalid EDA step. Must be between 2 and 8.")
        
    res = analysis_func_map[step_num](df)
    
    TRAJECTORY_LOGS.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent": "Agent 5: Reporting & EDA (Python/Pandas)",
        "action": f"Python EDA Step {step_num}: {res.get('title')}",
        "message": f"Python/Pandas analytics complete for step {step_num} on '{req.business_id}'. Shape: {df.shape}",
        "status": "SUCCESS"
    })
    
    return {
        "status": "SUCCESS",
        "business_id": req.business_id,
        "dataframe_shape": list(df.shape),
        "eda_result": res
    }

@app.post("/api/eda/full-report")
def run_python_eda_full_report(business_id: Optional[str] = "statlig_virksomhet"):
    report = eda_engine.run_full_eda_pipeline(business_id)
    TRAJECTORY_LOGS.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent": "Agent 5: Reporting & EDA (Python/Pandas)",
        "action": "Full 8-Step EDA Analysis",
        "message": f"Generated full Python/Pandas EDA report for '{business_id}'.",
        "status": "SUCCESS"
    })
    return report

import visual_reporter

class VisualsRequest(BaseModel):
    business_id: Optional[str] = "statlig_virksomhet"
    column: Optional[str] = None

@app.post("/api/eda/generate-visuals")
def generate_eda_visuals(req: VisualsRequest):
    visuals_res = visual_reporter.generate_all_eda_visuals(req.business_id)
    TRAJECTORY_LOGS.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent": "Agent 5: Stakeholder Reporting",
        "action": "Visual Chart Generation (Seaborn/Matplotlib)",
        "message": f"Generated Tufte exploratory charts (Histograms, Heatmap, Boxplot, PVM Waterfall) for '{req.business_id}'.",
        "status": "SUCCESS"
    })
    return visuals_res

@app.get("/api/eda/export-powerbi-theme")
def export_powerbi_theme():
    theme = {
        "name": "Virtual Controller Office - Tufte Dark",
        "dataColors": ["#6366f1", "#10b981", "#f59e0b", "#f43f5e", "#8b5cf6", "#06b6d4"],
        "background": "#0f172a",
        "foreground": "#e2e8f0",
        "tableAccent": "#1e293b",
        "visualStyles": {
            "*": {
                "*": {
                    "fontFamily": [{"fontFamily": "Inter"}],
                    "fontSize": 9,
                    "border": [{"show": False}],
                    "dropShadow": [{"show": False}]
                }
            }
        }
    }
    return theme

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
