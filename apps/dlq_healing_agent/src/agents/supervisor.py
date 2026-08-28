from langchain_core.prompts import ChatPromptTemplate

from ..llm import build_chat_model
from ..models import FailureReason, RecoveryProposal
from ..state import DLQHealingState

supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Supervisor Agent overseeing data pipeline DLQ recovery.
Return a structured recovery proposal.
Use schema_error only when all missing values can be recovered from the payload or trusted context.
Use missing_required_value when a required business value is absent.
Do not invent content or other facts.
Use unrecoverable when the payload cannot be safely reconstructed.
Every proposed change must be listed with its before value, after value, and reason."""),
    ("user", "Error: {error_message}\nPayload: {raw_payload}\nTrusted context: {recovery_context}")
])


def build_supervisor_chain():
    llm = build_chat_model()
    return supervisor_prompt | llm.with_structured_output(RecoveryProposal)


def route_proposal(proposal: RecoveryProposal) -> str:
    if proposal.reason is FailureReason.SCHEMA_ERROR and proposal.recoverable:
        return "schema_agent"
    return "FINISH"


def supervisor_node(state: DLQHealingState) -> DLQHealingState:
    chain = build_supervisor_chain()
    proposal = chain.invoke({
        "error_message": state["error_message"],
        "raw_payload": state["raw_payload"],
        "recovery_context": state.get("recovery_context", {}),
    })

    decision = route_proposal(proposal)
    state["next_agent"] = decision
    state["reason"] = proposal.reason.value
    state["confidence"] = proposal.confidence
    state["changes"] = [change.model_dump() for change in proposal.changes]
    state["recovery_proposal"] = proposal.model_dump(mode="json")
    state.setdefault("logs", []).append(f"Supervisor Routed to: {decision}")
    return state
