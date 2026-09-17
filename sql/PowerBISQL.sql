-- ============================================================================
-- PowerBISQL.sql
-- Run this file ONCE against your local Postgres (hospital_dw database) AFTER
-- the pipeline has loaded analytics.* tables at least one time.
--
-- HOW TO RUN (Postgres is already local, no Docker needed for this step):
--   psql -U postgres -d hospital_dw -f sql/PowerBISQL.sql
--   (or open it in pgAdmin4 and click "Execute")
--
-- WHAT IT DOES:
-- Creates a set of report-ready VIEWS in a new "reporting" schema. Views (not
-- raw tables) are what you point Power BI Desktop at, so you can change the
-- underlying logic here without ever touching your Power BI file.
--
-- IN POWER BI DESKTOP:
--   Get Data -> PostgreSQL database
--   Server:   localhost   (or 127.0.0.1)
--   Database: hospital_dw
--   Then select the "reporting" schema and import the views below.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS reporting;

-- 1) Patient overview: counts, age buckets, registrations over time
CREATE OR REPLACE VIEW reporting.vw_patient_overview AS
SELECT
    patient_id,
    gender,
    age,
    CASE
        WHEN age < 18 THEN '0-17'
        WHEN age BETWEEN 18 AND 35 THEN '18-35'
        WHEN age BETWEEN 36 AND 55 THEN '36-55'
        WHEN age BETWEEN 56 AND 75 THEN '56-75'
        ELSE '76+'
    END AS age_group,
    city,
    insurance_type,
    registration_date,
    date_trunc('month', registration_date) AS registration_month
FROM analytics.dim_patients;

-- 2) Appointments: scheduled / completed / cancelled, by doctor & department
CREATE OR REPLACE VIEW reporting.vw_appointments AS
SELECT
    a.appointment_id,
    a.appointment_date,
    date_trunc('month', a.appointment_date) AS appointment_month,
    a.status,
    a.visit_type,
    a.patient_id,
    a.doctor_id,
    d.department,
    d.specialization
FROM analytics.fact_appointments a
LEFT JOIN analytics.dim_doctors d ON a.doctor_id = d.doctor_id;

-- 3) Admissions: by department, with length of stay
CREATE OR REPLACE VIEW reporting.vw_admissions AS
SELECT
    admission_id,
    patient_id,
    department,
    admission_date,
    discharge_date,
    length_of_stay_days,
    date_trunc('month', admission_date) AS admission_month
FROM analytics.fact_admissions_billing;

-- 4) Billing: service charges, insurance covered, total billed, by department
CREATE OR REPLACE VIEW reporting.vw_billing AS
SELECT
    bill_id,
    admission_id,
    patient_id,
    department,
    service_charges,
    insurance_amount,
    total_bill,
    admission_date,
    date_trunc('month', admission_date) AS billing_month
FROM analytics.fact_admissions_billing
WHERE bill_id IS NOT NULL;

-- 5) Pre-aggregated daily metrics (fast-loading cards / trend lines in Power BI)
CREATE OR REPLACE VIEW reporting.vw_daily_admissions AS
SELECT * FROM analytics.agg_daily_admissions;

CREATE OR REPLACE VIEW reporting.vw_daily_appointments AS
SELECT * FROM analytics.agg_daily_appointments;

-- 6) One row per pipeline run, useful for a "last refreshed" card on the dashboard
CREATE OR REPLACE VIEW reporting.vw_pipeline_last_run AS
SELECT status, run_time, message
FROM raw.pipeline_audit
ORDER BY run_time DESC
LIMIT 1;
