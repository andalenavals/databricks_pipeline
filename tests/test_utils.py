from pyspark.sql import SparkSession

from databricks_pipeline.utils import get_spark_session


def test_get_spark_session_returns_active_session(spark: SparkSession):
    """Verifies get_spark_session reuses the existing active Spark session."""
    session = get_spark_session("TestApp")

    assert session is spark
    assert isinstance(session, SparkSession)