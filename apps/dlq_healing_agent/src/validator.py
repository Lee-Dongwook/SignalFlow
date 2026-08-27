from pydantic import ValidationError

from .models import (
    ApprovalStatus,
    RecoveryProposal,
    TelemetryEvent,
    ValidationResult,
    ValidationStatus,
)
from .state import DLQHealingState

MIN_APPROVAL_CONFIDENCE = 0.8


def validate_recovery(proposal: RecoveryProposal) -> ValidationResult:
    if not proposal.recoverable:
        return ValidationResult(status=ValidationStatus.NOT_APPLICABLE)

    if proposal.corrected_payload is None:
        return ValidationResult(
            status=ValidationStatus.INVALID,
            errors=["recoverable proposal requires corrected_payload"],
        )

    try:
        payload = TelemetryEvent.model_validate(proposal.corrected_payload)
    except ValidationError as error:
        errors = [
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors()
        ]
        return ValidationResult(status=ValidationStatus.INVALID, errors=errors)

    return ValidationResult(status=ValidationStatus.VALID, validated_payload=payload)


def determine_approval_status(result: ValidationResult, confidence: float) -> ApprovalStatus:
    if result.status is ValidationStatus.VALID and confidence >= MIN_APPROVAL_CONFIDENCE:
        return ApprovalStatus.PENDING
    return ApprovalStatus.ON_HOLD


def validator_node(state: DLQHealingState) -> DLQHealingState:
    proposal = RecoveryProposal.model_validate(state["recovery_proposal"])
    result = validate_recovery(proposal)
    approval_status = determine_approval_status(result, proposal.confidence)

    state["validation_result"] = result.model_dump(mode="json")
    state["approval_status"] = approval_status.value
    state["is_repaired"] = result.status is ValidationStatus.VALID
    state.setdefault("logs", []).append(
        f"Validator completed with {result.status.value}; approval is {approval_status.value}."
    )
    return state
