from datetime import datetime, timezone

from connectors.api_connector import extract as extract_api
from connectors.csv_connector import extract as extract_csv
from connectors.db_connector import extract as extract_db
from loaders.db_loader import load as load_db
from utils.db import (
    get_watermark,
    insert_audit_log,
    update_audit_log,
    upsert_watermark,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def transform(df, pipeline):
    if df is None or df.empty:
        return df

    df = df.drop_duplicates().copy()
    df.columns = [str(column).strip() for column in df.columns]

    rename_columns = (pipeline.get("source_options") or {}).get("rename_columns", {})
    if rename_columns:
        df = df.rename(columns=rename_columns)

    return df


def run_pipeline(pipeline):
    pipeline_name = pipeline["pipeline_name"]
    start_time = datetime.now(timezone.utc)
    run_id = insert_audit_log(pipeline_name, start_time, "RUNNING")
    status = "SUCCESS"
    rows_read = 0
    rows_written = 0
    error_message = None

    try:
        source_type = pipeline["source_type"]
        source_options = pipeline["source_options"] or {}
        load_type = pipeline["load_type"]
        incremental_key = pipeline.get("incremental_key")
        watermark = get_watermark(pipeline_name) if load_type == "incremental" else None

        if source_type == "csv":
            df = extract_csv(source_options, incremental_key=incremental_key, watermark=watermark)
        elif source_type == "api":
            df = extract_api(source_options, incremental_key=incremental_key, watermark=watermark)
        elif source_type == "db":
            df = extract_db(source_options, incremental_key=incremental_key, watermark=watermark)
        else:
            raise ValueError(f"Unsupported source type '{source_type}'")

        df = transform(df, pipeline)
        rows_read = 0 if df is None else len(df)
        rows_written = load_db(df, pipeline["destination_table"], load_type)

        if load_type == "incremental" and rows_written > 0 and incremental_key and incremental_key in df.columns:
            max_value = df[incremental_key].max()
            if hasattr(max_value, "isoformat"):
                max_value = max_value.isoformat()
            upsert_watermark(pipeline_name, str(max_value))

    except Exception as exc:
        status = "FAILED"
        error_message = str(exc)
        logger.exception("Pipeline '%s' failed", pipeline_name)

    end_time = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    update_audit_log(
        run_id=run_id,
        end_time=end_time,
        duration_ms=duration_ms,
        status=status,
        rows_read=rows_read,
        rows_written=rows_written,
        error_message=error_message,
    )

    return {
        "pipeline_name": pipeline_name,
        "status": status,
        "rows_read": rows_read,
        "rows_written": rows_written,
        "error_message": error_message,
    }
