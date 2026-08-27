import asyncio
import json
import os
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from .dlq_store import SQLiteDLQStore

app = FastAPI(title="SignalFlow Backend Control API", version="1.0.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("SIGNALFLOW_ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials="*" not in allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealRequest(BaseModel):
    event_id: str
    target_agent: str = "SupervisorAgent"


class DLQDecisionRequest(BaseModel):
    decision: Literal["approve", "hold"]
    note: str | None = Field(default=None, max_length=500)


class DLQEventCreateRequest(BaseModel):
    error_message: str = Field(min_length=1, max_length=2000)
    raw_payload: dict | str
    recovery_context: dict = Field(default_factory=dict)
    event_id: str | None = Field(default=None, min_length=1, max_length=100)


dlq_store = SQLiteDLQStore()

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
            "analysis_status": event.get("lifecycle", {}).get("analysis_status", "ready"),
            "updated_at": event.get("lifecycle", {}).get("updated_at", ""),
        }
        for event in dlq_store.list_events()
    ]


@app.post("/api/v1/dlq/events", status_code=201)
async def create_dlq_event(payload: DLQEventCreateRequest):
    event_id = payload.event_id or f"evt-{uuid4().hex[:12]}"
    event = {
        "event_id": event_id,
        "error_message": payload.error_message,
        "raw_payload": payload.raw_payload,
        "recovery_context": payload.recovery_context,
        "reason": "unclassified",
        "confidence": 0,
        "changes": [],
        "corrected_payload": None,
        "validation_result": {"status": "pending", "errors": []},
        "approval_status": "pending_analysis",
        "rationale": "",
        "risk_reason": "",
        "audit_logs": ["DLQ event was created and is waiting for analysis."],
        "lifecycle": {"analysis_status": "pending"},
    }
    try:
        return dlq_store.create_event(event)
    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            raise HTTPException(status_code=409, detail="DLQ event already exists") from error
        raise


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


@app.post("/api/v1/dlq/events/{event_id}/analyze")
async def analyze_dlq_event(event_id: str):
    event = dlq_store.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="DLQ event not found")
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")

    from apps.dlq_healing_agent.src.graph import build_dlq_healing_graph

    try:
        result = build_dlq_healing_graph().invoke(
            {
                "raw_payload": event["raw_payload"],
                "error_message": event["error_message"],
                "recovery_context": event.get("recovery_context", {}),
                "logs": [],
            }
        )
    except Exception as error:
        dlq_store.record_analysis_failure(event_id, str(error)[:200])
        raise HTTPException(
            status_code=502,
            detail="AI analysis failed. The stored review data was kept unchanged.",
        ) from error

    proposal = result.get("recovery_proposal", {})
    event["reason"] = result["reason"]
    event["confidence"] = result["confidence"]
    event["changes"] = result["changes"]
    event["corrected_payload"] = result.get("corrected_payload")
    event["validation_result"] = result["validation_result"]
    event["approval_status"] = result["approval_status"]
    event["rationale"] = proposal.get("rationale", "")
    event["risk_reason"] = proposal.get("risk_reason", "")
    event["audit_logs"].extend(result["logs"])
    return dlq_store.record_analysis(event)


@app.post("/api/v1/dlq/events/{event_id}/reprocess")
async def reprocess_dlq_event(event_id: str):
    event = dlq_store.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="DLQ event not found")
    if event["approval_status"] != "approved":
        raise HTTPException(status_code=409, detail="Only approved events can be reprocessed")

    return dlq_store.reprocess_event(event_id)
