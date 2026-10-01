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


def discover_local_data_dirs() -> List[Dict[str, str]]:
    """Discovers business folders under the Local Data directory and returns their metadata."""
    if not os.path.exists(LOCAL_DATA_DIR):
        return []

    discovered = []
    for entry in sorted(os.listdir(LOCAL_DATA_DIR)):
        full_path = os.path.join(LOCAL_DATA_DIR, entry)
        if os.path.isdir(full_path):
            discovered.append({
                "id": slugify(entry),
                "name": entry,
                "folder": full_path,
            })
    return discovered


def initialize_local_business_database(business_id: str, source_dir: str = None) -> Dict[str, Any]:
    """Creates a DuckDB database for a Local Data business folder by ingesting data files in that folder."""
    source_dir = source_dir or None
    if source_dir is None:
        for candidate in discover_local_data_dirs():
            if candidate["id"] == slugify(business_id):
                source_dir = candidate["folder"]
                break

    if not source_dir or not os.path.isdir(source_dir):
        raise FileNotFoundError(f"No Local Data directory found for business '{business_id}'.")

    db_path = get_business_db_path(business_id)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = duckdb.connect(db_path)
    ensure_knowledge_tables(conn)

    file_count = 0
    table_names = []
    for filename in sorted(os.listdir(source_dir)):
        full_path = os.path.join(source_dir, filename)
        if not os.path.isfile(full_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in {".csv", ".json", ".txt", ".md", ".log"}:
            continue

        file_count += 1
        if ext == ".csv":
            table_name = f"tbl_{slugify(os.path.splitext(filename)[0])}"
            sample_text = open(full_path, "r", encoding="utf-8", errors="ignore").read(4096)
            delim = ';' if ';' in sample_text else ','
            conn.execute(f"DROP TABLE IF EXISTS {table_name};")
            conn.execute(f"""
                CREATE TABLE {table_name} AS
                SELECT * FROM read_csv_auto('{full_path.replace('\\', '/')}', delim='{delim}', header=True);
            """)
            table_names.append(table_name)
        else:
            text_content = open(full_path, "r", encoding="utf-8", errors="ignore").read()
            doc_id = f"text_{int(datetime.now().timestamp() * 1000)}_{len(table_names)}"
            conn.execute("""
                INSERT INTO knowledge_text_index VALUES (?, ?, ?, ?, ?, ?);
            """, (doc_id, doc_id, filename, filename, text_content, datetime.now()))

    conn.close()
    return {
        "business_id": slugify(business_id),
        "db_path": db_path,
        "file_count": file_count,
        "table_count": len(table_names),
        "tables": table_names,
    }


def ensure_local_data_businesses_initialized() -> None:
    """Initializes any Local Data business folders that have not yet been bootstrapped into a DuckDB database."""
    registry = load_business_registry()
    for directory in discover_local_data_dirs():
        biz_id = directory["id"]
        db_path = get_business_db_path(biz_id)
        if os.path.exists(db_path):
            continue
        if biz_id not in registry:
            registry[biz_id] = {
                "id": biz_id,
                "name": directory["name"],
                "description": f"Discovered from Local Data directory '{directory['name']}'",
                "category": "Custom Local Business",
                "db_path": db_path,
            }
            save_business_registry(registry)
        initialize_local_business_database(biz_id, directory["folder"])


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
        },
        "umoe_mandal_defense": {
            "id": "umoe_mandal_defense",
            "name": "Umoe Mandal Defense & Maritime",
            "description": "Naval Defense & Composite Shipyard Project Controlling (EAC/ETC)",
            "category": "Defense & Maritime Engineering",
            "db_path": os.path.join(DATA_DIR, "umoe_mandal_defense.duckdb")
        },
        "premier_league": {
            "id": "premier_league",
            "name": "Premier League & Sports Analytics",
            "description": "English Premier League Match Data, Financial Performance & Operational Metrics",
            "category": "Sports & Entertainment Analytics",
            "db_path": os.path.join(DATA_DIR, "premier_league.duckdb")
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
    ensure_local_data_businesses_initialized()
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS business_context (
            business_id VARCHAR PRIMARY KEY,
            business_name VARCHAR,
            business_category VARCHAR,
            description TEXT,
            updated_at TIMESTAMP
        );
    """)
    conn.execute("INSERT OR REPLACE INTO business_context VALUES (?, ?, ?, ?, ?);",
                 (bid, name, category, meta["description"], datetime.now()))
    conn.close()
    
    return meta

def update_business_category(business_id: str, category: str) -> Dict[str, Any]:
    """Updates a business category in the registry and its DuckDB knowledge database."""
    bid = slugify(business_id)
    registry = load_business_registry()
    if bid not in registry:
        raise ValueError(f"Business '{business_id}' is not registered.")

    meta = registry[bid]
    meta["category"] = category.strip() or meta.get("category", "Custom Business")
    save_business_registry(registry)

    conn = duckdb.connect(meta.get("db_path", get_business_db_path(bid)))
    ensure_knowledge_tables(conn)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS business_context (
            business_id VARCHAR PRIMARY KEY,
            business_name VARCHAR,
            business_category VARCHAR,
            description TEXT,
            updated_at TIMESTAMP
        );
    """)
    conn.execute("INSERT OR REPLACE INTO business_context VALUES (?, ?, ?, ?, ?);",
                 (bid, meta["name"], meta["category"], meta.get("description", ""), datetime.now()))
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
            summary VARCHAR,
            business_category VARCHAR
        );
    """)
    knowledge_file_columns = {
        row[1].lower() for row in conn.execute("PRAGMA table_info('knowledge_files')").fetchall()
    }
    if "business_category" not in knowledge_file_columns:
        conn.execute("ALTER TABLE knowledge_files ADD COLUMN business_category VARCHAR")
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

        elif ext in [".xlsx", ".xls", ".xlsm"]:
            # Process Excel using pandas with openpyxl/xlrd
            excel_df_dict = pd.read_excel(raw_file_path, sheet_name=None)
            sheets_created = []
            total_rows = 0
            all_text_snippets = []
            
            base_fname = slugify(os.path.splitext(filename)[0])
            sheet_keys = list(excel_df_dict.keys())
            
            for sheet_name, df in excel_df_dict.items():
                if df is None or df.empty:
                    continue
                
                # Sanitize column names for clean DuckDB queries
                clean_cols = []
                seen_cols = set()
                for i, col in enumerate(df.columns):
                    c_str = str(col).strip()
                    c_slug = slugify(c_str) if c_str and c_str.lower() != 'unnamed' else f"col_{i+1}"
                    if not c_slug:
                        c_slug = f"col_{i+1}"
                    original_slug = c_slug
                    counter = 1
                    while c_slug in seen_cols:
                        c_slug = f"{original_slug}_{counter}"
                        counter += 1
                    seen_cols.add(c_slug)
                    clean_cols.append(c_slug)
                
                df.columns = clean_cols
                
                clean_sheet = slugify(str(sheet_name))
                if len(sheet_keys) == 1 or clean_sheet in ["sheet1", "sheet_1", "table1", "data"]:
                    sheet_table_name = f"tbl_{base_fname}"
                else:
                    sheet_table_name = f"tbl_{base_fname}_{clean_sheet}"
                
                # Register with DuckDB
                conn.register("tmp_excel_df", df)
                conn.execute(f"DROP TABLE IF EXISTS {sheet_table_name};")
                conn.execute(f"CREATE TABLE {sheet_table_name} AS SELECT * FROM tmp_excel_df;")
                conn.unregister("tmp_excel_df")
                
                rows = len(df)
                total_rows += rows
                sheets_created.append(f"{sheet_table_name} ({rows} rows, {len(df.columns)} cols)")
                if not stored_table:
                    stored_table = sheet_table_name
                    col_count = len(df.columns)
                
                # Sample text summary for text search index
                sample_str = df.head(10).to_string()
                all_text_snippets.append(f"Sheet: {sheet_name}\nColumns: {', '.join(clean_cols)}\nSample:\n{sample_str}")

            row_count = total_rows
            summary_info = f"Ingested Excel workbook '{filename}' into {len(sheets_created)} table(s): {', '.join(sheets_created)}"
            
            # Index summary text into knowledge text index
            if all_text_snippets:
                full_text = f"Excel File: {filename}\n" + "\n\n".join(all_text_snippets)
                conn.execute("""
                    INSERT INTO knowledge_text_index VALUES (?, ?, ?, ?, ?, ?);
                """, (f"text_{file_id}", file_id, filename, filename, full_text, datetime.now()))

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
            INSERT INTO knowledge_files (
                file_id, filename, file_type, file_size_bytes, upload_timestamp,
                stored_table_name, row_count, column_count, summary, business_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            file_id,
            filename,
            ext.replace(".", "").upper(),
            file_size,
            datetime.now(),
            stored_table,
            row_count,
            col_count,
            summary_info,
            registry[bid].get("category", "Custom Business")
        ))

        conn.close()
        
        return {
            "status": "success",
            "file_id": file_id,
            "filename": filename,
            "business_id": bid,
            "business_name": registry[bid]["name"],
            "business_category": registry[bid].get("category", "Custom Business"),
            "stored_table": stored_table,
            "row_count": row_count,
            "file_size": file_size,
            "summary": summary_info
        }

    except Exception as e:
        conn.close()
        raise RuntimeError(f"Error processing file '{filename}': {str(e)}")
