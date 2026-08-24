from confluent_kafka import Producer
from opentelemetry import trace
from apps.common.telemetry import init_tracer, inject_trace_context

tracer = init_tracer("signalflow-producer")

class TracedKafkaProducer:
    def __init__(self, bootstrap_servers: str):
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})
    
    def send_traced_event(self, topic:str, key:str, value:str):
        with tracer.start_as_current_span("kafka_produce_event") as span:
            span.set_attribute("messaging.system", "kafka")
            span.set_attribute("messaging.destination", topic)

            headers_dict = {}
            inject_trace_context(headers_dict)
            kafka_headers = [(k, v.encode('utf-8')) for k, v in headers_dict.items()]

            self.producer.produce(
                topic=topic,
                key=key,
                value=value,
                headers=kafka_headers
            )
            self.producer.flush()
