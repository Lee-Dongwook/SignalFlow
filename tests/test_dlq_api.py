import pytest
from fastapi.testclient import TestClient

from apps.backend_api.main import app, dlq_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_dlq_store():
    dlq_store.reset()


def test_list_dlq_events_returns_review_summaries():
    response = client.get("/api/v1/dlq/events")

    assert response.status_code == 200
    assert len(response.json()) == 3
    schema_event = next(event for event in response.json() if event["event_id"] == "evt-schema-001")
    assert schema_event["approval_status"] == "pending"
    assert schema_event["analysis_status"] == "ready"
    assert schema_event["updated_at"]


def test_get_dlq_event_returns_payload_and_audit_log():
    response = client.get("/api/v1/dlq/events/evt-schema-001")

    assert response.status_code == 200
    event = response.json()
    assert event["corrected_payload"]["timestamp"] == 1722470400000
    assert event["audit_logs"]


def test_create_dlq_event_waits_for_analysis():
    response = client.post(
        "/api/v1/dlq/events",
        json={
            "event_id": "evt-created-001",
            "error_message": "category is required",
            "raw_payload": {"event_id": "evt-created-001"},
        },
    )

    assert response.status_code == 201
    event = response.json()
    assert event["approval_status"] == "pending_analysis"
    assert event["lifecycle"]["analysis_status"] == "pending"


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


def test_reprocess_approved_dlq_event_records_replay_result():
    approval_response = client.post(
        "/api/v1/dlq/events/evt-schema-001/decision",
        json={"decision": "approve"},
    )
    response = client.post("/api/v1/dlq/events/evt-schema-001/reprocess")

    assert approval_response.status_code == 200
    assert response.status_code == 200
    event = response.json()
    assert event["approval_status"] == "reprocessed"
    assert event["reprocess_result"]["status"] == "simulated_success"


def test_cannot_reprocess_event_that_was_not_approved():
    response = client.post("/api/v1/dlq/events/evt-value-002/reprocess")

    assert response.status_code == 409


def test_analysis_requires_openai_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post("/api/v1/dlq/events/evt-schema-001/analyze")

    assert response.status_code == 503
    assert response.json()["detail"] == "OPENAI_API_KEY is not configured"
