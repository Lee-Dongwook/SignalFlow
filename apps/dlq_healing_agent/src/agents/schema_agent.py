import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.state import DLQHealingState

llm = ChatOpenAI(model="gpt-4o", temperature=0)

schema_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Schema Repair Agent. Fix structural schema errors in the payload.
Required Schema:
- event_id: string
- source: string
- category: string
- content: string
- timestamp: integer (epoch ms)

Return ONLY a valid JSON string matching the required schema."""),
    ("user", "Raw Payload: {raw_payload}\nError: {error_message}")
])

def schema_repair_node(state: DLQHealingState) -> DLQHealingState:
    chain = schema_prompt | llm
    response = chain.invoke({
        "raw_payload": state["raw_payload"],
        "error_message": state["error_message"]
    })

    try:
        repaired_json = json.loads(response.content.strip())
        state["corrected_payload"] = repaired_json
        state["is_repaired"] = True
        state["logs"].append("Schema Agent successfully repaired.")
    except Exception as e:
        state["is_repaired"] = False
        state["logs"].append(f"Schema Agent Repair failed: {str(e)}")

    return state
