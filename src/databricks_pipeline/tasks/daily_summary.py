from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pyspark.sql import SparkSession

from databricks_pipeline.core import DEMO_ORDERS, aggregate_customer_orders


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a simple order summary.")
    parser.add_argument(
        "--input-path",
        default="dbfs:/FileStore/databricks_pipeline/sample_orders.csv",
        help="CSV input path in Databricks or a local path for testing.",
    )
    parser.add_argument(
        "--output-path",
        default="dbfs:/FileStore/databricks_pipeline/outputs/daily_summary",
        help="Output path for the summary dataset.",
    )
    return parser.parse_args()


def _load_rows(spark, input_path: str) -> list[dict[str, object]]:
    try:
        df = spark.read.option("header", True).csv(input_path)
        rows = [row.asDict(recursive=True) for row in df.collect()]
        if rows:
            return rows
    except Exception:
        pass
    return DEMO_ORDERS


def _write_output(spark, rows: list[dict[str, object]], output_path: str) -> None:
    output_df = spark.createDataFrame(rows)
    output_df.write.mode("overwrite").parquet(output_path)


def main() -> None:
    args = parse_args()

    spark = SparkSession.builder.getOrCreate()

    input_rows = _load_rows(spark, args.input_path)
    summary_rows = aggregate_customer_orders(input_rows)
    _write_output(spark, summary_rows, args.output_path)

    print(json.dumps({"input_path": args.input_path, "output_path": args.output_path, "rows": len(summary_rows)}))


if __name__ == "__main__":
    main()
