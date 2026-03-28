UPDATE etl_control
SET is_active = CASE
    WHEN pipeline_name = 'failing-pipeline' THEN TRUE
    ELSE is_active
END;
