import os
from neo4j import GraphDatabase
from pyflink.datastream.functions import SinkFunction

class Neo4jGraphSink(SinkFunction):
    def __init__(self, uri: str = None, user: str = "neo4j", password: str = "test_password"):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://host.k3d.internal:7687")
        self.user = user
        self.password = password
        self.driver = None
    
    def open(self, context):
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def invoke(self, value: dict, context):
        cypher_query = """
        MERGE (e:IntelligenceEvent {event_id: $event_id})
        ON CREATE SET 
            e.payload = $payload,
            e.embedding = $embedding,
            e.timestamp = $timestamp,
            e.source = $source,
            e.trace_id = $trace_id

        MERGE (u:User {user_id: $user_id})
        MERGE (e)-[:CREATED_BY]->(u)
        """
        user_id = value.get("metadata", {}).get("user_id", "unknown_user")

        with self.driver.session() as session:
            session.run(
                cypher_query,
                event_id=value["event_id"],
                payload=value["payload"],
                embedding=value["embedding"],
                timestamp=value["timestamp"],
                source=value["source"],
                trace_id=value["trace_id"],
                user_id=user_id,
            )

    def close(self):
        if self.driver:
            self.driver.close()
