import asyncio
import json
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from .dlq_store import InMemoryDLQStore

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


class DLQDecisionRequest(BaseModel):
    decision: Literal["approve", "hold"]
    note: str | None = Field(default=None, max_length=500)


dlq_store = InMemoryDLQStore()

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


@app.get("/api/v1/dlq/events")
async def list_dlq_events():
    return [
        {
            "event_id": event["event_id"],
            "error_message": event["error_message"],
            "reason": event["reason"],
            "confidence": event["confidence"],
            "validation_status": event["validation_result"]["status"],
            "approval_status": event["approval_status"],
        }
        for event in dlq_store.list_events()
    ]


@app.get("/api/v1/dlq/events/{event_id}")
async def get_dlq_event(event_id: str):
    event = dlq_store.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="DLQ event not found")
    return event


@app.post("/api/v1/dlq/events/{event_id}/decision")
async def decide_dlq_event(event_id: str, payload: DLQDecisionRequest):
    event = dlq_store.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="DLQ event not found")
    if payload.decision == "approve" and event["approval_status"] != "pending":
        raise HTTPException(status_code=409, detail="Only pending events can be approved")

    updated_event = dlq_store.record_decision(event_id, payload.decision, payload.note)
    return updated_event


@app.post("/api/v1/dlq/events/{event_id}/reprocess")
async def reprocess_dlq_event(event_id: str):
    event = dlq_store.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="DLQ event not found")
    if event["approval_status"] != "approved":
        raise HTTPException(status_code=409, detail="Only approved events can be reprocessed")

    return dlq_store.reprocess_event(event_id)
