import os
import re
import glob
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
import duckdb
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOCAL_DATA_DIR = os.path.join(BASE_DIR, "Local Data")
REGISTRY_PATH = os.path.join(DATA_DIR, "businesses.json")
KNOWLEDGE_STORE_DIR = os.path.join(DATA_DIR, "knowledge")

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(KNOWLEDGE_STORE_DIR, exist_ok=True)

def slugify(text: str) -> str:
    """Converts a string into a clean lowercase identifier slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text.strip('_')

def get_business_db_path(business_id: str) -> str:
    """Returns absolute path to the DuckDB database for a business."""
    slug = slugify(business_id)
    if slug == "statlig_virksomhet":
        return os.path.join(DATA_DIR, "statlig_virksomhet.duckdb")
    elif slug in ["controller_office", "logistics_eu", "eu_logistics_enterprise"]:
        return os.path.join(DATA_DIR, "controller_office.duckdb")
    return os.path.join(DATA_DIR, f"{slug}.duckdb")

def load_business_registry() -> Dict[str, Dict[str, Any]]:
    """Loads the registered businesses from businesses.json."""
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Default built-in registry
    defaults = {
        "statlig_virksomhet": {
            "id": "statlig_virksomhet",
            "name": "Statlig Virksomhet (DFØ / SRS)",
            "description": "State Education & Research Institution under DFØ & SRS regulations (UiA Context)",
            "category": "Public Sector / Government",
            "db_path": os.path.join(DATA_DIR, "statlig_virksomhet.duckdb")
        },
        "logistics_eu": {
            "id": "logistics_eu",
            "name": "EU Logistics & Freight Enterprise",
            "description": "Global Freight, Transportation & Logistics Variance Audit",
            "category": "Commercial Supply Chain",
            "db_path": os.path.join(DATA_DIR, "controller_office.duckdb")
        }
    }
    save_business_registry(defaults)
    return defaults

def save_business_registry(registry: Dict[str, Dict[str, Any]]):
    """Saves business registry to JSON."""
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

def list_all_businesses() -> List[Dict[str, Any]]:
    """
    Returns list of all available businesses, combining local directories,
    duckdb database files, and registered business entries.
    """
    registry = load_business_registry()
    
    # Check Local Data directory for automatic business discovery
    if os.path.exists(LOCAL_DATA_DIR):
        for entry in os.listdir(LOCAL_DATA_DIR):
            full_p = os.path.join(LOCAL_DATA_DIR, entry)
            if os.path.isdir(full_p):
                bid = slugify(entry)
                if bid not in registry:
                    registry[bid] = {
                        "id": bid,
                        "name": entry,
                        "description": f"Discovered from Local Data directory '{entry}'",
                        "category": "Custom Local Business",
                        "db_path": get_business_db_path(bid)
                    }

    result = []
    for bid, meta in registry.items():
        db_p = meta.get("db_path", get_business_db_path(bid))
        table_cnt = 0
        doc_cnt = 0
        db_status = "uninitialized"
        
        if os.path.exists(db_p):
            try:
                conn = duckdb.connect(db_p, read_only=True)
                tables = conn.execute("SHOW TABLES;").fetchall()
                table_cnt = len(tables)
                
                # Check knowledge docs count if table exists
                tbl_names = [t[0].lower() for t in tables]
                if "knowledge_files" in tbl_names:
                    doc_cnt = conn.execute("SELECT COUNT(*) FROM knowledge_files;").fetchone()[0]
                conn.close()
                db_status = "ready"
            except Exception as e:
                db_status = f"error: {str(e)}"
        
        item = {**meta}
        item["db_exists"] = os.path.exists(db_p)
        item["table_count"] = table_cnt
        item["doc_count"] = doc_cnt
        item["status"] = db_status
        result.append(item)
        
    return result

def create_new_business(name: str, description: str = "", category: str = "Custom Business") -> Dict[str, Any]:
    """Registers a new business entity."""
    bid = slugify(name)
    registry = load_business_registry()
    
    meta = {
        "id": bid,
        "name": name,
        "description": description or f"Custom business context '{name}'",
        "category": category,
        "db_path": get_business_db_path(bid),
        "created_at": datetime.now().isoformat()
    }
    registry[bid] = meta
    save_business_registry(registry)
    
    # Initialize duckdb database
    db_p = meta["db_path"]
    conn = duckdb.connect(db_p)
    ensure_knowledge_tables(conn)
    conn.close()
    
    return meta

def ensure_knowledge_tables(conn: duckdb.DuckDBPyConnection):
    """Ensures that Knowledge Management metadata tables exist in the DuckDB database."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_files (
            file_id VARCHAR PRIMARY KEY,
            filename VARCHAR,
            file_type VARCHAR,
            file_size_bytes BIGINT,
            upload_timestamp TIMESTAMP,
            stored_table_name VARCHAR,
            row_count BIGINT,
            column_count INTEGER,
            summary VARCHAR
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_text_index (
            doc_id VARCHAR PRIMARY KEY,
            file_id VARCHAR,
            filename VARCHAR,
            title VARCHAR,
            content TEXT,
            uploaded_at TIMESTAMP
        );
    """)

def process_file_upload(file_content: bytes, filename: str, business_id: str) -> Dict[str, Any]:
    """
    Processes any uploaded file, ingests tabular data into DuckDB tables,
    extracts text into knowledge_text_index, and saves file in knowledge storage.
    """
    bid = slugify(business_id)
    registry = load_business_registry()
    
    if bid not in registry:
        # Auto-create business if not existing
        create_new_business(business_id)
        registry = load_business_registry()
        
    db_path = registry[bid].get("db_path", get_business_db_path(bid))
    
    # Save raw file to knowledge directory
    target_biz_dir = os.path.join(KNOWLEDGE_STORE_DIR, bid)
    os.makedirs(target_biz_dir, exist_ok=True)
    raw_file_path = os.path.join(target_biz_dir, filename)
    with open(raw_file_path, "wb") as f:
        f.write(file_content)
        
    ext = os.path.splitext(filename)[1].lower()
    file_id = f"doc_{int(datetime.now().timestamp() * 1000)}"
    file_size = len(file_content)
    
    conn = duckdb.connect(db_path)
    ensure_knowledge_tables(conn)
    
    summary_info = ""
    stored_table = ""
    row_count = 0
    col_count = 0
    
    try:
        if ext == ".csv":
            # Process CSV
            clean_table_name = f"tbl_{slugify(os.path.splitext(filename)[0])}"
            # Test delimiter
            sample_text = file_content[:4096].decode("utf-8", errors="ignore")
            delim = ';' if ';' in sample_text else ','
            
            conn.execute(f"DROP TABLE IF EXISTS {clean_table_name};")
            conn.execute(f"""
                CREATE TABLE {clean_table_name} AS 
                SELECT * FROM read_csv_auto('{raw_file_path.replace('\\', '/')}', delim='{delim}', header=True);
            """)
            
            row_count = conn.execute(f"SELECT COUNT(*) FROM {clean_table_name};").fetchone()[0]
            cols = [c[0] for c in conn.execute(f"DESCRIBE {clean_table_name};").fetchall()]
            col_count = len(cols)
            stored_table = clean_table_name
            summary_info = f"Ingested CSV table '{clean_table_name}' with {row_count} rows and {col_count} columns ({', '.join(cols[:5])}...)"

        elif ext in [".xlsx", ".xls"]:
            # Process Excel using pandas
            excel_df_dict = pd.read_excel(raw_file_path, sheet_name=None)
            sheets_created = []
            total_rows = 0
            
            for sheet_name, df in excel_df_dict.items():
                sheet_table_name = f"tbl_{slugify(os.path.splitext(filename)[0])}_{slugify(sheet_name)}"
                conn.register("tmp_excel_df", df)
                conn.execute(f"DROP TABLE IF EXISTS {sheet_table_name};")
                conn.execute(f"CREATE TABLE {sheet_table_name} AS SELECT * FROM tmp_excel_df;")
                conn.unregister("tmp_excel_df")
                
                rows = len(df)
                total_rows += rows
                sheets_created.append(f"{sheet_table_name} ({rows} rows)")
                if not stored_table:
                    stored_table = sheet_table_name
                    col_count = len(df.columns)
            
            row_count = total_rows
            summary_info = f"Ingested Excel workbook into {len(sheets_created)} sheets: {', '.join(sheets_created)}"

        elif ext == ".json":
            # Process JSON
            clean_table_name = f"tbl_{slugify(os.path.splitext(filename)[0])}"
            try:
                conn.execute(f"DROP TABLE IF EXISTS {clean_table_name};")
                conn.execute(f"""
                    CREATE TABLE {clean_table_name} AS 
                    SELECT * FROM read_json_auto('{raw_file_path.replace('\\', '/')}');
                """)
                row_count = conn.execute(f"SELECT COUNT(*) FROM {clean_table_name};").fetchone()[0]
                cols = [c[0] for c in conn.execute(f"DESCRIBE {clean_table_name};").fetchall()]
                col_count = len(cols)
                stored_table = clean_table_name
                summary_info = f"Ingested JSON table '{clean_table_name}' with {row_count} rows."
            except Exception:
                # Store as text document knowledge if JSON structure is nested/unstructured
                text_content = file_content.decode("utf-8", errors="ignore")
                conn.execute("""
                    INSERT INTO knowledge_text_index VALUES (?, ?, ?, ?, ?, ?);
                """, (f"text_{file_id}", file_id, filename, filename, text_content, datetime.now()))
                summary_info = f"Stored JSON as document knowledge ({len(text_content)} chars)."

        elif ext in [".txt", ".md", ".pdf", ".log"]:
            # Process Text / Markdown / Document
            text_content = file_content.decode("utf-8", errors="ignore")
            conn.execute("""
                INSERT INTO knowledge_text_index VALUES (?, ?, ?, ?, ?, ?);
            """, (f"text_{file_id}", file_id, filename, filename, text_content, datetime.now()))
            summary_info = f"Indexed text document knowledge ({len(text_content)} chars)."

        else:
            # Fallback binary file storage
            summary_info = f"Stored raw file '{filename}' in knowledge repository."

        # Insert metadata record
        conn.execute("""
            INSERT INTO knowledge_files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            file_id,
            filename,
            ext.replace(".", "").upper(),
            file_size,
            datetime.now(),
            stored_table,
            row_count,
            col_count,
            summary_info
        ))

        conn.close()
        
        return {
            "status": "success",
            "file_id": file_id,
            "filename": filename,
            "business_id": bid,
            "business_name": registry[bid]["name"],
            "stored_table": stored_table,
            "row_count": row_count,
            "file_size": file_size,
            "summary": summary_info
        }

    except Exception as e:
        conn.close()
        raise RuntimeError(f"Error processing file '{filename}': {str(e)}")
