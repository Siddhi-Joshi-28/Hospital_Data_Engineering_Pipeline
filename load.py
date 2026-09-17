"""
STAGE 5 — LOAD
Reads the cleaned Parquet files produced by transform_spark.py and loads them
into Postgres:
  - staging.*   -> cleaned, 1-to-1 versions of the source tables
  - analytics.* -> fact/dimension tables ready for Power BI / Streamlit
"""
from pathlib import Path
import pandas as pd
from sqlalchemy import text

from db import get_engine
from logger import get_logger

logger = get_logger(__name__)
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def parquet_to_df(name: str) -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / name)


def load_staging(engine):
    for table in ["patients", "doctors", "appointments", "admissions", "billing"]:
        df = parquet_to_df(table)
        df.to_sql(table, engine, schema="staging", if_exists="replace", index=False)
        logger.info(f"Loaded {len(df)} rows into staging.{table}")


def load_analytics(engine):
    dim_patients = parquet_to_df("patients")
    dim_doctors = parquet_to_df("doctors")
    fact_appointments = parquet_to_df("appointments")
    fact_admissions = parquet_to_df("admissions_billing")
    daily_admissions = parquet_to_df("daily_admissions")
    daily_appointments = parquet_to_df("daily_appointments")

    dim_patients.to_sql("dim_patients", engine, schema="analytics", if_exists="replace", index=False)
    dim_doctors.to_sql("dim_doctors", engine, schema="analytics", if_exists="replace", index=False)
    fact_appointments.to_sql("fact_appointments", engine, schema="analytics", if_exists="replace", index=False)
    fact_admissions.to_sql("fact_admissions_billing", engine, schema="analytics", if_exists="replace", index=False)
    daily_admissions.to_sql("agg_daily_admissions", engine, schema="analytics", if_exists="replace", index=False)
    daily_appointments.to_sql("agg_daily_appointments", engine, schema="analytics", if_exists="replace", index=False)

    logger.info("Loaded analytics.dim_patients, dim_doctors, fact_appointments, "
                "fact_admissions_billing, agg_daily_admissions, agg_daily_appointments")


def record_audit_run(engine, status: str, message: str = ""):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO raw.pipeline_audit (run_time, status, message)
                VALUES (now(), :status, :message)
            """),
            {"status": status, "message": message},
        )


def main():
    engine = get_engine()
    try:
        load_staging(engine)
        load_analytics(engine)
        record_audit_run(engine, "SUCCESS", "Pipeline completed")
        logger.info("Load stage complete")
    except Exception as e:
        record_audit_run(engine, "FAILED", str(e))
        logger.error(f"Load stage failed: {e}")
        raise


if __name__ == "__main__":
    main()
