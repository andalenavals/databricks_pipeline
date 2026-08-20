from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def aggregate_daily_summary(orders_df: DataFrame) -> DataFrame:
    """Aggregates raw orders into daily customer summaries."""
    return (
        orders_df
        .groupBy("order_date", "customer_id")
        .agg(
            F.count("order_id").alias("total_orders"),
            F.sum("amount").alias("total_spent")
        )
        .orderBy("order_date", "customer_id")
    )