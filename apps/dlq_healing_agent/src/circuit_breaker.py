import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class LLMRateLimitError(Exception): pass
class LLMTimeoutError(Exception): pass

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
                raise Exception("Circuit open, LLM API Circuit Breaker Active")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((LLMRateLimitError, LLMTimeoutError)),
        reraise=True
    )
    def invoke_agent_with_retry(self, state:dict, config:dict):
        self._check_circuit()

        try:
            result = self._call_llm_execution(state)
            self.failure_count = 0
            return result        
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= 5:
                self.circuit_open = True
                self.last_failure_time = time.time()
            raise e
            
    def _call_llm_execution(self, state: dict):
        return {"status": "SUCCESS", "healed_payload": state.get("payload")}
