from fastapi.testclient import TestClient

from apps.backend_api.main import app

client = TestClient(app)


def test_list_dlq_events_returns_review_summaries():
    response = client.get("/api/v1/dlq/events")

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0]["approval_status"] == "pending"


def test_get_dlq_event_returns_payload_and_audit_log():
    response = client.get("/api/v1/dlq/events/evt-schema-001")

    assert response.status_code == 200
    event = response.json()
    assert event["corrected_payload"]["timestamp"] == 1722470400000
    assert event["audit_logs"]


def test_approve_pending_dlq_event_records_operator_decision():
    response = client.post(
        "/api/v1/dlq/events/evt-schema-001/decision",
        json={"decision": "approve"},
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "approved"
    assert "Operator approved" in response.json()["audit_logs"][-1]


def test_cannot_approve_event_on_hold():
    response = client.post(
        "/api/v1/dlq/events/evt-value-002/decision",
        json={"decision": "approve"},
    )

    assert response.status_code == 409
