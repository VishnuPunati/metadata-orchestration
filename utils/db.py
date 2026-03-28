import os

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "metadata_etl"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


def get_engine():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "metadata_etl")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    return create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")


def get_pipelines():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT pipeline_id, pipeline_name, source_type, source_options,
                       destination_table, load_type, incremental_key, dependencies, is_active
                FROM etl_control
                WHERE is_active = TRUE
                ORDER BY pipeline_id
                """
            )
            return cur.fetchall()


def get_watermark(pipeline_name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT watermark_value FROM etl_watermarks WHERE pipeline_name = %s",
                (pipeline_name,),
            )
            row = cur.fetchone()
            return row[0] if row else None


def upsert_watermark(pipeline_name, watermark_value):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO etl_watermarks (pipeline_name, watermark_value)
                VALUES (%s, %s)
                ON CONFLICT (pipeline_name)
                DO UPDATE SET watermark_value = EXCLUDED.watermark_value
                """,
                (pipeline_name, watermark_value),
            )
        conn.commit()


def insert_audit_log(pipeline_name, start_time, status):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO etl_audit_log (pipeline_name, start_time, status)
                VALUES (%s, %s, %s)
                RETURNING run_id
                """,
                (pipeline_name, start_time, status),
            )
            run_id = cur.fetchone()[0]
        conn.commit()
        return run_id


def update_audit_log(run_id, end_time, duration_ms, status, rows_read, rows_written, error_message):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE etl_audit_log
                SET end_time = %s,
                    duration_ms = %s,
                    status = %s,
                    rows_read = %s,
                    rows_written = %s,
                    error_message = %s
                WHERE run_id = %s
                """,
                (end_time, duration_ms, status, rows_read, rows_written, error_message, run_id),
            )
        conn.commit()


def execute_sql_file(path):
    with open(path, "r", encoding="utf-8") as file_obj:
        sql = file_obj.read()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def wait_for_database():
    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))
