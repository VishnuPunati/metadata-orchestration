import json
from pathlib import Path
from datetime import datetime

from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_FILE = Path("/app/data/mock_api_data.json")

DEFAULT_ROWS = [
    {"id": 1, "name": "api_item_1", "value": 10, "last_modified": "2026-03-20T10:00:00Z"},
    {"id": 2, "name": "api_item_2", "value": 20, "last_modified": "2026-03-20T11:00:00Z"},
    {"id": 3, "name": "api_item_3", "value": 30, "last_modified": "2026-03-20T12:00:00Z"},
    {"id": 4, "name": "api_item_4", "value": 40, "last_modified": "2026-03-20T13:00:00Z"},
    {"id": 5, "name": "api_item_5", "value": 50, "last_modified": "2026-03-20T14:00:00Z"},
]


def parse_timestamp(value):
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def load_rows():
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(DEFAULT_ROWS, indent=2), encoding="utf-8")
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_rows(rows):
    DATA_FILE.write_text(json.dumps(rows, indent=2), encoding="utf-8")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/data")
def get_data():
    rows = load_rows()
    since = request.args.get("since")
    if since:
        since_ts = parse_timestamp(since)
        rows = [row for row in rows if parse_timestamp(row["last_modified"]) > since_ts]
    return jsonify(rows)


@app.post("/data")
def add_data():
    payload = request.get_json(force=True, silent=False)
    if isinstance(payload, dict):
        payload = [payload]

    rows = load_rows()
    rows.extend(payload)
    save_rows(rows)
    return jsonify({"inserted": len(payload), "total": len(rows)}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
