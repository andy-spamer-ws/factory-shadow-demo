"""Pure operations on the todo list state."""

from __future__ import annotations


def add(data: dict, text: str) -> tuple[dict, dict]:
    """Return a new state with a stripped item appended, and the new item. Raise ValueError on blank text."""
    stripped = text.strip()
    if not stripped:
        raise ValueError("todo text must not be empty")
    item = {"id": data["next_id"], "text": stripped, "done": False}
    items = [dict(existing) for existing in data["items"]]
    items.append(item)
    return {**data, "next_id": item["id"] + 1, "items": items}, dict(item)


def mark_done(data: dict, item_id: int) -> tuple[dict, dict]:
    """Return a new state with the item marked done, and that item. Raise KeyError for an unknown id."""
    items = [dict(existing) for existing in data["items"]]
    for item in items:
        if item["id"] == item_id:
            item["done"] = True
            return {**data, "items": items}, dict(item)
    raise KeyError(item_id)


def remove(data: dict, item_id: int) -> tuple[dict, dict]:
    """Return a new state without the item, and that item. Keep next_id so ids are never reused. Raise KeyError for an unknown id."""
    for index, item in enumerate(data["items"]):
        if item["id"] == item_id:
            items = [dict(existing) for existing in data["items"]]
            removed = items.pop(index)
            return {**data, "items": items}, removed
    raise KeyError(item_id)


def open_items(data: dict) -> list:
    """Return copies of the not-done items in their original order."""
    return [dict(item) for item in data["items"] if not item["done"]]
