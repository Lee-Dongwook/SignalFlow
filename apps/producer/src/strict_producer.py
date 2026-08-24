import os
import time
import uuid
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.protobuf import ProtobufSerializer
from schemas.event_schema_v1_pb2 import IntelligenceEvent, EventCategory

class StrictEventProducer:
    def __init__(self):
        registry_url = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

        schema_registry_client = SchemaRegistryClient({"url": registry_url})

        protobuf_serializer = ProtobufSerializer(
            IntelligenceEvent,
            schema_registry_client,
            {"use.deprecated.format": False}
        )

        producer_conf = {
            "bootstrap.servers": bootstrap_servers,
            "key.serializer": lambda k, ctx: k.encode("utf-8") if k else None,
            "value.serializer": protobuf_serializer,
            "acks": "all",
            "enable.idempotence": True,
            "max.in.flight.request.per.connection": 5,
            "retries": 214783647
        }
        self.producer = SerializingProducer(producer_conf)
    
    def send_event(self, topic: str, payload_data: dict, trace_id: str = "", span_id: str = ""):
        event = IntelligenceEvent(
            event_id=str(uuid.uuid4()),
            source=payload_data.get("source", "stream_pipeline"),
            category=payload_data.get("category", EventCategory.UNKNOWN),
            payload=payload_data.get("payload", ""),
            timestamp=int(time.time() * 1000),
            trace_id=trace_id,
            span_id=span_id,
            metadata=payload_data.get("metadata", {})
        )

        self.producer.produce(
            topic=topic,
            key=event.event_id,
            value=event,
            on_delivery=self._delivery_callback
        )

        self.producer.poll(0)

    @staticmethod
    def _delivery_callback(err, msg):
        if err is not None:
            print(f"Kafka Delivery Failed: {err}")
        else:
            print(f"Delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

