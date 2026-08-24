import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="SignalFlow Backend Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def trigger_agent_self_healing(payload: dict):
    event_id = payload.get("event_id")
    return {
        "status": "SUCCESS",
        "event_id": event_id,
        "assigned_agent": "SchemaAgent",
        "message": f"Self-healing workflow executed for {event_id}"
    }
