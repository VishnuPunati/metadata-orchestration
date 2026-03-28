# Evaluator Guide

## Overview

This project is a metadata-driven ETL orchestration framework built with:

- Docker Compose
- PostgreSQL
- Flask mock API
- Python orchestrator

The default evaluation path is intentionally clean:

- `pipeline-A` is active
- `pipeline-B` is active
- `api-incremental` is active
- `failing-pipeline` is inactive by default
- `cycle-A` and `cycle-B` are inactive by default

This means a normal fresh-start evaluation should not show intentional error traces.

## Services

The application contains these three services:

- `db`
- `mock-api`
- `orchestrator`

The `orchestrator` runs once by default and exits after completing its ETL pass.

## Fresh Start Evaluation

Run from the repository root:

```powershell
docker compose down -v
docker compose up --build -d
docker compose ps
```

Expected:

- `metadata-db` becomes `healthy`
- `metadata-mock-api` becomes `healthy`
- `metadata-orchestrator` starts successfully

## Verify Database Initialization

```powershell
docker compose exec db psql -U postgres -d metadata_etl -c "\dt"
docker compose exec db psql -U postgres -d metadata_etl -c "SELECT pipeline_name, source_type, load_type, dependencies, is_active FROM etl_control ORDER BY pipeline_id;"
```

Expected tables:

- `etl_control`
- `etl_audit_log`
- `etl_watermarks`
- `source_products`
- `destination_csv_table`
- `destination_api_table`
- `destination_db_table`

Expected default pipeline state:

- `pipeline-A` = active
- `pipeline-B` = active
- `api-incremental` = active
- `failing-pipeline` = inactive
- `cycle-A` = inactive
- `cycle-B` = inactive

## Verify Default ETL Execution

```powershell
docker compose logs orchestrator --tail=200
docker compose exec db psql -U postgres -d metadata_etl -c "SELECT pipeline_name, status, rows_read, rows_written, error_message FROM etl_audit_log ORDER BY run_id;"
docker compose exec db psql -U postgres -d metadata_etl -c "SELECT COUNT(*) AS csv_rows FROM destination_csv_table;"
docker compose exec db psql -U postgres -d metadata_etl -c "SELECT COUNT(*) AS db_rows FROM destination_db_table;"
docker compose exec db psql -U postgres -d metadata_etl -c "SELECT COUNT(*) AS api_rows FROM destination_api_table;"
docker compose exec db psql -U postgres -d metadata_etl -c "SELECT * FROM etl_watermarks ORDER BY pipeline_name;"
```

Expected results:

- `pipeline-A` has status `SUCCESS`
- `pipeline-B` has status `SUCCESS`
- `api-incremental` has status `SUCCESS`
- `destination_csv_table` row count is `10`
- `destination_db_table` row count is `5`
- `destination_api_table` row count is `5`
- `etl_watermarks` contains `api-incremental`

## Verify Full Load on Rerun

```powershell
docker compose run --rm orchestrator python -m orchestrator.main
docker compose exec db psql -U postgres -d metadata_etl -c "SELECT COUNT(*) AS csv_rows FROM destination_csv_table;"
docker compose exec db psql -U postgres -d metadata_etl -c "SELECT COUNT(*) AS db_rows FROM destination_db_table;"
```

Expected:

- `csv_rows` remains `10`
- `db_rows` remains `5`

This confirms full-load truncation and reload behavior.

## Verify Incremental API Behavior

Insert one newer API row:

```powershell
curl.exe -X POST http://localhost:8000/data -H "Content-Type: application/json" -d "{\"id\":6,\"name\":\"api_item_6\",\"value\":60,\"last_modified\":\"2026-03-20T15:00:00Z\"}"
docker compose run --rm orchestrator python -m orchestrator.main
docker compose exec db psql -U postgres -d metadata_etl -c "SELECT COUNT(*) AS api_rows FROM destination_api_table;"
docker compose exec db psql -U postgres -d metadata_etl -c "SELECT * FROM etl_watermarks WHERE pipeline_name = 'api-incremental';"
```

Expected:

- `api_rows` increases by `1`
- the watermark value advances

## Manual Failure Test

This is optional and should not be part of the default clean-path evaluation.

```powershell
docker compose cp scripts/manual_activate_failure_test.sql db:/tmp/manual_activate_failure_test.sql
docker compose exec db psql -U postgres -d metadata_etl -f /tmp/manual_activate_failure_test.sql
docker compose run --rm orchestrator python -m orchestrator.main
```

Expected:

- `failing-pipeline` appears in `etl_audit_log`
- status is `FAILED`
- `error_message` is populated

To restore normal mode afterward:

```powershell
docker compose exec db psql -U postgres -d metadata_etl -c "UPDATE etl_control SET is_active = CASE WHEN pipeline_name IN ('pipeline-A','pipeline-B','api-incremental') THEN TRUE WHEN pipeline_name IN ('failing-pipeline','cycle-A','cycle-B') THEN FALSE ELSE is_active END;"
```

## Manual Cycle Detection Test

This is optional and should also be run separately from the default evaluation path.

```powershell
docker compose cp scripts/manual_activate_cycle_test.sql db:/tmp/manual_activate_cycle_test.sql
docker compose exec db psql -U postgres -d metadata_etl -f /tmp/manual_activate_cycle_test.sql
docker compose run --rm orchestrator python -m orchestrator.main
docker compose logs orchestrator --tail=200
```

Expected:

- orchestrator logs contain `Cycle detected in dependency graph`
- cycle pipelines do not execute

To restore normal mode afterward:

```powershell
docker compose exec db psql -U postgres -d metadata_etl -c "UPDATE etl_control SET is_active = CASE WHEN pipeline_name IN ('pipeline-A','pipeline-B','api-incremental') THEN TRUE WHEN pipeline_name IN ('failing-pipeline','cycle-A','cycle-B') THEN FALSE ELSE is_active END;"
```

## Evaluation Conclusion

From the evaluator perspective, the clean default path should demonstrate:

- correct container startup
- correct schema creation and seed loading
- successful CSV ingestion
- successful API ingestion
- successful DB-to-DB ingestion
- dependency-aware execution order
- full-load behavior
- incremental watermark behavior

The failure and cycle scenarios are intentionally available as manual verification steps rather than being enabled during the default startup flow.
