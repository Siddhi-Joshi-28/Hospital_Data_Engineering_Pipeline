-- analytics.* = star-schema-ish tables built for reporting.
-- dim_patients, dim_doctors            -> dimension tables
-- fact_appointments, fact_admissions_billing -> fact tables
-- agg_daily_admissions, agg_daily_appointments -> pre-aggregated tables for fast dashboards
--
-- These are ALSO created/replaced automatically by load.py (via pandas
-- to_sql with if_exists="replace"), so you do NOT need to run this file
-- for the pipeline to work — load.py will (re)create these tables on every
-- run using the exact structure below. This file exists so the schema is
-- reviewable on its own, independent of the Python code.

CREATE TABLE IF NOT EXISTS analytics.dim_patients (
    patient_id        INTEGER PRIMARY KEY,
    name              TEXT,
    age               INTEGER,
    gender            TEXT,
    city              TEXT,
    registration_date DATE,
    insurance_type    TEXT
);

CREATE TABLE IF NOT EXISTS analytics.dim_doctors (
    doctor_id         INTEGER PRIMARY KEY,
    name              TEXT,
    department        TEXT,
    specialization    TEXT,
    experience_years  INTEGER
);

CREATE TABLE IF NOT EXISTS analytics.fact_appointments (
    appointment_id    INTEGER PRIMARY KEY,
    patient_id        INTEGER REFERENCES analytics.dim_patients(patient_id),
    doctor_id         INTEGER REFERENCES analytics.dim_doctors(doctor_id),
    appointment_date  DATE,
    status            TEXT,
    visit_type        TEXT
);

-- One row per admission, left-joined with its billing record (some
-- admissions have no bill yet, so bill_id / charges can be NULL).
CREATE TABLE IF NOT EXISTS analytics.fact_admissions_billing (
    admission_id         INTEGER PRIMARY KEY,
    patient_id           INTEGER REFERENCES analytics.dim_patients(patient_id),
    department           TEXT,
    admission_date        DATE,
    discharge_date        DATE,
    length_of_stay_days   INTEGER,
    bill_id               INTEGER,
    service_charges       NUMERIC(10, 2),
    insurance_amount      NUMERIC(10, 2),
    total_bill            NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS analytics.agg_daily_admissions (
    admission_date      DATE,
    department           TEXT,
    admissions_count     INTEGER,
    avg_length_of_stay   NUMERIC(6, 2)
);

CREATE TABLE IF NOT EXISTS analytics.agg_daily_appointments (
    appointment_date   DATE,
    status              TEXT,
    appointment_count   INTEGER
);