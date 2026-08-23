import json
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import MapFunction
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

class OTelTracingMapFunction(MapFunction):
    def open(self, runtime_context):
        self.tracer = trace.get_tracer("flink-workder")
    
    def map(self, kafka_record):
        headers_dict = {k: v.decode('utf-8') for k, v in kafka_record.headers()}
        parent_context = TraceContextTextMapPropagator().extract(carrier=headers_dict)

        with self.tracer.start_as_current_span("flink_process_event", context=parent_context) as span:
            payload = json.loads(kafka_record.value())
            span.set_attribute("flink.operator", "quality_filter")
            span.set_attribute("event.id", payload.get("event_id", ""))

            payload["processed_by"] = "flink"
            return json.dumps(payload)
