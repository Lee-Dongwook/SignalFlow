from langgraph.graph import END, StateGraph

from .agents.schema_agent import schema_repair_node
from .agents.supervisor import supervisor_node
from .state import DLQHealingState
from .validator import validator_node


def route_next(state: DLQHealingState) -> str:
    return state["next_agent"]

def build_dlq_healing_graph():
    workflow = StateGraph(DLQHealingState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("schema_agent", schema_repair_node)
    workflow.add_node("validator", validator_node)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_next,
        {
            "schema_agent": "schema_agent",
            "FINISH": "validator",
        }
    )
    workflow.add_edge("schema_agent", "validator")
    workflow.add_edge("validator", END)

    return workflow.compile()
