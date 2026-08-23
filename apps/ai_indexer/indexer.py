import json
from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer


print("Loading Embedding Model")
embedder = SentenceTransformer('all-MiniLM-L6-v2') 

es = Elasticsearch("http://localhost:9200")
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))

consumer = KafkaConsumer(
    'raw-intelligence-stream',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest'
)


def create_knowledge_graph(tx, event_id, category, title):
    query = """
    MERGE (e:Event {id: $event_id})
    SET e.title = $title
    MERGE (c:Category {name: $category})
    MERGE (e)-[:BELONGS_TO]->(c)
    """
    tx.run(query, event_id=event_id, category=category, title=title)


print("Starting AI Indexer: Ingesting to ES & Neo4j")
try:
    for message in consumer:
        event = message.value
        event_id = event.get('event_id')
        title = event.get('title', '')
        content = event.get('content', '')
        category = event.get('category', 'GENERAL')

        if not event_id or not content:
            continue

        
        text_to_embed = f"{title} {content}"
        vector = embedder.encode(text_to_embed).tolist()

        
        doc = {
            "event_id": event_id,
            "source": event.get('source'),
            "category": category,
            "title": title,
            "content": content,
            "text_embedding": vector,
            "created_at": event.get('created_at')
        }
        es.index(index="intelligence-vector-index", id=event_id, document=doc)

        
        with neo4j_driver.session() as session:
            session.execute_write(create_knowledge_graph, event_id, category, title)

        print(f"[INDEXED] ES Vector & Neo4j Graph -> event_id: {event_id}")

except KeyboardInterrupt:
    print("Indexer stopped.")
finally:
    neo4j_driver.close()
