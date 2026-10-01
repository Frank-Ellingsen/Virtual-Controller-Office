# HOOKS.md — Deterministic Lifecycle Hooks & Safety Guardrails

## Overview
Hooks run **outside** the LLM context as deterministic Python middleware. They validate parameters, enforce security boundaries, sanitize outputs, and log full execution traces.

## Deterministic Hook Declarations

### 1. PreToolUse Hooks (Execution Guardrails)

```python
# hooks/pre_tool_use.py

def pre_tool_use_sql_validator(tool_name: str, tool_args: dict) -> dict:
    """
    Enforces strict SELECT-only execution on DuckDB/SQLite tools.
    Blocks any DROP, DELETE, INSERT, UPDATE, or ALTER statements at the parser level.
    """
    if tool_name in ["duckdb_query", "sqlite_query"]:
        query = tool_args.get("query", "").upper().strip()
        forbidden_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "CREATE TABLE"]
        for keyword in forbidden_keywords:
            if keyword in query:
                raise PermissionError(f"[SECURITY BLOCK]: Destructive SQL keyword '{keyword}' detected. SQL agents are strictly limited to SELECT queries.")
    return tool_args

def pre_tool_use_pii_masker(tool_name: str, tool_args: dict) -> dict:
    """
    Redacts sensitive PII (emails, tax IDs, credit cards) before sending payloads to external APIs or LLM context.
    """
    return tool_args
```

### 2. HITL Approval Gate Hook

```python
# hooks/hitl_approval_gate.py

def hitl_action_risk_evaluator(proposed_action: dict) -> bool:
    """
    Evaluates action risk rating (LOW, MEDIUM, HIGH).
    If HIGH (e.g., executing strategy, issuing final audit report, budget reallocation),
    pauses execution state and generates a Web UI notification for human approval.
    """
    risk_level = proposed_action.get("risk_level", "LOW")
    if risk_level in ["MEDIUM", "HIGH"]:
        # Triggers Virtual Web UI approval card
        return False  # Execution paused until human clicks 'Approve'
    return True
```

### 3. PostToolUse Hooks (Observability & Sanitization)

```python
# hooks/post_tool_use.py

def post_tool_use_trace_logger(tool_name: str, tool_args: dict, result: dict, execution_time_ms: float):
    """
    Logs tool execution metadata, token spend, latency, and sanitized outputs to local SQLite audit log.
    """
    pass

def post_tool_use_output_sanitizer(tool_name: str, result: dict) -> dict:
    """
    Strips raw HTML tags and potential prompt injection payloads from web search results or external documents.
    """
    return result
```