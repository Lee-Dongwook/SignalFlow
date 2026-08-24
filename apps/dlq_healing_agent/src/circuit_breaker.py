import time
from tenacity import retry, stop_after_attempt, wait_none, retry_if_exception_type

class LLMRateLimitError(Exception): pass
class LLMTimeoutError(Exception): pass
class CircuitBreakerOpenException(Exception): pass

class ResilientSupervisorAgent:
    def __init__(self, checkpointer):
        self.checkpointer = checkpointer
        self.failure_count = 0
        self.circuit_open = False
        self.last_failure_time = 0
        self.COOLDOWN_PERIOD = 30

    def _check_circuit(self):
        if self.circuit_open:
            if time.time() - self.last_failure_time > self.COOLDOWN_PERIOD:
                self.circuit_open = False
                self.failure_count = 0
            else:
                raise CircuitBreakerOpenException("[CIRCUIT_OPEN] LLM API Circuit Breaker Active")

    def invoke_agent_with_retry(self, state: dict, config: dict):
        self._check_circuit()
        
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_none(),  
            retry=retry_if_exception_type((LLMRateLimitError, LLMTimeoutError)),
            reraise=True
        )
        def _execute():
            return self._call_llm_execution(state)

        try:
            result = _execute()
            self.failure_count = 0
            return result
        except (LLMRateLimitError, LLMTimeoutError) as e:
            self.failure_count += 1
            if self.failure_count >= 5:
                self.circuit_open = True
                self.last_failure_time = time.time()
            raise e

    def _call_llm_execution(self, state: dict):
        return {"status": "SUCCESS", "healed_payload": state.get("payload")}
