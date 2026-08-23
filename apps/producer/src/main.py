import json
import random
import time
import uuid
from datetime import datetime
from kafka import KafkaProducer
from faker import Faker

fake = Faker()

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all'
)

TOPIC_NAME = 'raw-intelligence-stream'
CATEGORIES = ['TECH', 'FINANCE', 'AI', 'MARKET']
SOURCES = ['news_api', 'rss_feed', 'web_scraper']

def generate_event():
    return {
        "event_id": str(uuid.uuid4()),
        "source": random.choice(SOURCES),
        "category": random.choice(CATEGORIES),
        "title": fake.sentence(nb_words=6),
        "content": fake.text(max_nb_chars=200),
        "created_at": datetime.utcnow().isoformat() + "Z"  # pyright: ignore[reportDeprecated]
    }

def main():
    print(f"Starting producer on topic: {TOPIC_NAME}")
    cache_event = None

    while True:
        try:
            if cache_event and random.random() < 0.1:
                event = cache_event
                print(f"Duplicate event_id: {event['event_id']}")
            else:
                event = generate_event()
                cache_event = event
            
            producer.send(TOPIC_NAME, value=event)
            print(f"Sent {event['category']} | {event['event_id']}")
            time.sleep(0.5)
        except KeyboardInterrupt:
            break
    
    producer.flush()


if __name__ == '__main__':
    main()
