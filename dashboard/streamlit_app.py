"""
Streamlit dashboard — reads directly from the `reporting` views created by
sql/PowerBISQL.sql (same views Power BI uses, so both tools always agree).
Runs in its own Docker container; connects to your LOCAL Postgres via
host.docker.internal (see docker-compose.yml).
"""
import os
import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine

st.set_page_config(page_title="Hospital Analytics", layout="wide")

PG_HOST = os.getenv("PG_HOST", "host.docker.internal")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "hospital_dw")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")


@st.cache_resource
def get_engine():
    url = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    return create_engine(url)


@st.cache_data(ttl=300)
def load(query: str) -> pd.DataFrame:
    return pd.read_sql(query, get_engine())


st.title("🏥 Hospital Data Engineering Platform")

last_run = load("SELECT * FROM reporting.vw_pipeline_last_run")
if not last_run.empty:
    st.caption(
        f"Last pipeline run: {last_run.iloc[0]['status']} at {last_run.iloc[0]['run_time']}"
    )

patients = load("SELECT * FROM reporting.vw_patient_overview")
appointments = load("SELECT * FROM reporting.vw_appointments")
admissions = load("SELECT * FROM reporting.vw_admissions")
billing = load("SELECT * FROM reporting.vw_billing")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Patients", len(patients))
col2.metric("Total Appointments", len(appointments))
col3.metric("Total Admissions", len(admissions))
col4.metric("Total Billed", f"${billing['total_bill'].sum():,.0f}")

tab1, tab2, tab3, tab4 = st.tabs(["Patients", "Appointments", "Admissions", "Billing"])

with tab1:
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.histogram(patients, x="age_group", title="Patients by Age Group"),
                     use_container_width=True)
    c2.plotly_chart(px.pie(patients, names="insurance_type", title="Patients by Insurance Type"),
                     use_container_width=True)
    st.plotly_chart(
        px.line(patients.groupby("registration_month").size().reset_index(name="count"),
                x="registration_month", y="count", title="Registrations Over Time"),
        use_container_width=True,
    )

with tab2:
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(appointments["status"].value_counts().reset_index(),
                            x="status", y="count", title="Appointments by Status"),
                     use_container_width=True)
    c2.plotly_chart(px.bar(appointments["department"].value_counts().reset_index(),
                            x="department", y="count", title="Appointments by Department"),
                     use_container_width=True)

with tab3:
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(admissions["department"].value_counts().reset_index(),
                            x="department", y="count", title="Admissions by Department"),
                     use_container_width=True)
    c2.plotly_chart(px.box(admissions, x="department", y="length_of_stay_days",
                            title="Length of Stay by Department"),
                     use_container_width=True)

with tab4:
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(billing.groupby("department")["total_bill"].sum().reset_index(),
                            x="department", y="total_bill", title="Total Billing by Department"),
                     use_container_width=True)
    c2.plotly_chart(px.scatter(billing, x="service_charges", y="insurance_amount",
                                color="department", title="Service Charges vs Insurance Covered"),
                     use_container_width=True)
