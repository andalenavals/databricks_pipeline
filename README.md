# databricks_pipeline

A small, functional Databricks Asset Bundle project that demonstrates a simple
customer-order summary pipeline.

## What it does

- Loads order data from a CSV file in Databricks or falls back to built-in demo records.
- Cleans and aggregates the data into a per-customer summary.
- Writes the summary as a Parquet dataset.
- Exposes the logic as a Databricks job that can be deployed with the Databricks CLI.

## Project layout

- `databricks.yml` - bundle entrypoint
- `pyproject.toml` - Package configuration file defining project dependencies, Python build settings, and CLI entry points. This is used to build a codebase into a standard .whl
- `src/databricks_pipeline/`: The main Python package directory:
    - `core.py`: Business logic and aggregation methods (such as aggregate_customer_orders) along with fallback mock data (DEMO_ORDERS).
    - `tasks/` (e.g., daily_summary.py): Execution scripts that parse CLI arguments, handle PySpark SparkSession initialization, load raw data, and write output files.
- `resources/` - Declarative YAML files defining Databricks workflows, job schedules, and compute configurations.
- `src/databricks_pipeline/` - reusable Python package and job entrypoint
- `tests/` - local unit tests for the pure-Python logic
- `setup_catalog.py` - create catalog, schema and tables in Databricks. Run `$ databricks warehouses list` to find the ID

## Local setup

```bash
python3 -m venv .venv
source .venv/Scripts/activate
pip install -e .[dev]
pytest
```

## Run locally:

    $ python -m databricks_pipeline.tasks.daily_summary --input-path local_data/sample_orders.csv --output-path local_data/output_daily_summary

    It requires manual installation of hadoop.dll and winutils.exe

    Set env variables
    export HADOOP_HOME="C:\\hadoop"
    export PATH="$PATH:/c/hadoop/bin"   

    Also install Java (OpenJDK 25)
    $ winget install Microsoft.OpenJDK.17

## Databricks setup

1. Install and authenticate the Databricks CLI.
2. Set your Databricks host in the CLI profile or environment.
    2.1 $ databricks configure --profile default
    2.2 Manually edit ~/.databrickscfg files

        [DEFAULT]
        host = https://<yourworkspace>.cloud.databricks.com

        [__settings__]
        auth_storage = secure
    2.3 Verify
        $ databricks clusters list
        $ databricks current-user me

3. Create catalog, schema and table
    $  python setup_catalog.py


4. From the repo root, validate the bundle:

```bash
databricks bundle validate
```

5. Deploy the bundle:

```bash
databricks bundle deploy -t dev
```

6. Run the job:

```bash
databricks bundle run daily_summary_job -t dev
```





