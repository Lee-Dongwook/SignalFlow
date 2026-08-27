from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr


class FailureReason(str, Enum):
    SCHEMA_ERROR = "schema_error"
    MISSING_REQUIRED_VALUE = "missing_required_value"
    UNRECOVERABLE = "unrecoverable"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ON_HOLD = "on_hold"
    REPROCESSED = "reprocessed"


class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    NOT_APPLICABLE = "not_applicable"


class TelemetryEvent(BaseModel):
    """재처리 토픽에 보낼 수 있는 최소 이벤트 스키마."""

    model_config = ConfigDict(extra="forbid", strict=True)

    event_id: StrictStr = Field(min_length=1)
    source: StrictStr = Field(min_length=1)
    category: StrictStr = Field(min_length=1)
    content: StrictStr = Field(min_length=1)
    timestamp: StrictInt = Field(ge=0)


class RecoveryChange(BaseModel):
    field: str
    before: Any = None
    after: Any = None
    reason: str = Field(min_length=1)


class RecoveryProposal(BaseModel):
    """LLM이 생성하는 구조화된 분석 및 복구 제안."""

    model_config = ConfigDict(extra="forbid")

    reason: FailureReason
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    recoverable: bool
    corrected_payload: dict[str, Any] | None = None
    changes: list[RecoveryChange] = Field(default_factory=list)
    risk_reason: str = Field(min_length=1)


class ValidationResult(BaseModel):
    status: ValidationStatus
    errors: list[str] = Field(default_factory=list)
    validated_payload: TelemetryEvent | None = None
