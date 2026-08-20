from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from pyspark.sql import SparkSession


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a simple order summary.")
    parser.add_argument(
        "--input-path",
        default="/Volumes/workspace/dev_default/raw_data/sample_orders.csv",
        help="CSV path, Volume path, local path, or UC table name.",
    )
    parser.add_argument(
        "--output-path",
        default="/Volumes/workspace/dev_default/raw_data/outputs/daily_summary",
        help="Output Volume path, local path, or UC table name.",
    )
    return parser.parse_args()


def _is_path(target: str) -> bool:
    """Check if target is a file system path rather than a Unity Catalog table identifier."""
    return (
        target.startswith(("/", "\\", "dbfs:", "s3:", "abfss:", "file:"))
        or "/" in target
        or "\\" in target
        or bool(Path(target).suffix)
    )


def _load_rows(spark: SparkSession, input_path: str) -> list[dict[str, object]]:
    from databricks_pipeline.core import DEMO_ORDERS

    try:
        if _is_path(input_path):
            df = spark.read.option("header", True).option("inferSchema", True).csv(input_path)
        else:
            df = spark.read.table(input_path)

        rows = [row.asDict(recursive=True) for row in df.collect()]
        if rows:
            return rows
    except Exception:
        pass
    return DEMO_ORDERS


def _write_output(spark: SparkSession, rows: list[dict[str, object]], output_path: str) -> None:
    """Convert input rows to a DataFrame and save strictly as Delta (path or UC table)."""
    if not rows:
        print("No rows to write.")
        return

    output_df = spark.createDataFrame(rows)

    if _is_path(output_path):
        output_df.write.mode("overwrite").format("delta").save(output_path)
    else:
        output_df.write.mode("overwrite").format("delta").saveAsTable(output_path)


def _create_spark_session() -> SparkSession:
    """Creates a SparkSession with Delta support via local JAR files."""
    builder = SparkSession.builder.appName("DailySummary")

    # Locate project root dynamically and search for JARs
    project_root = Path(__file__).resolve().parents[3]
    local_jars_dir = project_root / "jars"

    if local_jars_dir.exists():
        jar_files = list(local_jars_dir.glob("*.jar"))
        if jar_files:
            jar_paths_spark = ",".join(str(j) for j in jar_files)
            # Use os.pathsep (';' on Windows) to avoid file-locking during temp directory cleanup
            jar_paths_classpath = os.pathsep.join(str(j) for j in jar_files)

            builder = (
                builder
                .config("spark.jars", jar_paths_spark)
                .config("spark.driver.extraClassPath", jar_paths_classpath)
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
                .config(
                    "spark.sql.catalog.spark_catalog",
                    "org.apache.spark.sql.delta.catalog.DeltaCatalog",
                )
            )
            print(f"Loaded local JARs ({len(jar_files)} files found): {jar_paths_spark}")
    else:
        print("No local JARs found in jars/ directory. Starting plain Spark session.")

    return builder.getOrCreate()


def main() -> None:
    from databricks_pipeline.core import aggregate_customer_orders

    args = parse_args()
    spark = _create_spark_session()

    try:
        input_rows = _load_rows(spark, args.input_path)
        summary_rows = aggregate_customer_orders(input_rows)
        _write_output(spark, summary_rows, args.output_path)

        print(
            json.dumps(
                {
                    "input_path": args.input_path,
                    "output_path": args.output_path,
                    "rows": len(summary_rows),
                }
            )
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()