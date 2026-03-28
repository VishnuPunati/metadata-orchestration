from pathlib import Path

import pandas as pd


def extract(source_options, incremental_key=None, watermark=None):
    path = source_options.get("path")
    if not path:
        raise ValueError("CSV source_options must include 'path'")

    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV source file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    if watermark is not None and incremental_key and incremental_key in df.columns:
        df[incremental_key] = pd.to_datetime(df[incremental_key], errors="coerce", utc=True)
        df = df[df[incremental_key] > pd.to_datetime(watermark, utc=True)]

    return df
