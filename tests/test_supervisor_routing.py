from apps.dlq_healing_agent.src.agents.supervisor import route_proposal
from apps.dlq_healing_agent.src.models import RecoveryProposal


def test_recoverable_schema_error_routes_to_schema_agent():
    proposal = RecoveryProposal(
        reason="schema_error",
        rationale="The value can be recovered from trusted context.",
        confidence=0.95,
        recoverable=True,
        corrected_payload={},
        risk_reason="Operator approval is required.",
    )

    assert route_proposal(proposal) == "schema_agent"


def test_missing_required_value_routes_to_finish():
    proposal = RecoveryProposal(
        reason="missing_required_value",
        rationale="The original event does not contain content.",
        confidence=0.99,
        recoverable=False,
        risk_reason="Inventing content is unsafe.",
    )

    assert route_proposal(proposal) == "FINISH"
