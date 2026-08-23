CREATE DATABASE IF NOT EXISTS intelligence;

CREATE TABLE IF NOT EXISTS intelligence.events_raw
(
    event_id String,
    source LowCardinality(String),
    category LowCardinality(String),
    title String,
    content String,
    created_at DateTime,
    processed_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(processed_at)
ORDER BY (category, created_at, event_id);

CREATE TABLE IF NOT EXISTS intelligence.metrics_per_minute_agg
(
    window_start DateTime
    category LowCardinality(String),
    source LowCardinality(String),
    event_count UInt64
)
ENGINE = SummingMergeTree()
ORDER BY (window_start, category, source);

CREATE MATERIALIZED VIEW IF NOT EXISTS intelligence.mv_metrics_per_minute
TO intelligence.metrics_per_minute_agg AS
SELECT
    toStartOfMinute(created_at) AS window_start,
    category,
    source,
    count() AS event_count
FROM intelligence.events_raw
GROUP BY
    window_start,
    category,
    source;
