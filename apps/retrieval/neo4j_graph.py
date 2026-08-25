from typing import List, Dict, Any
from neo4j import GraphDatabase

class Neo4jGraphEngine:
    def __init__(self, uri="bolt://localhost:7687", auth=("neo4j", "test_password")):
        self.driver = GraphDatabase.driver(uri, auth=auth)
    
    def close(self):
        if self.driver:
            self.driver.close()

    def fetch_subgraph_context(self, event_ids: List[str]) -> List[Dict[str, Any]]:
        if not event_ids:
            return []
        
        cypher = """
        MATCH (e: IntelligenceEvent) WHERE e.id IN $event_ids
        OPTIONAL MATCH (e)-[r]->(target)
        RETURN e.id AS source_id, type(r) AS rel_type, target.id AS target_id
        """

        relations = []
        with self.driver.session() as session:
            result = session.run(cypher, event_ids=event_ids)
            for record in result:
                if record["rel_type"] and record["target_id"]:
                    relations.append({
                        "source": record["source_id"],
                        "relation": record["rel_type"],
                        "target": record["target_id"]
                    })
                else:
                    relations.append({
                        "source": record["source_id"],
                        "relation": None, 
                        "target": None
                    })
        return relations

from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

class DocumentReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        pairs = [[query, doc.get("payload", "")] for doc in candidates]
        scores = self.model.predict(pairs)

        for i, score in enumerate(scores):
            candidates[i]["rerank_score"] = float(score)

        sorted_candidates = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        return sorted_candidates[:top_n]
