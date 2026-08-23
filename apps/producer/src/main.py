import json
import time
from kafka import KafkaProducer
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

provider = TracerProvider()
processor = BatchSpanProcessor(JaegerExporter(collector_endpoint='http://jaeger:14268/api/traces'))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("kafka-producer")

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_event_with_trace(event_data):
    with tracer.start_as_current_span("produce_kafka_event") as span:
        headers = []
        TraceContextTextMapPropagator().inject(carrier=headers, setter=lambda c,k,v: c.append((k, v.encode('utf-8'))))

        span.set_attribute("event.id", event_data["event_id"])
        producer.send('raw-intelligence-stream', value=event_data, headers=headers)
        print(f"Sent with trace {event_data['event_id']} | Trace ID: {hex(span.get_span_context().trace_id)}")

if __name__ == '__main__':
    event = {"event_id": "evt-1001", "source": "news", "category": "AI", "title": "OTel Integration"}
    send_event_with_trace(event)
    producer.flush()
