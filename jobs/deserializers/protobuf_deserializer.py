import base64

from pyflink.datastream.functions import MapFunction
from schemas.event_schema_v1_pb2 import IntelligenceEvent, EventCategory


class ProtobufEventParser(MapFunction):
    """Kafka의 원시 바이트 메시지를 Protobuf 이벤트로 변환한다."""

    def map(self, message: str) -> IntelligenceEvent:
        event = IntelligenceEvent()

        try:
            event.ParseFromString(base64.b64decode(message))
            return event
        except Exception:
            fallback_event = IntelligenceEvent(
                event_id="corrupted-event",
                source="deserializer_error",
                category=EventCategory.SCHEMA_MISMATCH,
                payload="",
            )
            return fallback_event
