from pydantic import ValidationError

from .models import RecoveryProposal, TelemetryEvent, ValidationResult, ValidationStatus


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
