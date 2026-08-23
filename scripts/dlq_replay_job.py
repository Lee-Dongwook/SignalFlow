import json
from kafka import KafkaConsumer, KafkaProducer

def replay_dlq_messages():
    """
    DLQ 격리 데이터를 읽어 수정한 뒤 메인 스트림으로 재발송하는 Replay 스크립트
    """
    consumer = KafkaConsumer(
        'dlq-intelligence-stream',
        bootstrap_servers=['kafka:9092'],
        auto_offset_reset='earliest',
        group_id='dlq-recovery-worker'
    )

    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    replayed_count = 0
    print("Starting DLQ Replay Worker")

    for message in consumer:
        dlq_payload = json.loads(message.value.decode('utf-8'))
        raw_data = json.loads(dlq_payload.get("raw_data", "{}"))

        if "timestamp" not in raw_data or raw_data["timestamp"] is None:
            import time
            raw_data["timestamp"] = int(time.time() * 1000)
        
        producer.send('raw-intelligence-stream', value=raw_data)
        replayed_count += 1
        print(f"Replayed Message ID: {raw_data.get('event_id')} -> Main Topic")

    producer.flush()
    print(f"Completed DLQ Replay. Total Processed: {replayed_count}")

if __name__ == "__main__":
    replay_dlq_messages()
