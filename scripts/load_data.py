"""Shared connection to the MET Employability Career Match dataset."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPOSITORY_ROOT / ".env"

load_dotenv(ENV_FILE)


def get_raw_data_path():
    """Return and validate the private raw-data location."""

    configured_path = os.getenv("RAW_DATA_PATH")

    if not configured_path:
        raise ValueError(
            "RAW_DATA_PATH is missing. Copy .env.example to .env "
            "and add the location of the Parquet dataset."
        )

    data_path = Path(configured_path).expanduser()

    if not data_path.exists():
        raise FileNotFoundError(
            f"The configured raw-data folder does not exist: {data_path}"
        )

    parquet_files = sorted(data_path.glob("*.parquet"))

    if len(parquet_files) != 17:
        raise FileNotFoundError(
            f"Expected 17 Parquet files, but found "
            f"{len(parquet_files)} in {data_path}"
        )

    return parquet_files


def load_job_postings():
    """Load all raw partitions into one Spark DataFrame."""

    parquet_files = get_raw_data_path()

    spark = (
        SparkSession.builder
        .appName("Group2CareerMarketAnalysis")
        .getOrCreate()
    )

    dataframe = spark.read.parquet(
        *[str(file) for file in parquet_files]
    )

    return spark, dataframe


if __name__ == "__main__":
    spark, dataframe = load_job_postings()

    print("Shared data connection successful.")
    print(f"Rows: {dataframe.count():,}")
    print(f"Columns: {len(dataframe.columns)}")

    spark.stop()
    