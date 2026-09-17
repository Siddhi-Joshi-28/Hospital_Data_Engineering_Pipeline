# Architecture

```
Synthetic hospital data (Faker, generate_data.py)
        |
        v
Python ingestion (extract.py) --> raw schema (Postgres, local)
        |
        v
Validation (validate.py) --> data/rejected/*.csv for bad rows
        |
        v
Airflow DAG orchestrates all of the above + the two steps below
        |
        v
Spark transform (transform_spark.py) --> data/processed/*.parquet
        |
        v
Load (load.py) --> staging schema, analytics schema (Postgres, local)
        |
        v
reporting schema (sql/PowerBISQL.sql, views only)
        |
        +--> Power BI Desktop (reads reporting.* directly)
        +--> Streamlit dashboard, in Docker (reads reporting.* directly)
```

## What runs where
| Component            | Runs in Docker? | Notes |
|-----------------------|:---:|---|
| PostgreSQL (hospital_dw) | No | Already installed on your laptop |
| Airflow webserver/scheduler | Yes | Needs its own small metadata DB (`postgres-airflow`, also in Docker) |
| Spark | No (local mode) | PySpark runs in local mode from within the Airflow container / your machine — a real cluster isn't needed for ~2,000 rows |
| Streamlit dashboard | Yes | `dashboard/Dockerfile` |
| Power BI Desktop | No | Runs on your machine, connects straight to local Postgres |
