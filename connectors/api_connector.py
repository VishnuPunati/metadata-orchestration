import pandas as pd
import requests


def extract(source_options, incremental_key=None, watermark=None):
    url = source_options.get("url")
    if not url:
        raise ValueError("API source_options must include 'url'")

    params = dict(source_options.get("params", {}))
    if watermark is not None:
        params["since"] = watermark

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)

    if watermark is not None and incremental_key and incremental_key in df.columns:
        df[incremental_key] = pd.to_datetime(df[incremental_key], errors="coerce", utc=True)
        df = df[df[incremental_key] > pd.to_datetime(watermark, utc=True)]

    return df
