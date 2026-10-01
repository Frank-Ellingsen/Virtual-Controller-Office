import os

from fastapi.testclient import TestClient

from server import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "online"
    assert payload["database_ready"] is True
    assert "active_thresholds_loaded" in payload


def test_thresholds_endpoint_returns_expected_keys():
    response = client.get("/api/thresholds")
    assert response.status_code == 200
    payload = response.json()
    thresholds = payload["thresholds"]
    assert "TH-03" in thresholds
    assert "TH-04" in thresholds
    assert thresholds["TH-03"]["parameter_name"] == "PVM Materiality Variance Alert"


def test_variance_endpoint_detects_overrun():
    response = client.post(
        "/api/audit/evaluate-variance",
        json={"actual_variance_usd": 240000.0, "fuel_rate_inc_pct": 34.3},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["variance_status"] == "OVERRUN_DETECTED"
    assert payload["alerts_count"] >= 2


def test_valid_select_query_executes():
    response = client.post(
        "/api/query/execute",
        json={
            "sql": "SELECT region_name, COUNT(*) AS shipment_count FROM fact_logistics_q3 l JOIN dim_regions r ON l.region_id = r.region_id GROUP BY region_name ORDER BY shipment_count DESC"
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] > 0
    assert "columns" in payload
    assert "rows" in payload


def test_invalid_write_query_is_rejected():
    response = client.post(
        "/api/query/execute",
        json={"sql": "DROP TABLE dim_regions;"},
    )
    assert response.status_code == 400
    assert "Security Violation" in response.json()["detail"]


def test_hitl_flow_completes_after_approval():
    submit_response = client.post(
        "/api/audit/submit",
        json={"prompt": "Audit Q3 logistics variance", "user_id": "controller_admin"},
    )
    assert submit_response.status_code == 200
    task = submit_response.json()
    assert task["status"] == "AWAITING_HITL_APPROVAL"
    task_id = task["task_id"]

    hitl_response = client.post(
        "/api/hitl/approve",
        json={"task_id": task_id, "approved": True, "feedback": "Approved for execution"},
    )
    assert hitl_response.status_code == 200
    payload = hitl_response.json()
    assert payload["status"] == "COMPLETED"

    latest_status = client.get(f"/api/audit/hitl/{task_id}")
    assert latest_status.status_code == 200
    assert latest_status.json()["status"] == "COMPLETED"


def test_business_creation_and_upload_flow():
    business_name = "Demo Audit Unit"
    create_response = client.post(
        "/api/businesses",
        json={"name": business_name, "description": "Test business", "category": "QA"},
    )
    assert create_response.status_code == 200
    business = create_response.json()
    assert business["name"] == business_name

    file_response = client.post(
        "/api/upload",
        data={"business_id": business["id"], "new_business_name": ""},
        files={"file": ("audit_summary.csv", b"ProjectID;Status\nP1;Active\n", "text/csv")},
    )
    assert file_response.status_code == 200
    payload = file_response.json()
    assert payload["status"] == "success"
    assert payload["filename"] == "audit_summary.csv"
