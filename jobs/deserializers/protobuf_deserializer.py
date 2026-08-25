from pyflink.common.serialization import DeserializationSchema
from pyflink.common.typeinfo import Types
from schemas.event_schema_v1_pb2 import IntelligenceEvent, EventCategory

class IntelligenceEventDeserializer(DeserializationSchema):
    def deserialize(self, message: bytes) -> IntelligenceEvent:
        event = IntelligenceEvent()

        try:
            event.ParseFromString(message)
            return event
        except Exception:
            fallback_event = IntelligenceEvent(
                event_id="corrupted-event",
                source="deserializer_error",
                category=EventCategory.SCHEMA_MISMATCH,
                payload="",
            )
            return fallback_event

    def get_produced_type(self):
        return Types.PICKLED_BYTE_ARRAY()
