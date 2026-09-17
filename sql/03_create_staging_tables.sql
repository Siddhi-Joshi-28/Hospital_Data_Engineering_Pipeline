-- staging.* holds cleaned, de-duplicated, 1-to-1 versions of the raw tables.
-- These are ALSO created/replaced automatically by load.py (via pandas
-- to_sql with if_exists="replace"), so you do NOT need to run this file
-- for the pipeline to work — load.py will (re)create these tables on every
-- run using the exact structure below. This file exists so the schema is
-- reviewable on its own, independent of the Python code.

CREATE TABLE IF NOT EXISTS staging.patients (
    patient_id       INTEGER PRIMARY KEY,
    name              TEXT,
    age               INTEGER,
    gender            TEXT,
    city              TEXT,
    registration_date DATE,
    insurance_type    TEXT
);

CREATE TABLE IF NOT EXISTS staging.doctors (
    doctor_id         INTEGER PRIMARY KEY,
    name              TEXT,
    department        TEXT,
    specialization    TEXT,
    experience_years  INTEGER
);

CREATE TABLE IF NOT EXISTS staging.appointments (
    appointment_id    INTEGER PRIMARY KEY,
    patient_id        INTEGER REFERENCES staging.patients(patient_id),
    doctor_id         INTEGER REFERENCES staging.doctors(doctor_id),
    appointment_date  DATE,
    status            TEXT,
    visit_type        TEXT
);

CREATE TABLE IF NOT EXISTS staging.admissions (
    admission_id         INTEGER PRIMARY KEY,
    patient_id           INTEGER REFERENCES staging.patients(patient_id),
    department           TEXT,
    admission_date        DATE,
    discharge_date        DATE,
    length_of_stay_days   INTEGER
);

CREATE TABLE IF NOT EXISTS staging.billing (
    bill_id           INTEGER PRIMARY KEY,
    patient_id        INTEGER REFERENCES staging.patients(patient_id),
    admission_id      INTEGER REFERENCES staging.admissions(admission_id),
    service_charges   NUMERIC(10, 2),
    insurance_amount  NUMERIC(10, 2),
    total_bill        NUMERIC(10, 2)
);