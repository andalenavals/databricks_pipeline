import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

from databricks_pipeline.core import aggregate_daily_summary


def test_aggregate_daily_summary_success(spark: SparkSession):
    """Tests that aggregate_daily_summary correctly groups by order_date and customer_id."""
    schema = StructType(
        [
            StructField("order_date", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("order_id", StringType(), True),
            StructField("amount", DoubleType(), True),
        ]
    )

    data = [
        ("2026-08-20", "cust_A", "ord_001", 100.0),
        ("2026-08-20", "cust_A", "ord_002", 50.5),
        ("2026-08-20", "cust_B", "ord_003", 200.0),
        ("2026-08-21", "cust_A", "ord_004", 75.0),
    ]

    input_df = spark.createDataFrame(data, schema)

    # Execute transformation from core.py
    result_df = aggregate_daily_summary(input_df)
    results = result_df.collect()

    # Convert results to list of dicts for clean asserting
    records = [row.asDict() for row in results]

    # Assert correct number of grouped rows
    assert len(records) == 3

    # Assert customer A on 2026-08-20 (2 orders, $150.5 total)
    assert records[0] == {
        "order_date": "2026-08-20",
        "customer_id": "cust_A",
        "total_orders": 2,
        "total_spent": pytest.approx(150.5),
    }

    # Assert customer B on 2026-08-20 (1 order, $200.0 total)
    assert records[1] == {
        "order_date": "2026-08-20",
        "customer_id": "cust_B",
        "total_orders": 1,
        "total_spent": pytest.approx(200.0),
    }

    # Assert customer A on 2026-08-21 (1 order, $75.0 total)
    assert records[2] == {
        "order_date": "2026-08-21",
        "customer_id": "cust_A",
        "total_orders": 1,
        "total_spent": pytest.approx(75.0),
    }


def test_aggregate_daily_summary_empty_dataframe(spark: SparkSession):
    """Tests that aggregate_daily_summary handles empty DataFrames gracefully."""
    schema = StructType(
        [
            StructField("order_date", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("order_id", StringType(), True),
            StructField("amount", DoubleType(), True),
        ]
    )

    input_df = spark.createDataFrame([], schema)

    result_df = aggregate_daily_summary(input_df)

    assert result_df.count() == 0
    assert set(result_df.columns) == {
        "order_date",
        "customer_id",
        "total_orders",
        "total_spent",
    }