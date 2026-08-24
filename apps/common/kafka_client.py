import json
import logging
from typing import Callable, Optional
from confluent_kafka import Producer, Consumer, KafkaError, KafkaException

logger = logging.getLogger(__name__)

class SignalFlowKafkaProducer:
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.conf = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "signalflow-producer",
            "acks": "all", 
        }
        self.producer = Producer(self.conf)
    
    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Kafka Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

    def send_event(self, topic: str, value: dict, key: Optional[str] = None):
        payload = json.dumps(value).encode("utf-8")
        self.producer.produce(
            topic=topic,
            value=payload,
            key=key.encode("utf-8") if key else None,
            on_delivery=self._delivery_report
        )
        self.producer.poll(0)

    def flush(self, timeout: float = 10.0):
        self.producer.flush(timeout)

class SignalFlowKafkaConsumer:
    def __init__(self, topics: list[str], group_id: str, bootstrap_servers: str = "localhost:9092"):
        self.conf = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }
        self.consumer = Consumer(self.conf)
        self.consumer.subscribe(topics)
    
    def consume_loop(self, handler_fn: Callable[[dict], None], timeout: float = 1.0):
        try:
            msg = self.consumer.poll(timeout=timeout)
            if msg is None:
                return
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    return
                raise KafkaException(msg.error())

            payload = json.loads(msg.value().decode("utf-8"))
            handler_fn(payload)

        except Exception as e:
            logger.exception(f"Error consuming message: {e}")
            raise e
            
    def close(self):
        self.consumer.close()
