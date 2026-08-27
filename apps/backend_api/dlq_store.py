from copy import deepcopy
from typing import Any

SEED_EVENTS: list[dict[str, Any]] = [
    {
        "event_id": "evt-schema-001",
        "error_message": "timestamp must be an integer and category is required",
        "raw_payload": {
            "event_id": "evt-schema-001",
            "source": "mobile-app",
            "content": "checkout completed",
            "timestamp": "1722470400000",
        },
        "reason": "schema_error",
        "confidence": 0.95,
        "changes": [
            {
                "field": "timestamp",
                "before": "1722470400000",
                "after": 1722470400000,
                "reason": "numeric string conversion",
            },
            {
                "field": "category",
                "before": None,
                "after": "checkout",
                "reason": "trusted category context",
            },
        ],
        "corrected_payload": {
            "event_id": "evt-schema-001",
            "source": "mobile-app",
            "category": "checkout",
            "content": "checkout completed",
            "timestamp": 1722470400000,
        },
        "validation_result": {"status": "valid", "errors": []},
        "approval_status": "pending",
        "audit_logs": ["Supervisor classified schema_error.", "Validator returned valid."],
    },
    {
        "event_id": "evt-value-002",
        "error_message": "content is required and may not be empty",
        "raw_payload": {
            "event_id": "evt-value-002",
            "source": "web",
            "category": "support",
            "content": "",
            "timestamp": 1722470400000,
        },
        "reason": "missing_required_value",
        "confidence": 0.99,
        "changes": [],
        "corrected_payload": None,
        "validation_result": {"status": "not_applicable", "errors": []},
        "approval_status": "on_hold",
        "audit_logs": ["Supervisor classified missing_required_value.", "Event placed on hold."],
    },
    {
        "event_id": "evt-json-003",
        "error_message": "invalid JSON: unexpected end of input",
        "raw_payload": "{\"event_id\": \"evt-json-003\", \"source\":",
        "reason": "unrecoverable",
        "confidence": 1.0,
        "changes": [],
        "corrected_payload": None,
        "validation_result": {"status": "not_applicable", "errors": []},
        "approval_status": "on_hold",
        "audit_logs": ["Supervisor classified unrecoverable.", "Event placed on hold."],
    },
]


class InMemoryDLQStore:
    def __init__(self) -> None:
        self._events = {event["event_id"]: event for event in deepcopy(SEED_EVENTS)}

    def list_events(self) -> list[dict[str, Any]]:
        return list(self._events.values())

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        return self._events.get(event_id)

    def record_decision(
        self, event_id: str, decision: str, note: str | None
    ) -> dict[str, Any] | None:
        event = self.get_event(event_id)
        if event is None:
            return None

        if decision == "approve":
            event["approval_status"] = "approved"
            event["audit_logs"].append("Operator approved the event for reprocessing.")
        else:
            event["approval_status"] = "on_hold"
            event["audit_logs"].append(f"Operator placed the event on hold. {note or ''}".strip())
        return event

    def reprocess_event(self, event_id: str) -> dict[str, Any] | None:
        event = self.get_event(event_id)
        if event is None:
            return None

        event["approval_status"] = "reprocessed"
        event["reprocess_result"] = {
            "status": "simulated_success",
            "target": "raw-telemetry-stream",
        }
        event["audit_logs"].append("Approved payload was sent to the replay adapter.")
        return event
