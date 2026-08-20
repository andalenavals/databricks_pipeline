import os
import time
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import VolumeType
from databricks.sdk.service.sql import StatementState
from databricks.sdk.errors import NotFound, InvalidState, BadRequest

load_dotenv()

# Initialize WorkspaceClient
w = WorkspaceClient()

# Configuration
DESIRED_CATALOG = "dev"
FALLBACK_CATALOG = "workspace"  # Uses the workspace catalog active in your environment
SCHEMA_NAME = "dev_default"
VOLUME_NAME = "raw_data"
TABLE_NAME = "sample_orders"
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")

# 1. Resolve Catalog Access
print("Checking catalog access...")
CATALOG_NAME = DESIRED_CATALOG

try:
    w.catalogs.get(CATALOG_NAME)
    print(f"Using existing catalog '{CATALOG_NAME}'.")
except NotFound:
    try:
        print(f"Attempting to create catalog '{CATALOG_NAME}'...")
        w.catalogs.create(name=CATALOG_NAME)
        print(f"Catalog '{CATALOG_NAME}' created successfully.")
    except (InvalidState, BadRequest):
        print(f"Cannot create '{CATALOG_NAME}' without root storage.")
        print(f"Falling back to catalog '{FALLBACK_CATALOG}'...")
        CATALOG_NAME = FALLBACK_CATALOG

# 2. Create Schema and Volume
schema_full_name = f"{CATALOG_NAME}.{SCHEMA_NAME}"
try:
    w.schemas.get(schema_full_name)
    print(f"Schema '{schema_full_name}' already exists.")
except NotFound:
    w.schemas.create(name=SCHEMA_NAME, catalog_name=CATALOG_NAME)
    print(f"Schema '{schema_full_name}' created.")

volume_full_name = f"{CATALOG_NAME}.{SCHEMA_NAME}.{VOLUME_NAME}"
try:
    w.volumes.read(volume_full_name)
    print(f"Volume '{volume_full_name}' already exists.")
except NotFound:
    w.volumes.create(
        catalog_name=CATALOG_NAME,
        schema_name=SCHEMA_NAME,
        name=VOLUME_NAME,
        volume_type=VolumeType.MANAGED,
    )
    print(f"Volume '{volume_full_name}' created.")

# 3. Upload local CSV file to Volume
local_file_path = "local_data/sample_orders.csv"
volume_path = f"/Volumes/{CATALOG_NAME}/{SCHEMA_NAME}/{VOLUME_NAME}/sample_orders.csv"

if os.path.exists(local_file_path):
    print(f"Uploading {local_file_path} to {volume_path}...")
    with open(local_file_path, "rb") as f:
        w.files.upload(volume_path, f, overwrite=True)
    print("File uploaded successfully.")
else:
    print(f"Warning: Local file '{local_file_path}' not found. Skipping upload.")

# 4. Ensure SQL Warehouse is Active
if not WAREHOUSE_ID:
    raise ValueError("DATABRICKS_WAREHOUSE_ID environment variable is missing.")

print(f"Checking state of SQL Warehouse {WAREHOUSE_ID}...")
warehouse = w.warehouses.get(id=WAREHOUSE_ID)
if warehouse.state.value != "RUNNING":
    print("Starting SQL Warehouse... (this may take a few minutes)")
    w.warehouses.start(id=WAREHOUSE_ID).result()
    print("SQL Warehouse is now RUNNING.")

# 5. Create Delta Table from CSV
create_table_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME} 
AS SELECT * FROM read_files(
  '{volume_path}', 
  format => 'csv', 
  header => true, 
  inferSchema => true
)
"""

print(f"Creating table {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}...")

response = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=create_table_sql,
    wait_timeout="30s",
)

if response.status.state in [StatementState.PENDING, StatementState.RUNNING]:
    print("Waiting for table creation to complete...")
    statement_id = response.statement_id
    while response.status.state in [StatementState.PENDING, StatementState.RUNNING]:
        time.sleep(3)
        response = w.statement_execution.get_statement(statement_id)

if response.status.state == StatementState.SUCCEEDED:
    print(f"Table {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME} created successfully!")
else:
    print(f"Failed to create table: {response.status.error.message}")