import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
import file_processor

def test_file_ingestion():
    print("Testing File Processor & Business Discovery...")
    
    # 1. List Businesses
    businesses = file_processor.list_all_businesses()
    print(f"Found {len(businesses)} businesses:")
    for b in businesses:
        print(f" - {b['name']} ({b['id']}): {b['table_count']} tables, DB exists: {b['db_exists']}")

    # 2. Test uploading a sample CSV file to 'statlig_virksomhet'
    sample_csv_content = """ProjectID;ProjectName;BudgetNOK;Status
P101;Subsea Composite Hull Research;5000000;Active
P102;Autonomous Vessel Navigation;8500000;Active
P103;DFO SRS Accounting Automation;1200000;Completed
""".encode("utf-8")

    print("\nTesting file upload into 'statlig_virksomhet'...")
    res1 = file_processor.process_file_upload(sample_csv_content, "ProjectResearchIndex.csv", "statlig_virksomhet")
    print("Ingestion Result:", json.dumps(res1, indent=2))

    # 3. Test uploading a text document knowledge item into a new business 'umoe_mandal'
    doc_content = """# Project Controlling Manual - Umoe Mandal Defense
This document governs Earned Value Management (EVM), EAC forecasting, and risk tracking for fast craft vessels.
All cost overruns exceeding 5% require immediate HITL supervisor gate review.
""".encode("utf-8")

    print("\nTesting file upload into new business 'umoe_mandal'...")
    res2 = file_processor.process_file_upload(doc_content, "Project_Controlling_Manual.md", "Umoe Mandal Defense")
    print("Ingestion Result:", json.dumps(res2, indent=2))

    # 4. Verify businesses after upload
    businesses_after = file_processor.list_all_businesses()
    print(f"\nFound {len(businesses_after)} businesses after dynamic ingestion:")
    for b in businesses_after:
        print(f" - {b['name']} ({b['id']}): {b['table_count']} tables, {b['doc_count']} docs")

if __name__ == "__main__":
    test_file_ingestion()
