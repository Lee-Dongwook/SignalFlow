from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.state import DLQHealingState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Supervisor Agent overseeing data pipeline DLQ recovery.
Analyze the error message and determine the best worker agent to fix the data:
- 'schema_agent': Fixes missing keys, incorrect data types, or invalid JSON structures.
- 'value_agent': Fixes missing or null required values by imputing realistic context.
- 'FINISH': If the payload is unrecoverable or already valid.

Respond strictly with one of: 'schema_agent', 'value_agent', or 'FINISH'."""),
    ("user", "Error: {error_message}\nPayload: {raw_payload}")
])

def supervisor_node(state: DLQHealingState) -> DLQHealingState: 
    chain = supervisor_prompt | llm
    response = chain.invoke({
        "error_message": state["error_message"],
        "raw_payload": state["raw_payload"]
    })

    decision = response.content.strip()
    state["next_agent"] = decision
    state["logs"].append(f"Supervisor Routed to: {decision}")
    return state
