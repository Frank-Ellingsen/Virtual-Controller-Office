import os
import duckdb
import random
from datetime import datetime, timedelta

def initialize_database(db_path: str = "controller_office.duckdb"):
    """
    Initializes and seeds the DuckDB database for the Virtual Controller Office
    with realistic financial, logistics, and variance data.
    """
    print(f"Connecting to DuckDB database at '{db_path}'...")
    parent_dir = os.path.dirname(os.path.abspath(db_path))
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    conn = duckdb.connect(db_path)
    
    # Enable clean schema recreation
    conn.execute("DROP VIEW IF EXISTS vw_logistics_fuel_overruns;")
    conn.execute("DROP VIEW IF EXISTS vw_regional_cost_breakdown;")
    conn.execute("DROP VIEW IF EXISTS vw_q3_variance_summary;")
    conn.execute("DROP TABLE IF EXISTS fact_logistics_q3;")
    conn.execute("DROP TABLE IF EXISTS fact_financial_transactions;")
    conn.execute("DROP TABLE IF EXISTS dim_accounts;")
    conn.execute("DROP TABLE IF EXISTS dim_cost_centers;")
    conn.execute("DROP TABLE IF EXISTS dim_regions;")
    
    print("Creating Dimension Tables...")
    
    # 1. Dim Regions
    conn.execute("""
    CREATE TABLE dim_regions (
        region_id VARCHAR PRIMARY KEY,
        region_name VARCHAR,
        country VARCHAR,
        currency VARCHAR
    );
    """)
    conn.execute("""
    INSERT INTO dim_regions VALUES
        ('REG_EU_C', 'EU Central', 'Germany', 'EUR'),
        ('REG_EU_W', 'EU West', 'France', 'EUR'),
        ('REG_NA_E', 'North America East', 'United States', 'USD'),
        ('REG_NA_W', 'North America West', 'United States', 'USD'),
        ('REG_APAC', 'Asia Pacific', 'Singapore', 'USD');
    """)
    
    # 2. Dim Cost Centers
    conn.execute("""
    CREATE TABLE dim_cost_centers (
        cost_center_id VARCHAR PRIMARY KEY,
        cost_center_name VARCHAR,
        department VARCHAR,
        owner VARCHAR
    );
    """)
    conn.execute("""
    INSERT INTO dim_cost_centers VALUES
        ('CC_LOG_101', 'Inbound Freight', 'Logistics', 'Elena Rostova'),
        ('CC_LOG_102', 'Outbound Fulfillment', 'Logistics', 'Marcus Vance'),
        ('CC_LOG_103', 'Regional Warehousing', 'Logistics', 'Sarah Jenkins'),
        ('CC_OPS_201', 'Plant Manufacturing', 'Operations', 'Karl Weber'),
        ('CC_MKT_301', 'Global Marketing', 'Marketing', 'Chloe Dubois');
    """)
    
    # 3. Dim Accounts
    conn.execute("""
    CREATE TABLE dim_accounts (
        account_id VARCHAR PRIMARY KEY,
        account_name VARCHAR,
        category VARCHAR,
        account_type VARCHAR
    );
    """)
    conn.execute("""
    INSERT INTO dim_accounts VALUES
        ('ACC_5001', 'Freight & Transport', 'Logistics Cost', 'Expense'),
        ('ACC_5002', 'Fuel Surcharge', 'Logistics Cost', 'Expense'),
        ('ACC_5003', 'Warehouse Storage', 'Facilities', 'Expense'),
        ('ACC_5004', 'Packaging Supplies', 'Operations', 'Expense'),
        ('ACC_4001', 'Gross Product Revenue', 'Sales Revenue', 'Revenue');
    """)
    
    print("Creating Fact Tables...")
    
    # 4. Fact Financial Transactions
    conn.execute("""
    CREATE TABLE fact_financial_transactions (
        transaction_id VARCHAR PRIMARY KEY,
        txn_date DATE,
        region_id VARCHAR,
        cost_center_id VARCHAR,
        account_id VARCHAR,
        actual_amount DOUBLE,
        budget_amount DOUBLE,
        variance_amount DOUBLE
    );
    """)
    
    # Generate seed data for Fact Financial Transactions across 2026
    random.seed(42)
    tx_rows = []
    regions = ['REG_EU_C', 'REG_EU_W', 'REG_NA_E', 'REG_NA_W', 'REG_APAC']
    ccs = ['CC_LOG_101', 'CC_LOG_102', 'CC_LOG_103', 'CC_OPS_201', 'CC_MKT_301']
    accs = ['ACC_5001', 'ACC_5002', 'ACC_5003', 'ACC_5004']
    
    tx_counter = 1000
    start_date = datetime(2026, 1, 1)
    for day in range(270): # Jan 1 to Sep 27 (Q1-Q3)
        current_date = start_date + timedelta(days=day)
        # Generate 2-4 transactions per day
        for _ in range(random.randint(2, 4)):
            tx_counter += 1
            tx_id = f"TX_{tx_counter}"
            reg = random.choice(regions)
            cc = random.choice(ccs)
            acc = random.choice(accs)
            
            base_budget = round(random.uniform(5000, 45000), 2)
            
            # Inject realistic variance: EU Central logistics fuel surcharges spiked in Q3
            if reg == 'REG_EU_C' and acc == 'ACC_5002' and current_date.month in [7, 8, 9]:
                actual = round(base_budget * random.uniform(1.25, 1.45), 2) # 25-45% overrun
            else:
                actual = round(base_budget * random.uniform(0.92, 1.08), 2) # normal fluctuation
                
            variance = round(actual - base_budget, 2)
            tx_rows.append((tx_id, current_date.strftime('%Y-%m-%d'), reg, cc, acc, actual, base_budget, variance))
            
    conn.executemany("""
        INSERT INTO fact_financial_transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, tx_rows)
    
    # 5. Fact Logistics Q3 (Detailed granularity for Q3 audit)
    conn.execute("""
    CREATE TABLE fact_logistics_q3 (
        logistics_id VARCHAR PRIMARY KEY,
        shipment_date DATE,
        region_id VARCHAR,
        route VARCHAR,
        carrier VARCHAR,
        fuel_surcharge_actual DOUBLE,
        fuel_surcharge_budget DOUBLE,
        volume_actual_tons DOUBLE,
        volume_budget_tons DOUBLE,
        net_variance DOUBLE
    );
    """)
    
    log_rows = []
    carriers = ['DHL Supply Chain', 'Kuehne+Nagel', 'DB Schenker', 'Maersk Logistics', 'FedEx Freight']
    routes = ['Frankfurt-Hamburg', 'Rotterdam-Munich', 'Paris-Berlin', 'Antwerp-Stuttgart', 'Lyon-Milan']
    
    log_counter = 5000
    for day in range(92): # July 1 to Sept 30
        ship_date = datetime(2026, 7, 1) + timedelta(days=day)
        for _ in range(3):
            log_counter += 1
            log_id = f"LOG_{log_counter}"
            reg = 'REG_EU_C' if random.random() < 0.6 else random.choice(['REG_EU_W', 'REG_NA_E'])
            route = random.choice(routes) if reg == 'REG_EU_C' else 'Cross-Border Primary'
            carrier = random.choice(carriers)
            
            vol_budget = round(random.uniform(50, 200), 1)
            vol_actual = round(vol_budget * random.uniform(0.95, 1.10), 1)
            
            fuel_budget = round(vol_budget * random.uniform(120, 150), 2)
            if reg == 'REG_EU_C':
                fuel_actual = round(fuel_budget * random.uniform(1.30, 1.55), 2) # Significant fuel surcharge overrun
            else:
                fuel_actual = round(fuel_budget * random.uniform(0.98, 1.05), 2)
                
            net_var = round(fuel_actual - fuel_budget, 2)
            log_rows.append((log_id, ship_date.strftime('%Y-%m-%d'), reg, route, carrier, fuel_actual, fuel_budget, vol_actual, vol_budget, net_var))
            
    conn.executemany("""
        INSERT INTO fact_logistics_q3 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, log_rows)
    
    print("Creating Analytical Views...")
    
    # 6. Analytical Views
    conn.execute("""
    CREATE VIEW vw_q3_variance_summary AS
    SELECT 
        r.region_name,
        cc.department,
        acc.account_name,
        SUM(f.budget_amount) AS total_budget,
        SUM(f.actual_amount) AS total_actual,
        SUM(f.variance_amount) AS total_variance,
        ROUND((SUM(f.variance_amount) / NULLIF(SUM(f.budget_amount), 0)) * 100, 2) AS variance_pct
    FROM fact_financial_transactions f
    JOIN dim_regions r ON f.region_id = r.region_id
    JOIN dim_cost_centers cc ON f.cost_center_id = cc.cost_center_id
    JOIN dim_accounts acc ON f.account_id = acc.account_id
    WHERE f.txn_date BETWEEN '2026-07-01' AND '2026-09-30'
    GROUP BY r.region_name, cc.department, acc.account_name;
    """)
    
    conn.execute("""
    CREATE VIEW vw_logistics_fuel_overruns AS
    SELECT 
        r.region_name,
        carrier,
        COUNT(*) AS shipment_count,
        SUM(fuel_surcharge_budget) AS budget_fuel,
        SUM(fuel_surcharge_actual) AS actual_fuel,
        SUM(net_variance) AS total_fuel_variance
    FROM fact_logistics_q3 l
    JOIN dim_regions r ON l.region_id = r.region_id
    GROUP BY r.region_name, carrier
    ORDER BY total_fuel_variance DESC;
    """)
    
    print("\nDatabase initialization complete! Summary Statistics:")
    print("--------------------------------------------------")
    print(f"dim_regions rows:              {conn.execute('SELECT COUNT(*) FROM dim_regions').fetchone()[0]}")
    print(f"dim_cost_centers rows:         {conn.execute('SELECT COUNT(*) FROM dim_cost_centers').fetchone()[0]}")
    print(f"dim_accounts rows:             {conn.execute('SELECT COUNT(*) FROM dim_accounts').fetchone()[0]}")
    print(f"fact_financial_transactions:   {conn.execute('SELECT COUNT(*) FROM fact_financial_transactions').fetchone()[0]}")
    print(f"fact_logistics_q3:             {conn.execute('SELECT COUNT(*) FROM fact_logistics_q3').fetchone()[0]}")
    print("\nSample View Output (vw_logistics_fuel_overruns):")
    print(conn.execute("SELECT * FROM vw_logistics_fuel_overruns LIMIT 5").fetchdf().to_string(index=False))
    
    conn.close()
    print("\nDuckDB database connection closed cleanly.")

if __name__ == "__main__":
    default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "controller_office.duckdb")
    db_file = os.getenv("DUCKDB_PATH", default_path)
    initialize_database(db_file)
