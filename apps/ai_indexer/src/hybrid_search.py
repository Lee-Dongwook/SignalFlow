class GraphRAGEngine:
    def __init__(self, es_client, neo4j_store):
        self.es = es_client
        self.graph = neo4j_store
    
    def search(self, query_text: str, query_vector: list, top_k: int = 5):
        es_res = self.es.search(
            index="intelligence_events",
            knn={
                "field": "content_vector",
                "query_vector": query_vector,
                "k": top_k,
                "num_candidates": 50
            }
        )
        vector_hits = [hit["_source"] for hit in es_res["hits"]["hits"]]

        entities = list(set([h.get("category") for h in vector_hits if h.get("category")]))

        cypher = """
        MATCH (e:Entity) WHERE e.name IN $entities
        MATCH path = (e)-[r*1..2]-(target:Entity)
        RETURN e.name AS entity, labels(target) AS target_type, target.name AS connected_entity, type(r[0]) AS relation
        LIMIT 20
        """

        with self.graph.driver.session() as session:
            graph_res = session.run(cypher, entities=entities).data()

        hybrid_context = {
            "retrieved_documents": vector_hits,
            "knowledge_graph_subgraph": graph_res
        }

        return hybrid_context

