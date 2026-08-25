import time
import uuid
import random
from confluent_kafka import Producer

from schemas.event_schema_v1_pb2 import IntelligenceEvent, EventCategory

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC_NAME = "unstructured-events"

producer_conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "client.id": "signalflow-event-producer",
}

producer = Producer(producer_conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Sent Topic: {msg.topic()} | Partition: [{msg.partition()} | Offset: {msg.offset()}]")

SAMPLE_TEXTS = [
    "실시간 Flink 스트리밍 엔진에서 GPU 가속 기반 vLLM을 연결하여 초저지연 임베딩을 추출합니다.",
    "Data Quality 모니터링 레이어는 Schema Drift 및 텍스트 이상 유무를 체크하여 DLQ로 격리합니다.",
    "GraphRAG 구성을 위해 비정형 텍스트 내 주요 엔티티를 추출하고 Neo4j와 Memgraph에 파이프라이닝합니다.",
    "",
    "[ANOMALY_TEST] INVALID_PAYLOAD_FORMAT_ERR_0001"
]

def generate_protobuf_event() -> IntelligenceEvent:
    selected_text = random.choice(SAMPLE_TEXTS)

    category = EventCategory.UNKNOWN
    if not selected_text or selected_text.isspace():
        category = EventCategory.NULL_VALUE
    elif "[ANOMALY_TEST]" in selected_text:
        category = EventCategory.SCHEMA_MISMATCH

    event = IntelligenceEvent(
        event_id=str(uuid.uuid4()),
        source="stream_simulator",
        category=category,
        payload=selected_text,
        timestamp=int(time.time() * 1000), 
        trace_id=uuid.uuid4().hex,
        span_id=uuid.uuid4().hex[:16]
    )

    event.metadata["user_id"] = f"user_{random.randint(100, 999)}"
    event.metadata["env"] = "test"

    return event

def run_producer(events_per_second: int = 2):
    print(f"Starting Protobuf Kafka Producer for '{TOPIC_NAME}'")
    delay = 1.0 / events_per_second

    try:
        while True:
            event = generate_protobuf_event()
            serialized_payload = event.SerializeToString()
            producer.produce(
                topic=TOPIC_NAME,
                key=event.event_id.encode("utf-8"),
                value=serialized_payload,
                callback=delivery_report,
            )
            producer.poll(0)
            time.sleep(delay)

    except KeyboardInterrupt:
        print("Stopping Producer")
    
    finally:
        producer.flush()
        producer.close()

if __name__ == "__main__":
    run_producer()
