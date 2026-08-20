import argparse
from pathlib import Path
from databricks_pipeline.utils import get_spark_session
from databricks_pipeline.core import aggregate_daily_summary

def parse_args():
    parser = argparse.ArgumentParser(description="Process daily orders summary.")
    parser.add_argument(
        "--input", 
        required=True, 
        help="Unity Catalog table (dev.dev_default.sample_orders) or file path"
    )
    parser.add_argument(
        "--output", 
        required=True, 
        help="Target Unity Catalog table (dev.dev_default.daily_summary) or output directory"
    )
    return parser.parse_known_args()

def main():
    args, _ = parse_args()
    spark = get_spark_session("DailySummaryTask")

    input_target = args.input.strip()

    # 1. Read Input
    if input_target.endswith(".csv"):
        input_df = spark.read.option("header", "true").option("inferSchema", "true").csv(input_target)
    elif "/" in input_target or input_target.startswith("\\"):
        # File system directory or Volume path
        input_df = spark.read.format("delta").load(input_target)
    else:
        # Unity Catalog table (e.g., catalog.schema.table)
        input_df = spark.read.table(input_target)

    # 2. Process Business Logic
    summary_df = aggregate_daily_summary(input_df)

    # 3. Write Output
    output_target = args.output.strip()
    if "/" in output_target or output_target.startswith("\\"):
        summary_df.write.mode("overwrite").format("delta").save(output_target)
    else:
        summary_df.write.mode("overwrite").format("delta").saveAsTable(output_target)


if __name__ == "__main__":
    main()