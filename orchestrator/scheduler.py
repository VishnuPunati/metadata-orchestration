from pathlib import Path

from orchestrator.dependency_resolver import DependencyResolverError, topological_sort
from orchestrator.pipeline_executor import run_pipeline
from utils.db import get_pipelines, wait_for_database
from utils.logger import get_logger

logger = get_logger(__name__)
READY_FILE = Path("/tmp/orchestrator.ready")


def run_orchestrator():
    logger.info("Waiting for database connectivity")
    wait_for_database()
    READY_FILE.write_text("ready", encoding="utf-8")

    pipelines = get_pipelines()
    if not pipelines:
        logger.warning("No active pipelines found")
        return {"status": "empty", "results": []}

    try:
        ordered_pipelines = topological_sort(pipelines)
    except DependencyResolverError as exc:
        logger.error("Error: %s", exc)
        return {"status": "dependency_error", "error": str(exc), "results": []}

    results = []
    statuses = {}

    for pipeline in ordered_pipelines:
        dependency_failures = [
            dependency
            for dependency in pipeline.get("dependencies") or []
            if statuses.get(dependency) != "SUCCESS"
        ]
        if dependency_failures:
            logger.warning(
                "Skipping pipeline '%s' because dependency failures were detected: %s",
                pipeline["pipeline_name"],
                ", ".join(dependency_failures),
            )
            statuses[pipeline["pipeline_name"]] = "SKIPPED"
            results.append(
                {
                    "pipeline_name": pipeline["pipeline_name"],
                    "status": "SKIPPED",
                    "rows_read": 0,
                    "rows_written": 0,
                    "error_message": f"Skipped due to dependency failures: {', '.join(dependency_failures)}",
                }
            )
            continue

        result = run_pipeline(pipeline)
        statuses[pipeline["pipeline_name"]] = result["status"]
        results.append(result)

    return {"status": "completed", "results": results}
