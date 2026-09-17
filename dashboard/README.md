# Dashboard notes

Two dashboards read from the SAME `reporting.*` views (see `sql/PowerBISQL.sql`),
so Power BI and Streamlit will always show matching numbers.

## Power BI Desktop
1. Run `sql/PowerBISQL.sql` once against your local `hospital_dw` database.
2. In Power BI Desktop: Get Data -> PostgreSQL database -> server `localhost`,
   database `hospital_dw` -> select the `reporting` schema -> Load.
3. Build visuals on top of `vw_patient_overview`, `vw_appointments`,
   `vw_admissions`, `vw_billing`.

## Streamlit (runs in Docker)
`docker compose up streamlit` then open http://localhost:8501
