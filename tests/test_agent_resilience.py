import pytest
from unittest.mock import MagicMock
from apps.dlq_healing_agent.src.circuit_breaker import ResilientSupervisorAgent, LLMRateLimitError

class MockCheckpointer:
    def setup(self): pass

def test_circuit_breaker_opens_after_failures():
    checkpointer = MockCheckpointer()
    agent = ResilientSupervisorAgent(checkpointer)

    agent._call_llm_execution = MagicMock(side_effect=LLMRateLimitError("Rate Limit Exceeded"))

    for _ in range(5):
        with pytest.raises(LLMRateLimitError):
            agent.invoke_agent_with_retry({"payload": "test"}, config={})

    assert agent.circuit_open is True

    with pytest.raises(Exception) as exc_info:
        agent.invoke_agent_with_retry({"payload": "test"}, config={})

    assert "[CIRCUIT_OPEN]" in str(exc_info.value)
