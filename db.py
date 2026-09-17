"""
One place that knows how to talk to Postgres.
Reads connection info from environment variables (set in .env / docker-compose.yml)
so no password is ever hard-coded in the scripts.
"""
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "hospital_dw")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")


def get_engine():
    """
    Returns a SQLAlchemy engine.
    - Running this script directly on your laptop -> PG_HOST=localhost works.
    - Running inside an Airflow/Streamlit container -> PG_HOST=host.docker.internal
      lets the container reach the Postgres that lives on your host machine.
    """
    url = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    return create_engine(url)
