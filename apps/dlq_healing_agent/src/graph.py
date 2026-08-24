from langgraph.graph import StateGraph, END
from src.state import DLQHealingState
from src.agents.supervisor import supervisor_node
from src.agents.schema_agent import schema_repair_node

def route_next(state: DLQHealingState) -> str:
    return state["next_agent"]

def build_dlq_healing_graph():
    workflow = StateGraph(DLQHealingState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("schema_agent", schema_repair_node)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_next,
        {
            "schema_agent": "schema_agent",
            "FINISH": END
        }
    )
    workflow.add_edge("schema_agent", END)

    return workflow.compile()

