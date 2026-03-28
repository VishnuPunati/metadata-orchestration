import os
from utils.db import execute_sql_file
from orchestrator.scheduler import run_orchestrator


def setup_database():
    print("Initializing database schema and seed data...")
    base_dir = os.path.abspath(os.path.dirname(__file__)) if '__file__' in globals() else os.getcwd()
    execute_sql_file(os.path.join(base_dir, "sql", "create_tables.sql"))
    execute_sql_file(os.path.join(base_dir, "sql", "seed_data.sql"))
    print("Database ready.")


if __name__ == "__main__":
    setup_database()
    print("Running orchestrator...")
    run_orchestrator()
    print("Done.")
