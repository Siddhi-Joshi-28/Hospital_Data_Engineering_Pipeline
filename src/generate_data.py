"""
STAGE 1 — DATA GENERATION
Creates 2,000 synthetic hospital records across 5 related CSV files in data/raw/.
IDs are shared across files on purpose (appointments reference real patient_id /
doctor_id) so later stages can practice real foreign-key validation.
Some rows are deliberately broken (missing values, duplicate IDs) so the
validate.py stage has something real to catch.
"""
import random
from pathlib import Path
import pandas as pd
from faker import Faker

from logger import get_logger

logger = get_logger(__name__)
fake = Faker()
Faker.seed(42)
random.seed(42)

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

N_PATIENTS = 500
N_DOCTORS = 50
N_APPOINTMENTS = 800
N_ADMISSIONS = 300
N_BILLING = 350

DEPARTMENTS = ["Cardiology", "Neurology", "Orthopedics", "Pediatrics",
               "Oncology", "General Medicine", "Emergency", "Radiology"]
INSURANCE_TYPES = ["Private", "Government", "None", "Corporate"]
VISIT_TYPES = ["New", "Follow-up", "Emergency", "Consultation"]
APPOINTMENT_STATUS = ["Scheduled", "Completed", "Cancelled", "No-show"]


def generate_patients():
    rows = []
    for i in range(1, N_PATIENTS + 1):
        rows.append({
            "patient_id": i,
            "name": fake.name(),
            "age": random.randint(0, 95),
            "gender": random.choice(["Male", "Female", "Other"]),
            "city": fake.city(),
            "registration_date": fake.date_between(start_date="-3y", end_date="today"),
            "insurance_type": random.choice(INSURANCE_TYPES),
        })
    df = pd.DataFrame(rows)
    # inject a few missing ages / duplicate id on purpose, for validate.py to catch
    df.loc[df.sample(frac=0.02, random_state=1).index, "age"] = None
    dup = df.sample(3, random_state=2).copy()
    df = pd.concat([df, dup], ignore_index=True)
    return df


def generate_doctors():
    rows = []
    for i in range(1, N_DOCTORS + 1):
        rows.append({
            "doctor_id": i,
            "name": fake.name(),
            "department": random.choice(DEPARTMENTS),
            "specialization": fake.job(),
            "experience_years": random.randint(1, 35),
        })
    return pd.DataFrame(rows)


def generate_appointments(patient_ids, doctor_ids):
    rows = []
    for i in range(1, N_APPOINTMENTS + 1):
        rows.append({
            "appointment_id": i,
            "patient_id": random.choice(patient_ids),
            "doctor_id": random.choice(doctor_ids),
            "appointment_date": fake.date_between(start_date="-2y", end_date="today"),
            "status": random.choice(APPOINTMENT_STATUS),
            "visit_type": random.choice(VISIT_TYPES),
        })
    df = pd.DataFrame(rows)
    # a few rows referencing a non-existent patient, to test FK validation
    bad_idx = df.sample(5, random_state=3).index
    df.loc[bad_idx, "patient_id"] = 99999
    return df


def generate_admissions(patient_ids):
    rows = []
    for i in range(1, N_ADMISSIONS + 1):
        admit_date = fake.date_between(start_date="-2y", end_date="today")
        stay_days = random.randint(1, 20)
        rows.append({
            "admission_id": i,
            "patient_id": random.choice(patient_ids),
            "department": random.choice(DEPARTMENTS),
            "admission_date": admit_date,
            "discharge_date": admit_date + pd.Timedelta(days=stay_days),
        })
    return pd.DataFrame(rows)


def generate_billing(patient_ids, admission_ids):
    rows = []
    for i in range(1, N_BILLING + 1):
        service_charges = round(random.uniform(500, 20000), 2)
        insurance_amount = round(service_charges * random.uniform(0, 0.8), 2)
        rows.append({
            "bill_id": i,
            "patient_id": random.choice(patient_ids),
            "admission_id": random.choice(admission_ids + [None] * 5),  # some outpatient bills
            "service_charges": service_charges,
            "insurance_amount": insurance_amount,
            "total_bill": round(service_charges - insurance_amount, 2),
        })
    return pd.DataFrame(rows)


def main():
    patients = generate_patients()
    doctors = generate_doctors()
    appointments = generate_appointments(patients["patient_id"].tolist(), doctors["doctor_id"].tolist())
    admissions = generate_admissions(patients["patient_id"].tolist())
    billing = generate_billing(patients["patient_id"].tolist(), admissions["admission_id"].tolist())

    patients.to_csv(RAW_DIR / "patients.csv", index=False)
    doctors.to_csv(RAW_DIR / "doctors.csv", index=False)
    appointments.to_csv(RAW_DIR / "appointments.csv", index=False)
    admissions.to_csv(RAW_DIR / "admissions.csv", index=False)
    billing.to_csv(RAW_DIR / "billing.csv", index=False)

    total = len(patients) + len(doctors) + len(appointments) + len(admissions) + len(billing)
    logger.info(f"Generated {total} synthetic records into {RAW_DIR}")


if __name__ == "__main__":
    main()
