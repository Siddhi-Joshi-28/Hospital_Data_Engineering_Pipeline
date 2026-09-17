-- Already included in 02_create_raw_tables.sql (raw.pipeline_audit).
-- Query it any time to see pipeline run history:
SELECT * FROM raw.pipeline_audit ORDER BY run_time DESC;
