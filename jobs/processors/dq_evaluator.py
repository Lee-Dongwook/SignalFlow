from pyflink.datastream import OutputTag, ProcessFunction
from schemas.event_schema_v1_pb2 import EventCategory, IntelligenceEvent

DLQ_TAG = OutputTag("dlq_events")

class DataQualityEvaluator(ProcessFunction):
    def process_element(self, value: IntelligenceEvent, ctx: ProcessFunction.Context):
        if value.category == EventCategory.SCHEMA_MISMATCH:
            ctx.output(DLQ_TAG, self._build_dlq_record(value, "Schema Mismatch or Corrupted Payload"))
            return
        
        if not value.payload or value.payload.isspace():
            value.category = EventCategory.NULL_VALUE
            ctx.output(DLQ_TAG, self._build_dlq_record(value, "Payload is Empty or Null"))
            return
        
        if len(value.payload.strip()) < 5:
            value.category = EventCategory.MISSING_FIELD
            ctx.output(DLQ_TAG, self._build_dlq_record(value, "Payload Length Below Threshold (<5)"))
            return
        
        yield value

    def _build_dlq_record(self, event: IntelligenceEvent, reason: str) -> dict:
        return {
            "event_id": event.event_id,
            "source": event.source,
            "category": EventCategory.Name(event.category),
            "payload": event.payload,
            "error_reason": reason,
            "timestamp": event.timestamp,
            "trace_id": event.trace_id,
        }
