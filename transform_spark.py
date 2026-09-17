"""
STAGE 4 — SPARK TRANSFORMATION
Reads the raw CSVs with PySpark (runs in "local mode" — a real Spark cluster
is overkill for 2,000 rows, but you still get real Spark DataFrame / SQL practice),
cleans them, joins them, and writes the results as Parquet into data/processed/.
load.py then picks these Parquet files up and pushes them into Postgres
staging + analytics schemas.
"""
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from logger import get_logger

logger = get_logger(__name__)
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def get_spark():
    return (
        SparkSession.builder
        .appName("HospitalPipelineTransform")
        .master("local[*]")
        .getOrCreate()
    )


def main():
    spark = get_spark()

    patients = spark.read.csv(str(RAW_DIR / "patients.csv"), header=True, inferSchema=True)
    doctors = spark.read.csv(str(RAW_DIR / "doctors.csv"), header=True, inferSchema=True)
    appointments = spark.read.csv(str(RAW_DIR / "appointments.csv"), header=True, inferSchema=True)
    admissions = spark.read.csv(str(RAW_DIR / "admissions.csv"), header=True, inferSchema=True)
    billing = spark.read.csv(str(RAW_DIR / "billing.csv"), header=True, inferSchema=True)

    # --- clean ---
    patients_clean = (
        patients.dropDuplicates(["patient_id"])
        .withColumn("age", F.when(F.col("age").isNull(), F.lit(0)).otherwise(F.col("age")))
    )
    valid_patient_ids = [r.patient_id for r in patients_clean.select("patient_id").collect()]

    appointments_clean = appointments.filter(F.col("patient_id").isin(valid_patient_ids))
    admissions_clean = admissions.filter(F.col("patient_id").isin(valid_patient_ids)) \
        .withColumn(
            "length_of_stay_days",
            F.datediff(F.col("discharge_date"), F.col("admission_date")),
        )
    billing_clean = billing.filter(F.col("patient_id").isin(valid_patient_ids))

    # --- joins for analytics-ready tables ---
    admissions_billing = admissions_clean.join(
    billing_clean.drop("patient_id"), on="admission_id", how="left"
    )

    daily_admissions = (
        admissions_clean.groupBy("admission_date", "department")
        .agg(F.count("*").alias("admissions_count"),
             F.avg("length_of_stay_days").alias("avg_length_of_stay"))
        .orderBy("admission_date")
    )

    daily_appointments = (
        appointments_clean.groupBy("appointment_date", "status")
        .agg(F.count("*").alias("appointment_count"))
        .orderBy("appointment_date")
    )

    # --- write out as Parquet for load.py ---
    patients_clean.write.mode("overwrite").parquet(str(PROCESSED_DIR / "patients"))
    doctors.write.mode("overwrite").parquet(str(PROCESSED_DIR / "doctors"))
    appointments_clean.write.mode("overwrite").parquet(str(PROCESSED_DIR / "appointments"))
    admissions_clean.write.mode("overwrite").parquet(str(PROCESSED_DIR / "admissions"))
    billing_clean.write.mode("overwrite").parquet(str(PROCESSED_DIR / "billing"))
    admissions_billing.write.mode("overwrite").parquet(str(PROCESSED_DIR / "admissions_billing"))
    daily_admissions.write.mode("overwrite").parquet(str(PROCESSED_DIR / "daily_admissions"))
    daily_appointments.write.mode("overwrite").parquet(str(PROCESSED_DIR / "daily_appointments"))

    logger.info(f"Spark transform complete, Parquet written to {PROCESSED_DIR}")
    spark.stop()


if __name__ == "__main__":
    main()
