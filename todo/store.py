"""Locate, load and save the todo list file."""

from __future__ import annotations

import json
import os
import tempfile

DEFAULT_TODO_FILE = "todo.json"


def todo_path() -> str:
    """Return TODO_FILE when set and not empty, else todo.json in the current directory."""
    return os.environ.get("TODO_FILE") or DEFAULT_TODO_FILE


def load(path: str) -> dict:
    """Return the parsed todo file, or a fresh empty state when it does not exist."""
    if not os.path.exists(path):
        return {"next_id": 1, "items": []}
    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except (ValueError, RecursionError):
            raise ValueError(f"{path} is not a valid todo file") from None
    next_id = data.get("next_id") if isinstance(data, dict) else None
    if (
        not isinstance(next_id, int)
        or isinstance(next_id, bool)
        or not isinstance(data.get("items"), list)
    ):
        raise ValueError(f"{path} is not a valid todo file")
    ids = []
    for item in data["items"]:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), int)
            or isinstance(item.get("id"), bool)
            or item["id"] < 1
            or not isinstance(item.get("text"), str)
            or not isinstance(item.get("done"), bool)
        ):
            raise ValueError(f"{path} is not a valid todo file")
        ids.append(item["id"])
    if len(set(ids)) != len(ids) or next_id <= max(ids, default=0):
        raise ValueError(f"{path} is not a valid todo file")
    return data


def save(path: str, data: dict) -> None:
    """Write data as JSON atomically: temp file in the same directory, fsync, then os.replace."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(data))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        os.remove(tmp)
        raise
