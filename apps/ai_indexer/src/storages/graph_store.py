from neo4j import GraphDatabase

class Neo4jGraphStore:
    def __init__(self, uri="bolt://neo4j:7687", auth=("neo4j", "password123")):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def upsert_triples(self, triples, event_id):
        query= """
        UNWIND $triples AS t
        MERGE (s:Entity {name: t.subject})
        ON CREATE SET s.type = t.subject_type
        MERGE (o:Entity {name: t.object})
        ON CREATE SET o.type = t.object_type

        WITH s, o, t
        CALL apoc.create.relationship(s, UPPER(t.predicate), {source_event: $event_id}, o) YIELD rel
        RETURN count(rel)
        """

        with self.driver.session() as session:
            session.run(query, triples=triples, event_id=event_id)
