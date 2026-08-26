from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from apps.retrieval.tools import AgenticTools

router = APIRouter(prefix="/api/v1/search", tags=["Agentic Search"])
tools_instance = AgenticTools()

class AgenticSearchRequest(BaseModel):
    query: str
    embedding: Optional[List[float]] = None

class AgenticSearchResponse(BaseModel):
    query: str
    selected_tools: List[str]
    retrieved_context: Any

@router.post("/agentic", response_model=AgenticSearchResponse)
async def agentic_search(request: AgenticSearchRequest):
    selected_tools = []
    context_data = {}

    vector = request.embedding if request.embedding else [0.01] * 768

    if any(k in request.query for k in ["관계", "연결", "토폴로지", "엔티티"]):
        selected_tools.append("graph_cypher_search")
        context_data["graph"] = tools_instance.graph_cypher_search(["evt-9012"])
    
    selected_tools.append("vector_and_keyword_search")
    context_data["vector"] = tools_instance.vector_and_keyword_search(request.query, vector)

    return AgenticSearchResponse(
        query=request.query,
        selected_tools=selected_tools,
        retrieved_context=context_data
    )
