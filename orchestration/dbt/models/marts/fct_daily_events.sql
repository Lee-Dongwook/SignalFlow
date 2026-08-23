{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['event_date', 'category_key', 'source'],
    table_type='iceberg'
) }}

WITH stg AS (
    SELECT * FROM {{ ref('stg_events') }}
    {% if is_incremental() %}
      WHERE event_date >= DATE_SUB(CURRENT_DATE(), 3)
    {% endif %}
),
dim_cat AS (
    SELECT * FROM {{ ref('dim_category') }}
)

SELECT
    s.event_date,
    c.category_key,
    s.source,
    COUNT(s.event_id) AS total_event_count,
    COUNT(DISTINCT s.event_id) AS unique_event_count,
    CURRENT_TIMESTAMP() AS batch_processed_at
FROM stg s
LEFT JOIN dim_cat c ON s.category_code = c.category_code
GROUP BY
    s.event_date,
    c.category_key,
    s.source
