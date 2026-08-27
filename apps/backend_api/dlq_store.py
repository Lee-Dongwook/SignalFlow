import json
import os
import sqlite3
from copy import deepcopy
from pathlib import Path
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
        "recovery_context": {"trusted_category": "checkout"},
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


class SQLiteDLQStore:
    def __init__(self, database_path: str | Path | None = None) -> None:
        default_path = Path(__file__).resolve().parents[2] / "data" / "signalflow.db"
        self.database_path = Path(database_path or os.getenv("SIGNALFLOW_DB_PATH", default_path))
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS dlq_events "
                "(event_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )
            event_count = connection.execute("SELECT COUNT(*) FROM dlq_events").fetchone()[0]
            if event_count == 0:
                connection.executemany(
                    "INSERT INTO dlq_events (event_id, payload) VALUES (?, ?)",
                    [(event["event_id"], json.dumps(event)) for event in deepcopy(SEED_EVENTS)],
                )

    def _save_event(self, event: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE dlq_events SET payload = ? WHERE event_id = ?",
                (json.dumps(event), event["event_id"]),
            )

    def reset(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM dlq_events")
            connection.executemany(
                "INSERT INTO dlq_events (event_id, payload) VALUES (?, ?)",
                [(event["event_id"], json.dumps(event)) for event in deepcopy(SEED_EVENTS)],
            )

    def list_events(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT payload FROM dlq_events ORDER BY event_id").fetchall()
        return [json.loads(row[0]) for row in rows]

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM dlq_events WHERE event_id = ?", (event_id,)
            ).fetchone()
        return json.loads(row[0]) if row else None

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
        self._save_event(event)
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
        self._save_event(event)
        return event

    def record_analysis(self, event: dict[str, Any]) -> dict[str, Any]:
        self._save_event(event)
        return event
