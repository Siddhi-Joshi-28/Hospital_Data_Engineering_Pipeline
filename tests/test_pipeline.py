"""
Checks that each pipeline stage script runs end-to-end without raising.
Run manually and in order (they depend on each other's output), e.g.:
    pytest tests/test_pipeline.py -v
"""
import sys
import subprocess
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"


def run(script):
    result = subprocess.run([sys.executable, str(SRC / script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_01_generate_data():
    run("generate_data.py")


def test_02_extract():
    run("extract.py")


def test_03_validate():
    run("validate.py")


def test_04_spark_transform():
    run("transform_spark.py")


def test_05_load():
    run("load.py")
