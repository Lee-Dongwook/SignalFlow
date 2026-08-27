import json
from pathlib import Path

import pytest

from apps.dlq_healing_agent.src.models import RecoveryProposal, ValidationStatus
from apps.dlq_healing_agent.src.validator import validate_recovery

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "dlq"


@pytest.mark.parametrize("fixture_name", ["schema_repair", "missing_content", "unrecoverable_json"])
def test_fixture_proposals_have_expected_validation_status(fixture_name: str):
    fixture_path = FIXTURE_DIR / f"{fixture_name}.json"
    fixture = json.loads(fixture_path.read_text())

    proposal = RecoveryProposal.model_validate(fixture["proposal"])
    result = validate_recovery(proposal)

    assert result.status.value == fixture["expected_validation_status"]


def test_validator_rejects_empty_required_content():
    proposal = RecoveryProposal(
        reason="schema_error",
        rationale="The payload appears repairable.",
        confidence=0.9,
        recoverable=True,
        corrected_payload={
            "event_id": "evt-invalid-001",
            "source": "web",
            "category": "support",
            "content": "",
            "timestamp": 1722470400000,
        },
        risk_reason="Operator review is required.",
    )

    result = validate_recovery(proposal)

    assert result.status is ValidationStatus.INVALID
    assert result.validated_payload is None
    assert any("content" in error for error in result.errors)
