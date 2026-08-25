from pyflink.datastream.functions import MapFunction
from neo4j import GraphDatabase

class Neo4jGraphSink(MapFunction):
    def __init__(self, uri="bolt://localhost:7687", auth=("neo4j", "test_password")):
        self.uri = uri
        self.auth = auth
        self.driver = None

    def open(self, runtime_context):
        self.driver = GraphDatabase.driver(self.uri, auth=self.auth)

    def map(self, value):
        if not value:
            return value
            
        with self.driver.session() as session:
            query = """
            MERGE (e:IntelligenceEvent {id: $event_id})
            SET e.payload = $payload, e.timestamp = $timestamp
            """
            session.run(
                query,
                event_id=value.get("event_id"),
                payload=value.get("payload"),
                timestamp=value.get("timestamp")
            )
        return value

    def close(self):
        if self.driver:
            self.driver.close()
