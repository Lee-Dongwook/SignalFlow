from typing import List, Dict, Any
from apps.retrieval.clickhouse_hybrid import ClickHouseHybridEngine
from apps.retrieval.neo4j_graph import Neo4jGraphEngine
from apps.retrieval.reranker import DocumentReranker

class AdvancedGraphRAGPipeline:
    def __init__(self):
        self.hybrid_engine = ClickHouseHybridEngine()
        self.graph_engine = Neo4jGraphEngine()
        self.reranker = DocumentReranker()
    
    def run(self, query_text: str, query_vector: List[float], candidate_k: int = 10, final_top_n: int = 3) -> Dict[str, Any]:
        # 1. ClickHouse Hybrid Search + RRF
        candidates = self.hybrid_engine.search(query_text, query_vector, top_k=candidate_k)

        # 2. Cross-Encoder Reranking
        reranked_docs = self.reranker.rerank(query_text, candidates, top_n=final_top_n)

        # 3. Neo4j Graph Traversal
        top_ids = [doc["event_id"] for doc in reranked_docs]
        graph_contexts = self.graph_engine.fetch_subgraph_context(top_ids)

        return {
            "query": query_text,
            "documents": reranked_docs,
            "graph_context": graph_contexts
        }

