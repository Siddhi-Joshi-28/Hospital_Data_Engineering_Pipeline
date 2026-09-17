-- raw.* mirrors the source CSV files exactly, plus 2 pipeline-control tables.
-- Note: extract.py actually creates/replaces these tables automatically via
-- pandas.to_sql(), so this file is mainly for reference / manual runs.

CREATE TABLE IF NOT EXISTS raw.ingestion_metadata (
    id SERIAL PRIMARY KEY,
    file_name TEXT,
    ingested_at TIMESTAMP,
    row_count INT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS raw.pipeline_audit (
    id SERIAL PRIMARY KEY,
    run_time TIMESTAMP DEFAULT now(),
    status TEXT,
    message TEXT
);
