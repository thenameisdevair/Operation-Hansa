import json
import os
import tempfile
from pathlib import Path
from models import TaskLogEntry

_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "task_log.json")


def _log_path() -> str:
    return os.environ.get("TASK_LOG_PATH", _LOG_PATH)


def ensure_log_file_exists() -> None:
    path = Path(_log_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")


def append_task_log(entry: TaskLogEntry) -> None:
    ensure_log_file_exists()
    path = Path(_log_path())
    data = json.loads(path.read_text(encoding="utf-8"))
    data.append(entry.model_dump())
    # atomic write: write to temp then rename
    dir_ = path.parent
    with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False, suffix=".tmp", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        tmp = f.name
    os.replace(tmp, path)


def load_all_logs() -> list[dict]:
    ensure_log_file_exists()
    return json.loads(Path(_log_path()).read_text(encoding="utf-8"))


def find_log_by_task_id(task_id: str) -> dict | None:
    return next((e for e in load_all_logs() if e.get("task_id") == task_id), None)
