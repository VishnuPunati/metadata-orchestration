TRUNCATE TABLE etl_audit_log RESTART IDENTITY;
TRUNCATE TABLE etl_watermarks;
TRUNCATE TABLE etl_control RESTART IDENTITY CASCADE;
TRUNCATE TABLE source_products;
TRUNCATE TABLE destination_csv_table;
TRUNCATE TABLE destination_api_table;
TRUNCATE TABLE destination_db_table;
TRUNCATE TABLE destination_failed_table;

INSERT INTO source_products (id, name, category, price, last_modified) VALUES
    (1, 'prod_1', 'electronics', 100.00, '2026-03-20T10:00:00Z'),
    (2, 'prod_2', 'toys', 20.50, '2026-03-20T11:00:00Z'),
    (3, 'prod_3', 'books', 40.00, '2026-03-20T12:00:00Z'),
    (4, 'prod_4', 'home', 80.75, '2026-03-20T13:00:00Z'),
    (5, 'prod_5', 'sports', 55.25, '2026-03-20T14:00:00Z');

INSERT INTO etl_control (
    pipeline_name,
    source_type,
    source_options,
    destination_table,
    load_type,
    incremental_key,
    dependencies,
    is_active
) VALUES
    (
        'pipeline-A',
        'csv',
        '{"path": "/app/data/source_data.csv"}',
        'destination_csv_table',
        'full',
        NULL,
        ARRAY[]::TEXT[],
        TRUE
    ),
    (
        'pipeline-B',
        'db',
        '{"table": "source_products"}',
        'destination_db_table',
        'full',
        NULL,
        ARRAY['pipeline-A'],
        TRUE
    ),
    (
        'api-incremental',
        'api',
        '{"url": "http://mock-api:8000/data"}',
        'destination_api_table',
        'incremental',
        'last_modified',
        ARRAY[]::TEXT[],
        TRUE
    ),
    (
        'failing-pipeline',
        'csv',
        '{"path": "/app/data/does_not_exist.csv"}',
        'destination_failed_table',
        'full',
        NULL,
        ARRAY[]::TEXT[],
        FALSE
    ),
    (
        'cycle-A',
        'csv',
        '{"path": "/app/data/source_data.csv"}',
        'destination_csv_table',
        'full',
        NULL,
        ARRAY['cycle-B'],
        FALSE
    ),
    (
        'cycle-B',
        'csv',
        '{"path": "/app/data/source_data.csv"}',
        'destination_csv_table',
        'full',
        NULL,
        ARRAY['cycle-A'],
        FALSE
    );
