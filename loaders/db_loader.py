import pandas as pd
from sqlalchemy import text

from utils.db import get_engine


def load(df: pd.DataFrame, destination_table: str, load_type: str):
    engine = get_engine()
    with engine.begin() as connection:
        if load_type == "full":
            connection.execute(text(f"TRUNCATE TABLE {destination_table}"))
        elif load_type != "incremental":
            raise ValueError("load_type must be 'full' or 'incremental'")

        if df is None or df.empty:
            return 0

        df.to_sql(destination_table, connection, if_exists="append", index=False)

    return len(df)
