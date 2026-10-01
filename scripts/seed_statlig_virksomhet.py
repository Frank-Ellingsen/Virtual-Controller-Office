import os
import glob
import duckdb

DATA_DIR = r"C:\Users\frank\Desktop\Virtual Controller Office\Local Data\Statlig Virksomhet"
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "statlig_virksomhet.duckdb")

def seed_statlig_virksomhet():
    print(f"Initializing DuckDB database at '{DB_PATH}'...")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = duckdb.connect(DB_PATH)

    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    print(f"Found {len(csv_files)} CSV files in {DATA_DIR}.")

    for csv_file in sorted(csv_files):
        filename = os.path.basename(csv_file)
        table_name = os.path.splitext(filename)[0].lower()
        print(f"Ingesting '{filename}' into table '{table_name}'...")
        
        conn.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.execute(f"""
            CREATE TABLE {table_name} AS 
            SELECT * FROM read_csv_auto('{csv_file.replace('\\', '/')}', delim=';', header=True);
        """)

    print("\nCreating Analytical Views for DFØ SRS Controlling...")

    # 1. View for SRS Income Statement (Resultatregnskap)
    conn.execute("DROP VIEW IF EXISTS vw_srs_resultat;")
    conn.execute("""
        CREATE VIEW vw_srs_resultat AS
        SELECT 
            gl.DatoNokkel,
            d.Aar,
            d.MaanedNr,
            d.AarMaaned,
            o.Fakultetsnavn,
            o.Instituttnavn,
            a.Kontoklasse,
            a.Kontonavn,
            a.SRS_regnskapslinje,
            gl.Prosjekt,
            SUM(gl.Belop) AS Belop_Actual
        FROM factgl gl
        LEFT JOIN dimdate d ON gl.DatoNokkel = d.DatoNokkel
        LEFT JOIN dimorganization o ON gl.Organisasjonsnokkel = o.Organisasjonsnokkel
        LEFT JOIN dimaccount a ON gl.Konto = a.Konto
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10;
    """)

    # 2. View for Budget vs Actuals vs Forecast Variance
    conn.execute("DROP VIEW IF EXISTS vw_budget_actual_forecast_variance;")
    conn.execute("""
        CREATE VIEW vw_budget_actual_forecast_variance AS
        SELECT 
            COALESCE(gl.DatoNokkel, b.DatoNokkel, f.DatoNokkel) AS DatoNokkel,
            COALESCE(gl.Organisasjonsnokkel, b.Organisasjonsnokkel, f.Organisasjonsnokkel) AS Organisasjonsnokkel,
            COALESCE(gl.Konto, b.Konto, f.Konto) AS Konto,
            COALESCE(gl.Prosjekt, b.Prosjekt, f.Prosjekt) AS Prosjekt,
            SUM(COALESCE(gl.Belop, 0)) AS Actual_SRS,
            SUM(COALESCE(b.BudsjettBelop, 0)) AS Budget_SRS,
            SUM(COALESCE(f.ForecastBelop, 0)) AS Forecast_LE,
            SUM(COALESCE(gl.Belop, 0)) - SUM(COALESCE(b.BudsjettBelop, 0)) AS Variance_Actual_vs_Budget,
            SUM(COALESCE(f.ForecastBelop, 0)) - SUM(COALESCE(b.BudsjettBelop, 0)) AS Variance_Forecast_vs_Budget
        FROM factgl gl
        FULL OUTER JOIN factbudget b 
            ON gl.DatoNokkel = b.DatoNokkel 
            AND gl.Organisasjonsnokkel = b.Organisasjonsnokkel 
            AND gl.Konto = b.Konto 
            AND gl.Prosjekt = b.Prosjekt
        FULL OUTER JOIN factforecast f 
            ON COALESCE(gl.DatoNokkel, b.DatoNokkel) = f.DatoNokkel 
            AND COALESCE(gl.Organisasjonsnokkel, b.Organisasjonsnokkel) = f.Organisasjonsnokkel 
            AND COALESCE(gl.Konto, b.Konto) = f.Konto 
            AND COALESCE(gl.Prosjekt, b.Prosjekt) = f.Prosjekt
        GROUP BY 1, 2, 3, 4;
    """)

    # 3. View for BOA (Bidrags- og oppdragsaktivitet) Project Portfolio Overview
    conn.execute("DROP VIEW IF EXISTS vw_boa_project_summary;")
    conn.execute("""
        CREATE VIEW vw_boa_project_summary AS
        SELECT 
            Prosjekt,
            Prosjektnavn,
            Finansieringstype,
            Finansieringskilde,
            Kontraktsbelop,
            Budsjett,
            Frikjop,
            DirekteDrift,
            Overhead,
            Dekningsgrad,
            Forbruksavvik,
            RAG_Status,
            StatusMerknad
        FROM factprojectboa;
    """)

    # 4. View for Monthly Enterprise (SRS) vs Earned Value / Reconciliation
    conn.execute("DROP VIEW IF EXISTS vw_yearly_reconciliation_summary;")
    conn.execute("""
        CREATE VIEW vw_yearly_reconciliation_summary AS
        SELECT 
            MndNr,
            Maaned,
            StatligBevilgning,
            Forskningsinntekter,
            AndreInntekter,
            Lonnskostnader,
            Driftskostnader,
            InvesteringerCapex,
            TotalInntekt,
            TotalKostnad,
            NettoResultat
        FROM factyearlyreconciliation;
    """)

    # 5. View for Action Mitigation Tracker
    conn.execute("DROP VIEW IF EXISTS vw_action_mitigation_tracker;")
    conn.execute("""
        CREATE VIEW vw_action_mitigation_tracker AS
        SELECT 
            act.TiltakID,
            act.Organisasjonsnokkel,
            o.Fakultetsnavn,
            o.Instituttnavn,
            act.Prosjekt,
            act.Konto,
            act.Avviksarsak,
            act.Tiltaksbeskrivelse,
            act.AnsvarligRolle,
            act.StartDatoNokkel,
            act.FristDatoNokkel,
            act.ForventetEffekt,
            act.RealisertEffekt,
            act.Status,
            act.Prioritet
        FROM factaction act
        LEFT JOIN dimorganization o ON act.Organisasjonsnokkel = o.Organisasjonsnokkel;
    """)

    print("Checking Table Row Counts...")
    tables = conn.execute("SHOW TABLES;").fetchall()
    for (t,) in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
        print(f" - Table/View '{t}': {count} rows")

    conn.close()
    print(f"\nSuccessfully seeded '{DB_PATH}'!")

if __name__ == "__main__":
    seed_statlig_virksomhet()
