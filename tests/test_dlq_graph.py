import json
from pathlib import Path

import pytest

from apps.dlq_healing_agent.src import graph
from apps.dlq_healing_agent.src.models import ApprovalStatus, ValidationStatus

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "dlq"


@pytest.mark.parametrize("fixture_name", ["missing_content", "unrecoverable_json"])
def test_non_recoverable_event_is_validated_and_held(monkeypatch, fixture_name: str):
    fixture = json.loads((FIXTURE_DIR / f"{fixture_name}.json").read_text())

    def supervisor_stub(state: dict) -> dict:
        return {
            **state,
            "next_agent": "FINISH",
            "recovery_proposal": fixture["proposal"],
            "logs": [],
        }

    monkeypatch.setattr(graph, "supervisor_node", supervisor_stub)
    workflow = graph.build_dlq_healing_graph()
    result = workflow.invoke(
        {
            "raw_payload": fixture["raw_payload"],
            "error_message": fixture["error_message"],
            "logs": [],
        }
    )

    assert result["validation_result"]["status"] == ValidationStatus.NOT_APPLICABLE.value
    assert result["approval_status"] == ApprovalStatus.ON_HOLD.value
