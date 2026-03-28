UPDATE etl_control
SET is_active = CASE
    WHEN pipeline_name IN ('cycle-A', 'cycle-B') THEN TRUE
    WHEN pipeline_name IN ('pipeline-A', 'pipeline-B', 'api-incremental', 'failing-pipeline') THEN FALSE
    ELSE is_active
END;
