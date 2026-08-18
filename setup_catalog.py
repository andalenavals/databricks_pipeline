import os
from databricks.sdk import WorkspaceClient

# Initializes using your local Databricks CLI authentication (~/.databrickscfg or environment variables)
w = WorkspaceClient()

# Set your SQL Warehouse ID
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")

# 1. Create Catalog, Schema, and Volume via SQL
sql_statements = [
    "CREATE CATALOG IF NOT EXISTS dev",
    "CREATE SCHEMA IF NOT EXISTS dev.default",
    "CREATE VOLUME IF NOT EXISTS dev.default.raw_data",
]

print("Creating catalog, schema, and volume...")
for stmt in sql_statements:
    w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID, statement=stmt
    )
print("Catalog hierarchy created successfully.")

# 2. Upload local CSV file to the Unity Catalog Volume
local_file_path = "local_data/sample_orders.csv"
volume_path = "/Volumes/dev/default/raw_data/sample_orders.csv"

print(f"Uploading {local_file_path} to {volume_path}...")
with open(local_file_path, "rb") as f:
    w.files.upload(volume_path, f, overwrite=True)
print("File uploaded successfully.")

# 3. Create Delta Table from uploaded CSV
create_table_sql = """
CREATE TABLE IF NOT EXISTS dev.default.sample_orders 
AS SELECT * FROM read_files(
  '/Volumes/dev/default/raw_data/sample_orders.csv', 
  format => 'csv', 
  header => true, 
  inferSchema => true
)
"""

print("Creating table dev.default.sample_orders...")
w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID, statement=create_table_sql
)
print("Table created successfully!")
