import os
import duckdb
import sqlite3
import pytest
from scripts import file_processor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOCAL_DATA_DIR = os.path.join(BASE_DIR, "Local Data")


# =============================================================================
# 1. STATLIG VIRKSOMHET (DFØ SRS UNIVERSITY CONTROLLING MODEL)
# =============================================================================

@pytest.fixture(scope="module")
def statlig_db():
    db_path = os.path.join(DATA_DIR, "statlig_virksomhet.duckdb")
    assert os.path.exists(db_path), f"Statlig Virksomhet DB missing at {db_path}"
    conn = duckdb.connect(db_path, read_only=True)
    yield conn
    conn.close()


def test_statlig_dimension_primary_keys_unique(statlig_db):
    pk_checks = [
        ("dimaccount", "Konto"),
        ("dimaccountclass", "Kontoklasse"),
        ("dimdate", "DatoNokkel"),
        ("dimforecastversion", "Versjonsnokkel"),
        ("dimorganization", "Organisasjonsnokkel"),
        ("dimpositiongroup", "Stillingsgruppenokkel"),
        ("dimproject", "Prosjekt"),
        ("dimstudyprogram", "Studieprogramkode"),
    ]
    for table, pk in pk_checks:
        sql = f"SELECT count(DISTINCT {pk}) = count(*), count(*) FROM {table};"
        is_unique, total = statlig_db.execute(sql).fetchone()
        assert is_unique is True, f"Primary key {pk} in table {table} has duplicate values!"
        assert total > 0, f"Table {table} is empty!"


def test_statlig_factgl_referential_integrity(statlig_db):
    orphan_account = statlig_db.execute(
        "SELECT count(*) FROM factgl WHERE Konto NOT IN (SELECT Konto FROM dimaccount);"
    ).fetchone()[0]
    orphan_org = statlig_db.execute(
        "SELECT count(*) FROM factgl WHERE Organisasjonsnokkel NOT IN (SELECT Organisasjonsnokkel FROM dimorganization);"
    ).fetchone()[0]
    orphan_date = statlig_db.execute(
        "SELECT count(*) FROM factgl WHERE DatoNokkel NOT IN (SELECT DatoNokkel FROM dimdate);"
    ).fetchone()[0]

    assert orphan_account == 0, f"Found {orphan_account} orphan accounts in factgl"
    assert orphan_org == 0, f"Found {orphan_org} orphan org keys in factgl"
    assert orphan_date == 0, f"Found {orphan_date} orphan date keys in factgl"


def test_statlig_budget_and_forecast_integrity(statlig_db):
    b_orphan_acc = statlig_db.execute(
        "SELECT count(*) FROM factbudget WHERE Konto NOT IN (SELECT Konto FROM dimaccount);"
    ).fetchone()[0]
    f_orphan_acc = statlig_db.execute(
        "SELECT count(*) FROM factforecast WHERE Konto NOT IN (SELECT Konto FROM dimaccount);"
    ).fetchone()[0]

    assert b_orphan_acc == 0
    assert f_orphan_acc == 0

    total_budget = statlig_db.execute("SELECT sum(BudsjettBelop) FROM factbudget;").fetchone()[0]
    total_forecast = statlig_db.execute("SELECT sum(ForecastBelop) FROM factforecast;").fetchone()[0]
    assert total_budget != 0
    assert total_forecast != 0


def test_statlig_srs_views_operational(statlig_db):
    # Verify SRS P&L view
    res = statlig_db.execute("SELECT count(*), sum(Belop_Actual) FROM vw_srs_resultat;").fetchone()
    assert res[0] > 0
    assert res[1] is not None

    # Verify Budget vs Actual variance view
    var_res = statlig_db.execute(
        "SELECT count(*), sum(Actual_SRS), sum(Budget_SRS) FROM vw_budget_actual_forecast_variance;"
    ).fetchone()
    assert var_res[0] > 0
    assert var_res[1] is not None
    assert var_res[2] is not None

    # Verify BOA Project summary view
    boa_res = statlig_db.execute("SELECT count(*), min(Dekningsgrad), max(Dekningsgrad) FROM vw_boa_project_summary;").fetchone()
    assert boa_res[0] == 6  # 6 external projects
    assert boa_res[1] >= 0.0

    # Verify Yearly Reconciliation view covers all 12 periods
    rec_res = statlig_db.execute("SELECT count(DISTINCT MndNr) FROM vw_yearly_reconciliation_summary;").fetchone()[0]
    assert rec_res == 12


# =============================================================================
# 2. HYDRO POWER (POWER MARKET BACKOFFICE & PRODUCTION CONTROLLING)
# =============================================================================

@pytest.fixture(scope="module")
def hydro_db():
    db_path = os.path.join(LOCAL_DATA_DIR, "Hydro Power", "power_market_backoffice.duckdb")
    assert os.path.exists(db_path), f"Hydro Power DB missing at {db_path}"
    conn = duckdb.connect(db_path, read_only=True)
    yield conn
    conn.close()


def test_hydro_power_dimension_and_fact_counts(hydro_db):
    plants = hydro_db.execute("SELECT count(*) FROM dim_plant;").fetchone()[0]
    aggr = hydro_db.execute("SELECT count(*) FROM dim_aggregate;").fetchone()[0]
    prod = hydro_db.execute("SELECT count(*) FROM fact_production;").fetchone()[0]
    imb = hydro_db.execute("SELECT count(*) FROM fact_imbalance;").fetchone()[0]
    rep = hydro_db.execute("SELECT count(*) FROM fact_reporting;").fetchone()[0]

    assert plants == 5, f"Expected 5 plants, got {plants}"
    assert aggr == 10, f"Expected 10 aggregates, got {aggr}"
    assert prod == 87600, f"Expected 87,600 hourly production rows (10 aggr * 8760 h), got {prod}"
    assert imb == 1825, f"Expected 1,825 imbalance rows (5 plants * 365 d), got {imb}"
    assert rep == 1825, f"Expected 1,825 reporting rows, got {rep}"


def test_hydro_power_referential_integrity(hydro_db):
    orphan_aggr = hydro_db.execute("SELECT count(*) FROM dim_aggregate WHERE PlantID NOT IN (SELECT PlantID FROM dim_plant);").fetchone()[0]
    orphan_prod = hydro_db.execute("SELECT count(*) FROM fact_production WHERE PlantID NOT IN (SELECT PlantID FROM dim_plant);").fetchone()[0]
    orphan_imb = hydro_db.execute("SELECT count(*) FROM fact_imbalance WHERE PlantID NOT IN (SELECT PlantID FROM dim_plant);").fetchone()[0]

    assert orphan_aggr == 0
    assert orphan_prod == 0
    assert orphan_imb == 0


def test_hydro_power_physical_capacity_and_conservation(hydro_db):
    # Total aggregate output capacity vs plant installed capacity
    cap_diff = hydro_db.execute("""
        SELECT sum(abs(p.InstalledCapacity_MW - a.TotalAggr_MW))
        FROM dim_plant p
        JOIN (SELECT PlantID, sum(MaxOutput_MW) as TotalAggr_MW FROM dim_aggregate GROUP BY PlantID) a
        ON p.PlantID = a.PlantID;
    """).fetchone()[0]
    assert cap_diff < 0.01, "Discrepancy between plant installed capacity and aggregate capacity!"

    # Production volume conservation: sum of aggregates vs plant reported total
    prod_vs_rep = hydro_db.execute("""
        SELECT 
            sum(p.Sum_Measured),
            sum(r.Sum_Reported),
            abs(sum(p.Sum_Measured) - sum(r.Sum_Reported)) / sum(r.Sum_Reported) * 100.0 as Diff_Pct
        FROM (
            SELECT PlantID, sum(Measured_MWh) as Sum_Measured 
            FROM fact_production 
            GROUP BY PlantID
        ) p
        JOIN (
            SELECT PlantID, sum(Reported_MWh) as Sum_Reported 
            FROM fact_reporting 
            GROUP BY PlantID
        ) r ON p.PlantID = r.PlantID;
    """).fetchone()

    measured_sum, reported_sum, diff_pct = prod_vs_rep
    assert measured_sum > 0
    assert reported_sum > 0
    assert diff_pct < 0.2, f"Production conservation variance is too high: {diff_pct:.4f}%"


def test_hydro_power_sqlite_duckdb_parity():
    duck_p = os.path.join(LOCAL_DATA_DIR, "Hydro Power", "power_market_backoffice.duckdb")
    sql_p = os.path.join(LOCAL_DATA_DIR, "Hydro Power", "power_market_backoffice.sqlite")

    assert os.path.exists(duck_p)
    assert os.path.exists(sql_p)

    duck_conn = duckdb.connect(duck_p, read_only=True)
    sql_conn = sqlite3.connect(sql_p)
    cursor = sql_conn.cursor()

    tables = ["dim_plant", "dim_aggregate", "dim_time", "fact_production", "fact_predictions", "fact_imbalance", "fact_reporting"]
    for t in tables:
        duck_cnt = duck_conn.execute(f"SELECT count(*) FROM {t};").fetchone()[0]
        cursor.execute(f"SELECT count(*) FROM {t};")
        sql_cnt = cursor.fetchone()[0]
        assert duck_cnt == sql_cnt, f"Parity mismatch in {t}: DuckDB={duck_cnt}, SQLite={sql_cnt}"

    duck_conn.close()
    sql_conn.close()


# =============================================================================
# 3. BANK DATASET (CREDIT CARD, LOAN DEFAULT, INCOME)
# =============================================================================

@pytest.fixture(scope="module")
def bank_db():
    db_path = os.path.join(DATA_DIR, "bank.duckdb")
    assert os.path.exists(db_path), f"Bank DB missing at {db_path}"
    conn = duckdb.connect(db_path, read_only=True)
    yield conn
    conn.close()


def test_bank_creditcard_fraud_distribution(bank_db):
    total, fraud_cnt, fraud_rate = bank_db.execute("""
        SELECT count(*), sum(Class), round(sum(Class)*100.0/count(*), 4) 
        FROM tbl_creditcard;
    """).fetchone()

    assert total == 284807, f"Unexpected creditcard row count: {total}"
    assert fraud_cnt == 492, f"Expected 492 fraud cases, got {fraud_cnt}"
    assert fraud_rate == 0.1728 or round(fraud_rate, 3) == 0.173


def test_bank_loan_default_portfolio(bank_db):
    res = bank_db.execute("""
        SELECT count(*), count(DISTINCT ID), sum(Status), min(Loan_Limit)
        FROM tbl_loan_default;
    """).fetchone()

    total, distinct_ids, default_cnt, min_limit = res
    assert total == 148670
    assert total == distinct_ids, "Duplicate loan IDs detected!"
    assert default_cnt > 0
    assert default_cnt < total
    assert min_limit is not None


def test_bank_income_datasets_consistency(bank_db):
    raw_rows = bank_db.execute("SELECT count(*) FROM tbl_income;").fetchone()[0]
    clean_rows = bank_db.execute("SELECT count(*) FROM tbl_income_clean;").fetchone()[0]

    assert raw_rows == 31978
    assert clean_rows == 28516
    assert clean_rows < raw_rows  # Clean dataset filtered invalid/duplicate entries

    # Check clean bounds
    clean_stats = bank_db.execute("""
        SELECT min(age), max(age), min(hoursperweek), max(hoursperweek), sum(salstat)
        FROM tbl_income_clean;
    """).fetchone()

    min_age, max_age, min_hours, max_hours, high_sal_count = clean_stats
    assert min_age >= 17
    assert max_age <= 90
    assert min_hours >= 1
    assert max_hours <= 100
    assert high_sal_count > 0


# =============================================================================
# 4. TIME SERIES & AIR TRAFFIC
# =============================================================================

def test_air_passengers_continuity_and_ranges():
    db_path = os.path.join(DATA_DIR, "air_traffic.duckdb")
    conn = duckdb.connect(db_path, read_only=True)

    rows, min_p, max_p, avg_p = conn.execute("""
        SELECT count(*), min("Passengers (k)"), max("Passengers (k)"), avg("Passengers (k)")
        FROM tbl_airpassengers;
    """).fetchone()
    conn.close()

    assert rows == 144, f"Expected 144 monthly records, got {rows}"
    assert min_p > 0
    assert max_p > min_p
    assert 200 < avg_p < 400


def test_time_series_metrics_and_boundaries():
    db_path = os.path.join(DATA_DIR, "time_series.duckdb")
    conn = duckdb.connect(db_path, read_only=True)

    # Madrid weather check
    madrid_cnt, min_temp, max_temp = conn.execute("""
        SELECT count(*), min(temperature), max(temperature)
        FROM tbl_madrid_weather;
    """).fetchone()
    assert madrid_cnt == 27024
    assert -15.0 < min_temp < 10.0
    assert 30.0 < max_temp < 50.0

    # Power consumption check
    pwr_cnt, min_z1, max_z1 = conn.execute("""
        SELECT count(*), min(PowerConsumption_Zone1), max(PowerConsumption_Zone1)
        FROM tbl_powerconsumption;
    """).fetchone()
    assert pwr_cnt == 52416
    assert min_z1 >= 0.0
    assert max_z1 > 10000.0

    # Taco stands
    taco_cnt = conn.execute("SELECT count(*) FROM tbl_taco_stands;").fetchone()[0]
    assert taco_cnt == 240

    conn.close()


# =============================================================================
# 5. LOCAL DATA REGISTRY & MULTI-BUSINESS DISCOVERY
# =============================================================================

def test_all_local_data_directories_discovered_and_initialized():
    discovered = file_processor.discover_local_data_dirs()
    discovered_ids = {d["id"] for d in discovered}

    expected_ids = {"air_traffic", "bank", "hydro_power", "ratings", "statlig_virksomhet", "time_series"}
    assert expected_ids.issubset(discovered_ids), f"Missing local directories: {expected_ids - discovered_ids}"

    businesses = file_processor.list_all_businesses()
    biz_map = {b["id"]: b for b in businesses}

    # Populated business folders must have ready databases
    for bid in ["air_traffic", "bank", "hydro_power", "statlig_virksomhet", "time_series"]:
        assert bid in biz_map, f"Business {bid} not in registry!"
        assert biz_map[bid]["db_exists"] is True, f"DB for {bid} does not exist!"
        assert biz_map[bid]["table_count"] > 0, f"DB for {bid} has no tables!"

    # Empty folder (Ratings) handled gracefully without failure
    assert "ratings" in biz_map
    assert biz_map["ratings"]["db_exists"] is True
