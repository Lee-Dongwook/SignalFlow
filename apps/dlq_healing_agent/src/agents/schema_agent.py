from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..models import RecoveryProposal
from ..state import DLQHealingState

schema_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a Schema Repair Agent.
Return a structured recovery proposal for a telemetry event with these fields:
event_id (string), source (string), category (string), content (string).
timestamp is an integer epoch in milliseconds.
Only correct types or add a missing field when the value exists in trusted context.
Never create content or other business facts absent from the payload and trusted context.
If safe recovery is not possible, return recoverable=false with no corrected payload.
List every change with its before value, after value, and reason.""",
        ),
        (
            "user",
            "Raw payload: {raw_payload}\nError: {error_message}\n"
            "Trusted context: {recovery_context}\n"
            "Supervisor proposal: {supervisor_proposal}",
        ),
    ]
)


def build_schema_repair_chain():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return schema_prompt | llm.with_structured_output(RecoveryProposal)


def schema_repair_node(state: DLQHealingState) -> DLQHealingState:
    chain = build_schema_repair_chain()
    proposal = chain.invoke(
        {
            "raw_payload": state["raw_payload"],
            "error_message": state["error_message"],
            "recovery_context": state.get("recovery_context", {}),
            "supervisor_proposal": state["recovery_proposal"],
        }
    )

    state["reason"] = proposal.reason.value
    state["confidence"] = proposal.confidence
    state["changes"] = [change.model_dump() for change in proposal.changes]
    state["corrected_payload"] = proposal.corrected_payload
    state["recovery_proposal"] = proposal.model_dump(mode="json")
    state.setdefault("logs", []).append("Schema Agent completed recovery proposal.")
    return state
