from datetime import timedelta
from feast import (
    Entity,
    Field,
    FeatureView,
    KafkaSource,
    RedisOnlineStore
)
from feast.types import Float32, Int64, String

event_entitiy = Entity(name="event_id", value_type=String)

online_store = RedisOnlineStore(connection_string="redis:6379")

event_features_view = FeatureView(
    name="event_realtime_features",
    entities=[event_entitiy],
    ttl=timedelta(days=1),
    schema=[
        Field(name="category_frequency_1h", type=Int64),
        Field(name="sentiment_score", type=Float32),
        Field(name="anomaly_score", type=Float32), 
    ],
    online=True,
    source=KafkaSource(
        name="kafka_feature_stream",
        kafka_bootstrap_servers="kafka:29092",
        topic="processed-features-stream",
        timestamp_field="ts",    
    )
)
