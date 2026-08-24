import pytest
import clickhouse_connect
from elasticsearch import Elasticsearch
from neo4j import GraphDatabase
from tenacity import retry, stop_after_attempt, wait_fixed

CLICKHOUSE_PORT = 8123
ELASTICSEARCH_PORT = 9200
NEO4J_BOLT_PORT = 7687

@pytest.fixture(scope="module")
def infra_clients():
    ch_client = clickhouse_connect.get_client(
        host='localhost', 
        port=CLICKHOUSE_PORT, 
        username='default', 
        password=''
    )
    
    
    es_client = Elasticsearch(
        [f"http://localhost:{ELASTICSEARCH_PORT}"],
        request_timeout=5,
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    
    neo4j_driver = GraphDatabase.driver(
        f"bolt://localhost:{NEO4J_BOLT_PORT}", 
        auth=("neo4j", "test_password")
    )
    
    yield {
        "clickhouse": ch_client, 
        "elasticsearch": es_client, 
        "neo4j": neo4j_driver
    }
    
    neo4j_driver.close()

def test_clickhouse_connection(infra_clients):
    ch = infra_clients["clickhouse"]
    result = ch.command("SELECT 1")
    assert result == 1


@retry(stop=stop_after_attempt(15), wait=wait_fixed(2))
def test_elasticsearch_cluster_health(infra_clients):
    es = infra_clients["elasticsearch"]
    health = es.cluster.health()
    assert health["status"] in ["green", "yellow"]

def test_neo4j_node_creation_and_query(infra_clients):
    driver = infra_clients["neo4j"]
    with driver.session() as session:
        session.run("CREATE (a:Agent {name: 'TestAgent'})")
        result = session.run("MATCH (a:Agent {name: 'TestAgent'}) RETURN a.name AS name")
        record = result.single()
        assert record["name"] == "TestAgent"
        session.run("MATCH (a:Agent {name: 'TestAgent'}) DELETE a")
