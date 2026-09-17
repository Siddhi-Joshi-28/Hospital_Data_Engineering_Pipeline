"""
STAGE 3 — VALIDATE
Runs simple data-quality checks against the raw tables:
  - required fields not null
  - no duplicate primary keys
  - foreign keys point to a real parent row (e.g. every appointment.patient_id
    exists in patients)
Rows that fail are written to data/rejected/<table>_rejected.csv for inspection,
and a summary is printed/logged. This mirrors what the "Data quality and audit"
stage of the roadmap asks for.
"""
from pathlib import Path
import pandas as pd
from db import get_engine
from logger import get_logger

logger = get_logger(__name__)
REJECTED_DIR = Path(__file__).resolve().parent.parent / "data" / "rejected"
REJECTED_DIR.mkdir(parents=True, exist_ok=True)


def check_table(engine, table, required_cols, pk_col):
    df = pd.read_sql(f"SELECT * FROM raw.{table}", engine)
    issues = pd.DataFrame()

    # 1) required fields missing
    missing = df[df[required_cols].isnull().any(axis=1)]
    issues = pd.concat([issues, missing])

    # 2) duplicate primary key
    dups = df[df.duplicated(subset=[pk_col], keep=False)]
    issues = pd.concat([issues, dups])

    issues = issues.drop_duplicates()
    if not issues.empty:
        out_path = REJECTED_DIR / f"{table}_rejected.csv"
        issues.to_csv(out_path, index=False)
        logger.warning(f"{table}: {len(issues)} problem row(s) written to {out_path}")
    else:
        logger.info(f"{table}: no issues found")
    return len(df), len(issues)


def check_foreign_key(engine, child_table, fk_col, parent_table, parent_pk):
    child = pd.read_sql(f"SELECT * FROM raw.{child_table}", engine)
    parent_ids = set(pd.read_sql(f"SELECT {parent_pk} FROM raw.{parent_table}", engine)[parent_pk])
    orphans = child[~child[fk_col].isin(parent_ids) & child[fk_col].notnull()]
    if not orphans.empty:
        out_path = REJECTED_DIR / f"{child_table}_orphan_{fk_col}.csv"
        orphans.to_csv(out_path, index=False)
        logger.warning(
            f"{child_table}.{fk_col}: {len(orphans)} row(s) reference a missing "
            f"{parent_table}.{parent_pk} -> {out_path}"
        )
    return len(orphans)


def main():
    engine = get_engine()
    check_table(engine, "patients", ["patient_id", "age", "gender"], "patient_id")
    check_table(engine, "doctors", ["doctor_id", "department"], "doctor_id")
    check_table(engine, "appointments", ["appointment_id", "patient_id", "doctor_id"], "appointment_id")
    check_table(engine, "admissions", ["admission_id", "patient_id", "department"], "admission_id")
    check_table(engine, "billing", ["bill_id", "patient_id", "total_bill"], "bill_id")

    check_foreign_key(engine, "appointments", "patient_id", "patients", "patient_id")
    check_foreign_key(engine, "appointments", "doctor_id", "doctors", "doctor_id")
    check_foreign_key(engine, "admissions", "patient_id", "patients", "patient_id")
    check_foreign_key(engine, "billing", "patient_id", "patients", "patient_id")

    logger.info("Validation stage complete")


if __name__ == "__main__":
    main()
