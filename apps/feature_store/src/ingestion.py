import json
import redis
from kafka import KafkaConsumer

class FeatureIngestionWorker:
    def __init__(self):
        self.redis_client = redis.Redis(host="redis", port=6379, db=0)
        self.consumer = KafkaConsumer(
            'processed-features-stream',
            bootstrap_servers=['kafka:29092'],
            value_deserialize=lambda m:json.loads(m.decode('utf-8'))
        )

    def run(self):
        print("Feature Ingestion Worker Started")
        for msg in self.consumer:
            data = msg.value
            event_id = data.get("event_id")

            redis_key = f"feature:event:{event_id}"
            self.redis_client.hset(redis_key, mapping={
                "category_frequency_1h": data.get("category_frequency_1h", 0),
                "sentiment_score": data.get("sentiment_score", 0.0),
                "anomaly_score": data.get("anomaly_score", 0.0)
            })
            self.redis_client.expire(redis_key, 86400)
