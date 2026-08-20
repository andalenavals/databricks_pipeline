import os
from pathlib import Path
from pyspark.sql import SparkSession

def get_spark_session(app_name: str = "DatabricksPipeline") -> SparkSession:
    # Return the active Databricks session if it already exists
    active_session = SparkSession.getActiveSession()
    if active_session is not None:
        return active_session

    builder = SparkSession.builder.appName(app_name)

    # Apply local configurations ONLY when running outside Databricks
    if "DATABRICKS_RUNTIME_VERSION" not in os.environ:
        # Isolate local temp directory to prevent Windows JVM file lock warnings
        temp_dir = Path("./tmp/spark").resolve()
        temp_dir.mkdir(parents=True, exist_ok=True)

        builder = (
            builder.master("local[*]")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .config("spark.local.dir", str(temp_dir))
        )

        # Optional: Load local JARs safely if they exist
        current_file = globals().get("__file__")
        if current_file:
            project_root = Path(current_file).resolve().parents[2]
            jars_dir = project_root / "jars"
            if jars_dir.exists():
                jar_files = [str(p) for p in jars_dir.glob("*.jar")]
                if jar_files:
                    builder = builder.config("spark.jars", ",".join(jar_files))

    return builder.getOrCreate()


def get_dbutils(spark: SparkSession):
    """Safely fetch DBUtils across local and cloud environments."""
    try:
        from pyspark.dbutils import DBUtils
        return DBUtils(spark)
    except (ImportError, ModuleNotFoundError):
        return None