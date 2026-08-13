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
- `resources/` - Databricks job definitions
- `src/databricks_pipeline/` - reusable Python package and job entrypoint
- `tests/` - local unit tests for the pure-Python logic

## Local setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
pytest
```

## Databricks setup

1. Install and authenticate the Databricks CLI.
2. Set your Databricks host in the CLI profile or environment.
3. From the repo root, validate the bundle:

```bash
databricks bundle validate
```

4. Deploy the bundle:

```bash
databricks bundle deploy -t dev
```

5. Run the job:

```bash
databricks bundle run daily_summary_job -t dev
```

## Notes

- The job is intentionally small and serverless-friendly.
- The task script bootstraps demo data if the configured input path does not exist yet, so the example can run end-to-end without extra setup.

