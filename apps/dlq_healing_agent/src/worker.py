import time

from apps.dlq_healing_agent.src.metrics import (
    CIRCUIT_BREAKER_STATE,
    DLQ_HEAL_ATTEMPTS_TOTAL,
    DLQ_HEAL_DURATION_SECONDS,
    start_metrics_server,
)


class SchemaAgentWorker:
    def __init__(self, agent_name: str = "SchemaAgent"):
        self.agent_name = agent_name
        self.is_circuit_open = False

    def heal_event(self, event_payload: dict) -> bool:
        start_time = time.time()

        if self.is_circuit_open:
            CIRCUIT_BREAKER_STATE.labels(agent_name=self.agent_name).set(1)
            DLQ_HEAL_ATTEMPTS_TOTAL.labels(agent_name=self.agent_name, status="circuit_broken").inc()

        try:
            success = True
            
            if success:
                DLQ_HEAL_ATTEMPTS_TOTAL.labels(agent_name=self.agent_name, status="success").inc()
                CIRCUIT_BREAKER_STATE.labels(agent_name=self.agent_name).set(0)
            else:
                DLQ_HEAL_ATTEMPTS_TOTAL.labels(agent_name=self.agent_name, status="failed").inc()
        
        finally:
            duration = time.time() - start_time
            DLQ_HEAL_DURATION_SECONDS.labels(agent_name=self.agent_name).observe(duration)

if __name__ == "__main__":
    start_metrics_server(port=8002)
    print("DLQ Healing Agent Prometheus Metrics Server running on :8002")
