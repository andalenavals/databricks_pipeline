import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    """Creates a local PySpark session for running tests off-cluster."""
    session = (
        SparkSession.builder.master("local[1]")
        .appName("DatabricksPipelineUnitTest")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.default.parallelism", "1")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )

    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()