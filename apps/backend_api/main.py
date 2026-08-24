import asyncio
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="SignalFlow Backend Control API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealRequest(BaseModel):
    event_id: str
    target_agent: str = "SupervisorAgent"

@app.get("/health")
async def health_check():
    return {"status": "HEALTHY", "service": "backend_api"}

@app.get("/api/v1/stream/metrics")
async def stream_metrics():
    async def event_generator():
        while True:
            metric_data = {
                "tps": 2340,
                "clickhouse_latency": 8.2,
                "agent_healing_rate": 99.4,
                "iceberg_storage_tb": 1.2
            }
            yield {
                "event": "metric_update",
                "data": json.dumps(metric_data)
            }
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())


@app.post("/api/v1/agents/heal")
async def trigger_agent_self_healing(payload: HealRequest):
    if not payload.event_id:
        raise HTTPException(status_code=400, detail="event_id is required")

    return {
        "status": "SUCCESS",
        "event_id": payload.event_id,
        "assigned_agent": "SchemaAgent",
        "message": f"Self-healing workflow executed for {payload.event_id}"
    }
