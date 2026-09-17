"""
Basic sanity checks you can run with: pytest tests/
These check the OUTPUT of the pipeline (the Postgres tables), not the code
logic itself — run generate/extract/validate/load first, or run this after
a full Airflow DAG run.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
from db import get_engine


def test_patients_no_duplicate_ids():
    engine = get_engine()
    df = pd.read_sql("SELECT patient_id FROM staging.patients", engine)
    assert df["patient_id"].is_unique


def test_appointments_reference_real_patients():
    engine = get_engine()
    appts = pd.read_sql("SELECT patient_id FROM staging.appointments", engine)
    patients = pd.read_sql("SELECT patient_id FROM staging.patients", engine)
    assert appts["patient_id"].isin(patients["patient_id"]).all()


def test_billing_total_matches_charges_minus_insurance():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM staging.billing", engine)
    diff = (df["service_charges"] - df["insurance_amount"] - df["total_bill"]).abs()
    assert (diff < 0.01).all()
