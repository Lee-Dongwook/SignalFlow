import json
from typing import List, Dict, Any
from apps.retrieval.clickhouse_hybrid import ClickHouseHybridEngine
from apps.retrieval.neo4j_graph import Neo4jGraphEngine

class AgenticTools:
    def __init__(self):
        self.clickhouse = ClickHouseHybridEngine()
        self.neo4j = Neo4jGraphEngine()

    def vector_and_keyword_search(self, query_text: str, query_vector: List[float]) -> str:
        results = self.clickhouse.search(query_text=query_text, query_vector=query_vector, top_k=5)
        return json.dumps(results, ensure_ascii=False)

    def graph_cypher_search(self, event_ids: List[str]) -> str:
        results = self.neo4j.fetch_subgraph_context(event_ids=event_ids)
        return json.dumps(results, ensure_ascii=False)

tool_definitions = [
    {
        "name": "vector_and_keyword_search",
        "description": "이벤트 로그 및 비정형 메시지에서 벡터 유사도 및 키워드 기반 하이브리드 검색을 수행합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "query_text": {"type": "string", "description": "검색할 키워드 또는 문장"}
            },
            "required": ["query_text"]
        }
    },
    {
        "name": "graph_cypher_search",
        "description": "이벤트 ID 간의 연관 관계 및 인프라 엔티티 간의 연결 상태를 조회합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_ids": {"type": "array", "items": {"type": "string"}, "description": "조회할 이벤트 ID 리스트"}
            },
            "required": ["event_ids"]
        }
    }
]
