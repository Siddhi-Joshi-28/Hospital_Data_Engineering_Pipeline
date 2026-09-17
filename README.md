# Hospital Data Engineering Pipeline

A local, portfolio-ready hospital analytics pipeline: synthetic data ->
Python ingestion -> Airflow orchestration -> Spark transformation ->
PostgreSQL warehouse (raw/staging/analytics/reporting) -> Power BI + Streamlit.

PostgreSQL is assumed to already be installed and running on your machine —
it is NOT part of `docker-compose.yml`.

## What each file does

| Path | What it does |
|---|---|
| `src/generate_data.py` | Creates 2,000 synthetic records (patients, doctors, appointments, admissions, billing) into `data/raw/*.csv` using Faker |
| `src/extract.py` | Loads those CSVs as-is into the `raw` schema in Postgres, logs each file into `raw.ingestion_metadata` |
| `src/validate.py` | Checks nulls, duplicate IDs, and broken foreign keys; writes bad rows to `data/rejected/` |
| `src/transform_spark.py` | Cleans, joins, and aggregates the data with PySpark; writes Parquet to `data/processed/` |
| `src/load.py` | Loads the Parquet files into `staging.*` and `analytics.*` tables; records every run in `raw.pipeline_audit` |
| `src/db.py` | One shared function that builds the Postgres connection from environment variables |
| `src/logger.py` | Shared logging setup used by every script |
| `dags/hospital_pipeline_dag.py` | Airflow DAG chaining all 5 stages above — **only used if you run Option B (Docker)** |
| `sql/01-05_*.sql` | Schema/table creation reference (also done automatically by the Python scripts) |
| `sql/PowerBISQL.sql` | **Run this yourself** in pgAdmin4 to build the `reporting.*` views that Power BI and Streamlit both read from |
| `dashboard/streamlit_app.py` | Streamlit dashboard reading `reporting.*` views |
| `dashboard/Dockerfile` | Builds the Streamlit container — only needed for Option B |
| `docker-compose.yml` | Starts Airflow (+ its own tiny metadata DB) and Streamlit — only needed for Option B |
| `tests/` | pytest checks for data quality and for each pipeline stage |
| `docs/architecture.md` | Diagram + "what runs where" table |

---

## Which tools you need, if you're NOT running Docker

If Docker Desktop isn't running (or you don't want to use it), you can run
every stage of this project directly with Python. Here's exactly what to
install, since some of these are easy to miss:

| Tool | Why you need it | Check it's installed |
|---|---|---|
| **Python 3.11 or 3.12** | Runs every script in `src/` | `python --version` |
| **pip** (comes with Python) | Installs packages | `pip --version` |
| **PostgreSQL + pgAdmin4** | Your data warehouse — already on your machine | Open pgAdmin4, connect to your local server |
| **Java (JDK 8, 11, or 17)** | Required by PySpark — Spark runs on the JVM | `java -version` |
| **`winutils.exe` + `hadoop.dll`** (Windows only) | PySpark needs these to write files locally on Windows | see below |
| **Git Bash** | Recommended terminal — Linux-style commands on Windows | comes with Git for Windows |

**Skip entirely if not using Docker:** Docker Desktop, `docker-compose.yml`,
`dashboard/Dockerfile`, and the Airflow DAG (`dags/hospital_pipeline_dag.py`)
— you'll trigger each stage manually instead of through Airflow.

### Windows-only extra step: winutils.exe + hadoop.dll

PySpark's local file writes fail on Windows without two small files from the
Hadoop project. Download both from the same source folder:
https://github.com/cdarlint/winutils/tree/master/hadoop-3.3.5/bin

Use the direct raw links so your browser downloads them immediately instead
of opening a preview page:
```
https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.5/bin/winutils.exe
https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.5/bin/hadoop.dll
```

**After downloading, put both files into one folder and verify with `ls`**
so you can see they actually landed there before moving on:

```bash
mkdir -p /c/hadoop/bin
cp ~/Downloads/winutils.exe /c/hadoop/bin/
cp ~/Downloads/hadoop.dll /c/hadoop/bin/
ls -la /c/hadoop/bin
```

You should see exactly two files listed:
```
winutils.exe   (~117 KB)
hadoop.dll     (~85 KB)
```

Then set two environment variables (Settings → System → About → Advanced
system settings → Environment Variables):
- New **system variable**: `HADOOP_HOME` = `C:\hadoop`
- Edit the `Path` variable → **New** → add `%HADOOP_HOME%\bin`

Click OK on both dialogs, then **close every open terminal / VS Code window
completely** and reopen — environment variable changes never apply to
terminals that were already open. Confirm it worked:
```bash
echo $HADOOP_HOME        # should print C:\hadoop
echo $PATH | tr ':' '\n' | grep -i hadoop   # should print /c/hadoop/bin
```

---

## One-time setup

```bash
# 1. Clone / open this folder, then:
cp .env.example .env
# edit .env: set PG_HOST=localhost (not host.docker.internal — that only
# works from inside a Docker container) and PG_PASSWORD to your real
# local Postgres password

# 2. Create the hospital_dw database — use pgAdmin4's Query Tool (right-click
#    Databases -> Create -> Database), not the psql command line, since psql
#    usually isn't on your Windows PATH by default.

# 3. Create the warehouse schemas — open each file below in a text editor,
#    copy its contents into pgAdmin4's Query Tool (connected to hospital_dw),
#    and click Execute:
#    sql/01_create_schemas.sql
#    sql/02_create_raw_tables.sql
```

## Option A — run the pipeline locally (no Docker at all) — RECOMMENDED

```bash
cd Hospital_Data_Engineering_Pipeline
python -m venv .venv
source .venv/Scripts/activate        # Git Bash on Windows
python -m pip install --upgrade pip
python -m pip install pandas numpy Faker python-dotenv SQLAlchemy psycopg2-binary pyarrow pyspark
```

Every time you open a **new** terminal to work on this project, reactivate
the venv first and confirm it's actually active:
```bash
cd ~/Downloads/Hospital_Data_Engineering_Pipeline
source .venv/Scripts/activate
which python     # must end in .venv/Scripts/python — if it shows
                  # anaconda3 or another path, the venv did not activate
```

Then run each stage in order:
```bash
cd src
python generate_data.py
python extract.py
python validate.py
python transform_spark.py
python load.py
```

If `python load.py` finishes with `Load stage complete`, your `staging.*`
and `analytics.*` tables are populated — the core pipeline is done.

## Option B — run orchestrated with Airflow + Streamlit in Docker

Only do this if Docker Desktop is installed and running.

```bash
docker compose up airflow-init      # first time only: sets up Airflow
docker compose up -d                # starts Airflow UI + scheduler + Streamlit
```
- Airflow UI: http://localhost:8080 (user: `admin`, password: `admin`) → trigger `hospital_pipeline_dag`
- Streamlit dashboard: http://localhost:8501

---

## Build the Power BI dashboard

Run `sql/PowerBISQL.sql` in pgAdmin4's Query Tool (same way as the schema
files above: open it in a text editor, copy, paste into the Query Tool,
Execute). This must be done **after** `load.py` has run at least once,
since the views read from `analytics.*` tables.

Verify it worked:
```sql
SELECT table_name FROM information_schema.views WHERE table_schema = 'reporting';
```
Should list 7 views including `vw_patient_overview`, `vw_appointments`,
`vw_admissions`, `vw_billing`.

Then open **Power BI Desktop** → Get Data → PostgreSQL database → server
`localhost`, database `hospital_dw` → import from the `reporting` schema.
See `dashboard/README.md` for details.

## Run the Streamlit dashboard (no Docker)

**Run `sql/PowerBISQL.sql` FIRST** (see above) — the dashboard reads the
`reporting.*` views, so it will error with "relation does not exist" if
you skip this step or run Streamlit before it.

Once the views exist, paste this whole block into one Git Bash terminal
in a single go (keeping every line together avoids environment variables
getting lost between separate commands):

```bash
cd ~/Downloads/Hospital_Data_Engineering_Pipeline
source .venv/Scripts/activate
python -m pip install streamlit plotly
export PG_HOST=localhost
export PG_PORT=5432
export PG_DB=hospital_dw
export PG_USER=postgres
export PG_PASSWORD=your_local_postgres_password
cd dashboard
python -m streamlit run streamlit_app.py
```

Using `python -m streamlit run ...` (not bare `streamlit run ...`) makes
sure it uses your venv's Streamlit, not a different copy that might already
be installed elsewhere (e.g. Anaconda) and get picked up first on PATH.

It should open `http://localhost:8501` in your browser automatically. If
your terminal closes or you open a new one later, you must re-export the
five `PG_*` variables again before rerunning `python -m streamlit run` —
they don't persist between terminal sessions.

## Run the tests

```bash
pytest tests/
```

******
If you regenerated new synthetic data (ran generate_data.py again)

Rerun everything downstream of it, in order:

```bash
python extract.py
python validate.py
python transform_spark.py
python load.py
```
If you manually edited a CSV in data/raw/ yourself

Same as above — skip `generate_data.py` (don't overwrite your edit), but rerun:

```bash
python extract.py
python validate.py
python transform_spark.py
python load.py
```
If you only changed one script's logic (e.g. `tweaked transform_spark.py`)

You only need to rerun from that stage onward — anything before it is unaffected:

```bash
python transform_spark.py
python load.py
```
Why the whole chain matters

Each stage's output is the next stage's input:
`generate_data.py` → `data/raw/*.csv` → `extract.py` reads those → `raw.* tables` → `validate.py` reads those → `transform_spark.py` reads `raw.*` again → `data/processed/*.`parquet → `load.py` reads that → `staging.*` / `analytics.*` tables

If you skip a stage, downstream stages are working on stale data.

After `load.py` finishes — refreshing your dashboards

Power BI Desktop: click Refresh in the ribbon (it won't auto-update)
Streamlit: it caches query results for 5 minutes (ttl=300 in the code) — either wait, or just refresh your browser tab and it'll re-query if the cache expired; to force it instantly, stop and restart `python -m streamlit run streamlit_app.py`

You do not need to rerun `sql/PowerBISQL.sql` again unless you changed the view logic itself — those views just point at whatever is currently in `analytics.*`, so they automatically reflect fresh data.
