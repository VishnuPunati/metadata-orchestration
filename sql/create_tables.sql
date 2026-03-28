CREATE TABLE IF NOT EXISTS etl_control (
    pipeline_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL UNIQUE,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('csv', 'api', 'db')),
    source_options JSONB NOT NULL,
    destination_table VARCHAR(255) NOT NULL,
    load_type VARCHAR(20) NOT NULL CHECK (load_type IN ('full', 'incremental')),
    incremental_key VARCHAR(255),
    dependencies TEXT[] DEFAULT ARRAY[]::TEXT[],
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS etl_audit_log (
    run_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_ms INTEGER,
    status VARCHAR(20) NOT NULL CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED')),
    rows_read INTEGER NOT NULL DEFAULT 0,
    rows_written INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS etl_watermarks (
    pipeline_name VARCHAR(255) PRIMARY KEY,
    watermark_value VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS source_products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    last_modified TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS destination_csv_table (
    id INTEGER,
    name VARCHAR(255),
    category VARCHAR(255),
    price NUMERIC(10, 2),
    last_modified TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS destination_api_table (
    id INTEGER,
    name VARCHAR(255),
    value INTEGER,
    last_modified TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS destination_db_table (
    id INTEGER,
    name VARCHAR(255),
    category VARCHAR(255),
    price NUMERIC(10, 2),
    last_modified TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS destination_failed_table (
    id INTEGER,
    value TEXT
);
