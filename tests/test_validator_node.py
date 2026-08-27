import json
from pathlib import Path

from apps.dlq_healing_agent.src.models import ApprovalStatus, ValidationStatus
from apps.dlq_healing_agent.src.validator import validator_node

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "dlq"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text())


def test_validator_node_sets_pending_approval_for_valid_recovery():
    fixture = load_fixture("schema_repair")
    state = validator_node({"recovery_proposal": fixture["proposal"], "logs": []})

    assert state["validation_result"]["status"] == ValidationStatus.VALID.value
    assert state["approval_status"] == ApprovalStatus.PENDING.value
    assert state["is_repaired"] is True


def test_validator_node_holds_unrecoverable_event():
    fixture = load_fixture("unrecoverable_json")
    state = validator_node({"recovery_proposal": fixture["proposal"], "logs": []})

    assert state["validation_result"]["status"] == ValidationStatus.NOT_APPLICABLE.value
    assert state["approval_status"] == ApprovalStatus.ON_HOLD.value
    assert state["is_repaired"] is False
