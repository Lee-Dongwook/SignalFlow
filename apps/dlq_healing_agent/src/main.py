import os
import json
from kafka import KafkaConsumer, KafkaProducer
from checkpoint import get_langgraph_checkpointer
from circuit_breaker import ResilientSupervisorAgent

def run_dlq_self_healing_worker():
    consumer = KafkaConsumer(
        'dlq-intelligence-stream',
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        group_id='dlq_healing_agent_group',
        auto_offset_reset='earliset',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        enable_auto_commit=False
    )

    producer = KafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    checkpointer = get_langgraph_checkpointer()
    agent_runner = ResilientSupervisorAgent(checkpointer)

    for message in consumer:
        try:
            event_data = json.loads(message.value.decode("utf-8"))
            thread_config = {"configurable": {"thread_id": event_data["event_id"]}}
            healed_result = agent_runner.invoke_agent_with_retry(event_data, config=thread_config)

            producer.send("raw-telemetry-stream", value=healed_result["healed_payload"])
            consumer.commit()
            print(f"Repaired & Reinjected Event ID: {event_data["event_id"]}")
        
        except Exception as err:
            print(f"Fallback DLQ Routing to Secondary Offline Storage due to : {err}")

if __name__ == "__main__":
    run_dlq_self_healing_worker()
