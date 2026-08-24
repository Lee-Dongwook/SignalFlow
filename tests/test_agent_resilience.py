import pytest
import time
from unittest.mock import MagicMock
from apps.dlq_healing_agent.src.circuit_breaker import ResilientSupervisorAgent, LLMRateLimitError, CircuitBreakerOpenException

class MockPostgresSaver:
    def setup(self):
        pass

    def put(self, config, checkpoint, metadata, new_versions):
        pass

    def get_tuple(self, config):
        return None

@pytest.fixture
def agent():
    checkpointer = MockPostgresSaver()
    return ResilientSupervisorAgent(checkpointer)

def test_llm_retry_success_on_second_attempt(agent):
    calls = 0

    def mock_llm_call(state):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise LLMRateLimitError("Rate Limit Hit")
        return {"status": "SUCCESS", "healed_payload": state.get("payload")}

    agent._call_llm_execution = MagicMock(side_effect=mock_llm_call)

    result = agent.invoke_agent_with_retry({"payload": "test_data"}, config={})

    assert result["status"] == "SUCCESS"
    assert calls == 2
    assert agent.failure_count == 0

def test_circuit_breaker_trip_and_cooldown(agent):
    agent._call_llm_execution = MagicMock(
        side_effect=LLMRateLimitError("Persistent Failure")
    )

    for _ in range(5):
        with pytest.raises(LLMRateLimitError):
            agent.invoke_agent_with_retry({"payload": "bad_payload"}, config={})

    assert agent.circuit_open is True

    with pytest.raises(CircuitBreakerOpenException) as exc_info:
        agent.invoke_agent_with_retry({"payload": "bad_payload"}, config={})

    assert "[CIRCUIT_OPEN]" in str(exc_info.value)

    agent.last_failure_time = time.time() - 31
    agent._call_llm_execution = MagicMock(
        return_value={"status": "SUCCESS", "healed_payload": "recovered"}
    )

    recovery_result = agent.invoke_agent_with_retry(
        {"payload": "recovered"}, config={}
    )
    assert recovery_result["status"] == "SUCCESS"
    assert agent.circuit_open is False
