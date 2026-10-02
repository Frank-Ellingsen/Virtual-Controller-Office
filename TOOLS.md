# TOOLS.md — MCP Tool Manifest & JSON Schemas

## Overview
Model Context Protocol (MCP) server definitions exposing internal databases, local files, web retrieval, and visualization generators.

## Tool Definitions

### 1. Database & Local Data Tools

#### `duckdb_query`
- **Description**: Runs high-performance analytical SQL queries on local DuckDB database or Parquet files. Strictly `SELECT` queries.
- **Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "SQL SELECT query to execute against DuckDB."
    },
    "limit": {
      "type": "integer",
      "default": 100,
      "description": "Maximum rows to return."
    }
  },
  "required": ["query"]
}
```

#### `excel_parse_workbook`
- **Description**: Reads sheets, formulas, and data tables from local Excel workbooks (`.xlsx`, `.xls`).
- **Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "file_path": { "type": "string" },
    "sheet_name": { "type": "string" }
  },
  "required": ["file_path"]
}
```

### 2. External Retrieval Tools

#### `serper_web_search`
- **Description**: Conducts targeted Google search queries via Serper API for market benchmarks and industry financial indicators.
- **Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": { "type": "string" },
    "num_results": { "type": "integer", "default": 5 }
  },
  "required": ["query"]
}
```

### 3. Visualization & Output Tools

#### `generate_powerbi_theme`
- **Description**: Generates a custom Power BI Theme JSON file adhering to enterprise contrast and design standards.
- **Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "primary_color": { "type": "string" },
    "secondary_color": { "type": "string" },
    "font_family": { "type": "string", "default": "Segoe UI" }
  },
  "required": ["primary_color"]
}
```

#### `generate_web_dashboard`
- **Description**: Compiles an interactive HTML/JS virtual web dashboard with Recharts visual components and executive KPI cards.

#### `generate_eda_visual_charts`
- **Description**: Generates Seaborn/Matplotlib base64 SVG charts and Chart.js dataset specs for 8-step EDA (Histograms, Heatmaps, Boxplots, PVM Bridges).
- **Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "step": { "type": "integer", "description": "EDA step number 1 through 8" },
    "chart_type": { "type": "string", "enum": ["histogram", "heatmap", "boxplot", "pvm_bridge", "scatter"] },
    "business_id": { "type": "string" }
  },
  "required": ["step", "chart_type"]
}
```