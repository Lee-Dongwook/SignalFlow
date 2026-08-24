import pytest
import json
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from apps.backend_api.main import app, stream_metrics

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "HEALTHY", "service": "backend_api"}

@pytest.mark.asyncio
async def test_stream_metrics_generator_logic():
    response = await stream_metrics()
    
    assert response.status_code == 200
    assert response.media_type == "text/event-stream"

    event_gen = response.body_iterator
    first_event = await event_gen.__anext__()

    assert first_event["event"] == "metric_update"
    
    payload = json.loads(first_event["data"])
    assert "tps" in payload
    assert "agent_healing_rate" in payload

def test_trigger_agent_self_healing_success():
    payload = {
        "event_id": "evt-9012",
        "target_agent": "SchemaAgent"
    }
    response = client.post("/api/v1/agents/heal", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["event_id"] == "evt-9012"
    assert data["assigned_agent"] == "SchemaAgent"

def test_trigger_agent_self_healing_validation_error():
    payload = {} 
    response = client.post("/api/v1/agents/heal", json=payload)
    assert response.status_code == 422 
