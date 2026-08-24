import json
from kafka import KafkaConsumer, KafkaProducer
from src.graph import build_dlq_healing_graph

def run_dlq_self_healing_worker():
    consumer = KafkaConsumer(
        'dlq-intelligence-stream',
        bootstrap_servers=["kafka:29092"],
        auto_offset_reset='earliset',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    producer = KafkaProducer(
        bootstrap_servers=['kafka:29092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    app = build_dlq_healing_graph()
    print("Multi Agent DLQ Self-Healing Worker Started")

    for message in consumer:
        dlq_event = message.value
        raw_payload = json.loads(dlq_event.get("raw_data", "{}"))
        error_msg = dlq_event.get("error_message", "Unknown Error")

        initial_state = {
            "raw_payload": raw_payload,
            "error_message": error_msg,
            "next_agent": "",
            "corrected_payload": None,
            "is_repaired": False,
            "retry_count": 0,
            "logs": []
        }

        result_state = app.invoke(initial_state)

        if result_state["is_repaired"] and result_state["corrected_payload"]:
            producer.send('raw-intelligence-stream', value=result_state["corrected_payload"])
            producer.flush()
            print(f"Success Self-Healed & Replayed: {result_state['corrected_payload'].get('event_id')}")
        else:
            print(f"Manual Intervention Required: {error_msg}")

if __name__ == "__main__":
    run_dlq_self_healing_worker()
