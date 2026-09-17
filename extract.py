"""
STAGE 2 — EXTRACT / INGEST
Reads the 5 raw CSV files and loads them AS-IS into the `raw` schema in Postgres.
Nothing is cleaned here on purpose — `raw` is meant to be a faithful copy of the
source files. Also writes one row per file into raw.ingestion_metadata so you can
always answer "when was this file loaded, how many rows, did it succeed?".
"""
from pathlib import Path
from datetime import datetime
import pandas as pd
from sqlalchemy import text

from db import get_engine
from logger import get_logger

logger = get_logger(__name__)
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

FILES = {
    "patients": "patients.csv",
    "doctors": "doctors.csv",
    "appointments": "appointments.csv",
    "admissions": "admissions.csv",
    "billing": "billing.csv",
}


def load_file_to_raw(engine, table_name: str, file_name: str):
    path = RAW_DIR / file_name
    df = pd.read_csv(path)
    df.to_sql(table_name, engine, schema="raw", if_exists="replace", index=False)

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO raw.ingestion_metadata (file_name, ingested_at, row_count, status)
                VALUES (:file_name, :ingested_at, :row_count, :status)
            """),
            {
                "file_name": file_name,
                "ingested_at": datetime.now(),
                "row_count": len(df),
                "status": "SUCCESS",
            },
        )
    logger.info(f"Ingested {len(df)} rows from {file_name} into raw.{table_name}")


def main():
    engine = get_engine()
    for table_name, file_name in FILES.items():
        load_file_to_raw(engine, table_name, file_name)


if __name__ == "__main__":
    main()
