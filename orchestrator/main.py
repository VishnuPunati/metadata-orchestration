import os
import time

from orchestrator.scheduler import run_orchestrator
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    run_once = os.getenv("RUN_ONCE", "true").lower() == "true"
    interval_seconds = int(os.getenv("ORCHESTRATOR_INTERVAL_SECONDS", "300"))

    while True:
        run_orchestrator()
        if run_once:
            break
        logger.info("Sleeping for %s seconds before the next run", interval_seconds)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
