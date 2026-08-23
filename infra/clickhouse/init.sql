CREATE DATABASE IF NOT EXISTS intelligence;

CREATE TABLE IF NOT EXISTS intelligence.realtime_metrics
(
    event_id UUID,
    source LowCardinality(String),
    category LowCardinality(String),
    title String,
    content String,
    sentiment_score Float32 DEFAULT 0.0,
    created_at DateTime,
    processed_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(processed_at)
ORDER BY (category, created_at, event_id);
