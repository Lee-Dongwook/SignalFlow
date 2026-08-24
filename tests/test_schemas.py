import pytest
import time
from schemas.event_schema_v1_pb2 import IntelligenceEvent, EventCategory

def test_protobuf_event_serialization():
    raw_event={
        "event_id": "test-uuid-1234",
        "source": "kafka_stream_test",
        "category": EventCategory.SCHEMA_MISMATCH,
        "payload": '{"invalid_key": "bad_data"}',
        "timestamp": int(time.time() * 1000),
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "span_id": "00f067aa0ba902b7"
    }

    proto_event = IntelligenceEvent(**raw_event)
    serialized_data = proto_event.SerializeToString()

    deserialized_event = IntelligenceEvent()
    deserialized_event.ParseFromString(serialized_data)

    assert deserialized_event.event_id == raw_event["event_id"]
    assert deserialized_event.category == EventCategory.SCHEMA_MISMATCH
    assert deserialized_event.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert deserialized_event.timestamp == raw_event["timestamp"]
