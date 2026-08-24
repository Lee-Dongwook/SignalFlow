import json
import time
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

tracer = trace.get_tracer("flink-stream-processor")

def process_element_with_tracing(element_str: str, headers: list):
    carrier = {k: v.decode('utf-8') if isinstance(v, bytes) else v for k, v in headers}
    ctx = TraceContextTextMapPropagator().extract(carrier=carrier)

    with tracer.start_as_current_span("flink_data_transformation", context=ctx) as span:
        try:
            raw_data = json.loads(element_str)

            event_id = raw_data.get("event_id")
            if not event_id:
                span.set_attribute("error", True)
                span.set_attribute("error.type", "MISSING_EVENT_ID")
                raise ValueError("Missing required field: event_id")

            transformed_element = {
                "event_id": str(event_id).strip(),
                "source": raw_data.get("source", "unknown").lower(),
                "category": raw_data.get("category", "uncategorized"),
                "content": raw_data.get("content", "").strip(),
                "processed_at": int(time.time() * 1000),
                "is_valid": True
            }

            span.set_attribute("event.id", transformed_element["event_id"])
            span.set_attribute("event.category", transformed_element["category"])
            span.set_attribute("processing.status", "SUCCESS")

            return transformed_element
        
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("processing.status", "Failed")
            return {
                "raw_data": element_str,
                "error_message": str(e),
                "is_valid": False
            }


