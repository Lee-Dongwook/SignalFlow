import pytest
import json
import time
import os
from confluent_kafka import Producer, Consumer, KafkaError

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Kafka integration test: run with RUN_INTEGRATION_TESTS=1 and test infrastructure running",
)

KAFKA_SERVER = "localhost:9092"
MAIN_TOPIC = "signalflow.events.raw"
DLQ_TOPIC = "signalflow.events.dlq"

@pytest.fixture(scope="module")
def kafka_setup():
    producer = Producer({
        "bootstrap.servers":KAFKA_SERVER,
        
    })
    consumer = Consumer({
        "bootstrap.servers": KAFKA_SERVER,
        "group.id": "test_dlq_group",
        "auto.offset.reset": "earliest"
    })
    consumer.subscribe([DLQ_TOPIC])
    return producer, consumer

def test_kafka_dlq_routing_on_poison_pill(kafka_setup):
    producer, consumer = kafka_setup

    bad_payload = json.dumps({"event_id": "corrupt-001", "malformed_json": True}).encode("utf-8")
    producer.produce(DLQ_TOPIC, value=bad_payload)
    producer.flush()
    
    msg = consumer.poll(timeout=5.0)
    assert msg is not None, "Kafka 메시지 수신 타임아웃 (Docker Kafka 브로커 확인 필요)"
    assert msg.error() is None, f"Kafka Error: {msg.error()}"

    received_payload = json.loads(msg.value().decode("utf-8"))
    assert received_payload["event_id"] == "corrupt-001"

    consumer.close()
