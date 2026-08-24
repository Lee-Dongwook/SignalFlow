import pytest
import json
from apps.backend_api.main import app, stream_metrics
from fastapi.testclient import TestClient

client = TestClient(app)
@pytest.mark.asyncio
async def test_dashboard_sse_payload_schema():
    response = await stream_metrics()
    assert response.status_code == 200

    event_gen = response.body_iterator
    first_event = await event_gen.__anext__()

    assert first_event["event"] == "metric_update"
    
    data_payload = json.loads(first_event["data"])
    assert "tps" in data_payload
    assert "clickhouse_latency" in data_payload
    assert "agent_healing_rate" in data_payload

def test_dashboard_agent_action_trigger():
    request_body = {
        "event_id": "dash-evt-8899",
        "target_agent": "DLQHealingAgent"
    }

    response = client.post("/api/v1/agents/heal", json=request_body)

    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "SUCCESS"
    assert res_json["event_id"] == "dash-evt-8899"
