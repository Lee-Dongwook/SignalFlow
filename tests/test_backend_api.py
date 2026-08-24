import pytest
from fastapi.testclient import TestClient
from apps.backend_api.main import app

client = TestClient(app)

def test_stream_metrics_endpoint():
    response = client.get("/api/v1/stream/metrics")
    
    # Then: 헤더 및 응답 타입 검증
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
