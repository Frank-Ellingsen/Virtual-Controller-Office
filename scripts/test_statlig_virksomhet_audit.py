import os
import duckdb

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "statlig_virksomhet.duckdb")

def run_statlig_virksomhet_audit():
    print(f"Connecting to '{DB_PATH}' for DFØ SRS Controlling Audit...")
    conn = duckdb.connect(DB_PATH, read_only=True)

    print("\n======================================================================")
    print("1. SUMMARY RESULTATREGNSKAP PER KONTOKLASSE (SRS)")
    print("======================================================================")
    res = conn.execute("""
        SELECT 
            a.Kontoklasse,
            ac.Kontoklassenavn,
            ROUND(SUM(gl.Belop), 2) AS Sum_Actual_NOK
        FROM factgl gl
        JOIN dimaccount a ON gl.Konto = a.Konto
        JOIN dimaccountclass ac ON a.Kontoklasse = ac.Kontoklasse
        GROUP BY a.Kontoklasse, ac.Kontoklassenavn
        ORDER BY a.Kontoklasse;
    """).fetchall()
    for row in res:
        print(f" Kontoklasse {row[0]} ({row[1]}): {row[2]:,.2f} NOK")

    print("\n======================================================================")
    print("2. BUDSJETTWAVVIK & PROGNOSE (BUDGET VS ACTUAL VS FORECAST LE)")
    print("======================================================================")
    v_res = conn.execute("""
        SELECT 
            o.Fakultetsnavn,
            ROUND(SUM(v.Actual_SRS), 2) AS Actuals,
            ROUND(SUM(v.Budget_SRS), 2) AS Budget,
            ROUND(SUM(v.Forecast_LE), 2) AS Forecast_LE,
            ROUND(SUM(v.Variance_Actual_vs_Budget), 2) AS Variance_Actual_vs_Bud,
            ROUND(SUM(v.Variance_Forecast_vs_Budget), 2) AS Variance_FC_vs_Bud
        FROM vw_budget_actual_forecast_variance v
        JOIN dimorganization o ON v.Organisasjonsnokkel = o.Organisasjonsnokkel
        GROUP BY o.Fakultetsnavn
        ORDER BY Variance_Actual_vs_Bud DESC;
    """).fetchall()
    print(f"{'Fakultet':<35} | {'Actuals (NOK)':<15} | {'Budget (NOK)':<15} | {'Forecast LE':<15} | {'Avvik Actual':<15}")
    print("-" * 105)
    for r in v_res:
        print(f"{r[0]:<35} | {r[1]:>15,.2f} | {r[2]:>15,.2f} | {r[3]:>15,.2f} | {r[4]:>15,.2f}")

    print("\n======================================================================")
    print("3. BOA PROSJEKTPORTEFØLJE & DEKNINGSGRAD (SRS 10)")
    print("======================================================================")
    boa_res = conn.execute("""
        SELECT 
            Prosjekt,
            Prosjektnavn,
            Finansieringskilde,
            Kontraktsbelop,
            Budsjett,
            Frikjop,
            DirekteDrift,
            Overhead,
            Dekningsgrad,
            Forbruksavvik,
            RAG_Status
        FROM vw_boa_project_summary;
    """).fetchall()
    print(f"{'Prosjekt':<10} | {'Prosjektnavn':<35} | {'Kilde':<15} | {'Kontrakt (NOK)':<15} | {'Dekningsgrad':<12} | {'RAG'}")
    print("-" * 105)
    for b in boa_res:
        print(f"{b[0]:<10} | {b[1]:<35} | {b[2]:<15} | {b[3]:>15,.0f} | {b[8]:>11.1f}% | {b[10]}")

    print("\n======================================================================")
    print("4. MÅNEDLIG AVVIK: SRS ENTERPRISE VS STATSKASSE BEVILGNING")
    print("======================================================================")
    rec_res = conn.execute("""
        SELECT 
            MndNr,
            Maaned,
            StatligBevilgning,
            TotalInntekt,
            TotalKostnad,
            NettoResultat
        FROM vw_yearly_reconciliation_summary
        ORDER BY MndNr;
    """).fetchall()
    print(f"{'Mnd':<4} | {'Måned':<12} | {'Bevilgning (NOK)':<20} | {'Tot. Inntekt':<18} | {'Tot. Kostnad':<18} | {'Netto Resultat'}")
    print("-" * 100)
    for rc in rec_res:
        print(f"{rc[0]:<4} | {rc[1]:<12} | {rc[2]:<20} | {rc[3]:<18} | {rc[4]:<18} | {rc[5]}")

    print("\n======================================================================")
    print("5. AKTIVE TILTAK OG INNSPARINGSETTIMATER (FactAction)")
    print("======================================================================")
    act_res = conn.execute("""
        SELECT 
            TiltakID,
            Fakultetsnavn,
            Prosjekt,
            Avviksarsak,
            Tiltaksbeskrivelse,
            AnsvarligRolle,
            ForventetEffekt,
            Status,
            Prioritet
        FROM vw_action_mitigation_tracker;
    """).fetchall()
    for act in act_res:
        print(f"[{act[0]}] {act[1]} - {act[2]}: {act[4]} (Ansvarlig: {act[5]}, Forventet: {act[6]:,} NOK, Status: {act[7]}, Prioritet: {act[8]})")

    conn.close()

if __name__ == "__main__":
    run_statlig_virksomhet_audit()
