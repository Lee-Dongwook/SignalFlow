from prometheus_client import Counter, Histogram, Gauge, start_http_server

DLQ_HEAL_ATTEMPTS_TOTAL = Counter(
    "dlq_heal_attempts_total",
    "Total number of DLQ event healing attempts",
    ["agent_name", "status"] 
)

DLQ_HEAL_DURATION_SECONDS = Histogram(
    "dlq_heal_duration_seconds",
    "Time spent healing DLQ events in seconds",
    ["agent_name"]
)

CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Current status of the agent circuit breaker (1=Open, 0=Closed)",
    ["agent_name"]
)

def start_metrics_server(port: int = 8002):
    start_http_server(port)
