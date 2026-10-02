# Copilot Developer Architecture Guide — Virtual Controller Office

This guide helps developers use GitHub Copilot when extending the Virtual Controller Office. Treat diagrams and prompts as design guidance; validate the current implementation and schema before relying on them.

---

## System Components and Data Flow

```text
Browser Dashboard (index.html / web/index.html)
        | REST API (when a backend is configured)
        v
FastAPI service (server.py) ---- DuckDB business databases
        |                          scripts/file_processor.py
        +---- optional Serper research
        +---- HITL and trajectory endpoints
```

The dashboard can also run as a static page. In that mode, supported uploads and results are stored locally in the browser; the page does not connect to a shared FastAPI or DuckDB service.

## Architecture Notes

- `server.py` defines the actual API routes and the SQL safety validator. Inspect it before adding routes or describing runtime behavior.
- `scripts/file_processor.py` owns business discovery, per-business storage, and file ingestion.
- `index.html` is the primary frontend; keep `web/index.html` in sync with UI changes.
- `tests/` contains automated tests. Add regression coverage for behavior changes.
- The agent registry in `AGENTS.md` describes the intended roles. Do not assume a LangGraph runtime, WebSocket transport, or fully autonomous worker implementation unless the current code explicitly provides it.

## Prompt Recipes

### 1. Add a Read-Only FastAPI Endpoint

> Inspect `server.py` and the current DuckDB schema first. Add a read-only FastAPI endpoint for the requested summary using the project’s existing connection and error-handling conventions. Reject unsafe SQL, parameterize values, and add pytest coverage.

### 2. Create a Headless Financial Plot

> Write a Python analysis using dependencies already declared by this project. Select Matplotlib's `Agg` backend before importing `pyplot`, validate input columns, save the chart to a caller-provided path, and close the figure. Give the chart an insight-focused title.

### 3. Modify the Dashboard

> Update the dashboard to display the requested data from an existing API endpoint or a clearly identified browser-local calculation. Keep `index.html` and `web/index.html` synchronized, handle loading/error/empty states, and verify the static GitHub Pages behavior.

### 4. Investigate a Dataset

> Inspect the actual workbook/database headers and representative rows before writing calculations. Document assumptions, missing-value handling, and row counts; never infer field names from a prompt template alone.

## Validation Commands

- Backend tests: `pytest -q`
- API integration scripts: review and run the relevant script under `scripts/` or at the repository root.
- For frontend changes, test both the FastAPI-served page and the static/browser-only path when applicable.
