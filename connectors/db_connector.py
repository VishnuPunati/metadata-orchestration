import pandas as pd
from sqlalchemy import text

from utils.db import get_engine


def extract(source_options, incremental_key=None, watermark=None):
    table = source_options.get("table")
    query = source_options.get("query")
    if not table and not query:
        raise ValueError("DB source_options must include 'table' or 'query'")

    engine = get_engine()
    with engine.begin() as connection:
        if query:
            statement = text(query)
            df = pd.read_sql_query(statement, connection)
        else:
            sql = f"SELECT * FROM {table}"
            params = {}
            if watermark is not None and incremental_key:
                sql += f" WHERE {incremental_key} > :watermark"
                params["watermark"] = watermark
            df = pd.read_sql_query(text(sql), connection, params=params)

    return df
