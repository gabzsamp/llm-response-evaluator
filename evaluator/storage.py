"""Reading tasks and reading/writing evaluation records (JSON and JSON Lines)."""
import json
from pathlib import Path


def load_tasks(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_records(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def append_record(path, record):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def done_task_ids(path):
    """Task ids already evaluated, so a session can be resumed."""
    if not Path(path).exists():
        return set()
    return {r["task_id"] for r in load_records(path)}
