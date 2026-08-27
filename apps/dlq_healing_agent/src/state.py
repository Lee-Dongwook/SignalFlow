from typing import Any, TypedDict


class DLQHealingState(TypedDict, total=False):
    raw_payload: dict[str, Any] | str
    error_message: str
    recovery_context: dict[str, Any]
    next_agent: str
    reason: str
    confidence: float
    recovery_proposal: dict[str, Any]
    changes: list[dict[str, Any]]
    corrected_payload: dict[str, Any] | None
    validation_result: dict[str, Any]
    approval_status: str
    is_repaired: bool
    retry_count: int
    logs: list[str]
