{{ config(
    materialized='table',
    table_type='iceberg'
) }}

SELECT
    MD5(category_code) AS category_key,
    category_code,
    CASE 
        WHEN category_code = 'TECH' THEN 'Technology & Software'
        WHEN category_code = 'FINANCE' THEN 'Financial Markets & Investment'
        WHEN category_code = 'AI' THEN 'Artificial Intelligence'
        ELSE 'General Market'
    END AS category_description,
    CURRENT_TIMESTAMP() AS updated_at
FROM (
    SELECT DISTINCT category_code 
    FROM {{ ref('stg_events') }}
)
