WITH raw_data AS (
    SELECT
        event_id,
        source,
        UPPER(TRIM(category)) AS category_code,
        title,
        content,
        CAST(created_at AS TIMESTAMP) AS created_at
    FROM {{ source('iceberg_raw', 'raw_events_iceberg') }}
    WHERE event_id IS NOT NULL
)
SELECT
    event_id,
    source,
    COALESCE(category_code, 'UNKNOWN') AS category_code,
    title,
    content,
    created_at,
    CAST(created_at AS DATE) AS event_date
FROM raw_data
