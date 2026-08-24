from typing import TypedDict, Optional, Dict, Any, List

class DLQHealingState(TypedDict):
    raw_payload: Dict[str, Any]
    error_message: str
    next_agent: str
    corrected_payload: Optional[Dict[str, Any]]
    is_repaired: bool
    retry_count: int
    logs: List[str]
