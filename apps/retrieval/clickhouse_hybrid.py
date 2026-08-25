from typing import List, Dict, Any
import clickhouse_connect

class ClickHouseHybridEngine:
    def __init__(self, host="localhost", port=8123, database="signalflow_test"):
        self.host = host
        self.port = port
        self.database = database
    
    def _get_client(self):
        return clickhouse_connect.get_client(host=self.host, port=self.port, database=self.database)
        
    def _apply_rrf(self, rank_lists: List[List[Dict[str, Any]]], k: int = 60) -> List[Dict[str,Any]]:
        scores = {}
        item_map = {}
        for rank_list in rank_lists:
            for rank, item in enumerate(rank_list):
                doc_id = item["event_id"]
                item_map[doc_id] = item
                scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))

        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [item_map[doc_id] for doc_id, _ in sorted_ids] 

    def search(self, query_text: str, query_vector: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        client = self._get_client()

        dense_sql = """
        SELECT event_id, payload, source, timestamp, trace_id, L2Distance(embedding, {query_vec:Array(Float32)}) AS dist
        FROM intelligence_vectors
        ORDER BY dist ASC LIMIT {top_k}
        """
        dense_rows = client.query(dense_sql, parameters={"query_vec": query_vector})
        dense_docs = [
            {"event_id": r[0], "payload": r[1], "source": r[2], "timestamp": r[3], "trace_id": r[4]}
            for r in dense_rows
        ]

        sparse_sql = """
        SELECT event_id, payload, source, timestamp, trace_id
        FROM intelligence_vectors
        WHERE payload ILIKE {query_text}
        LIMIT {top_k}
        """
        
        sparse_rows = client.query(
            sparse_sql, 
            parameters={"query_text": f"%{query_text}", "top_k": top_k}
        ).result_rows
        
        sparse_docs = [
            {"event_id": r[0], "payload": r[1], "source": r[2], "timestamp": r[3], "trace_id": r[4]}
            for r in sparse_rows
        ]

        return self._apply_rrf([dense_docs, sparse_docs])[:top_k]

