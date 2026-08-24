import pytest
import time
from unittest.mock import MagicMock
from schemas.event_schema_v1_pb2 import IntelligenceEvent, EventCategory

def test_protobuf_event_serialization():
    raw_event={
        "event_id": "evt-1001",
        "source": "kafka_stream_test",
        "category": EventCategory.SCHEMA_MISMATCH,
        "payload": '{"invalid_field": "test_value"}',
        "timestamp": int(time.time() * 1000),
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "span_id": "00f067aa0ba902b7",
        "metadata": {"env": "test", "version": "v1"}
    }

    proto_event = IntelligenceEvent(**raw_event)
    serialized_data = proto_event.SerializeToString()

    deserialized_event = IntelligenceEvent()
    deserialized_event.ParseFromString(serialized_data)

    assert deserialized_event.event_id == "evt-1001"
    assert deserialized_event.category == EventCategory.SCHEMA_MISMATCH
    assert deserialized_event.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert deserialized_event.metadata["env"] == "test"

def test_schema_producer_serializer_mock():
    mock_serializer = MagicMock()
    mock_serializer.return_value = b"\x00\x00\x00\x00\x01\x08\x01"

    event = IntelligenceEvent(
        event_id="evt-1002",
        source="unit_test",
        category=EventCategory.SYSTEM_LATENCY
    )

    serialized_data = mock_serializer(event)
    assert isinstance(serialized_data, bytes)
    mock_serializer.assert_called_once_with(event)

