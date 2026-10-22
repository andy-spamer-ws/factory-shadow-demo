"""Tests for adding todo items in todo.items."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class AddTest(unittest.TestCase):
    def test_add_assigns_sequential_ids_strips_text_rejects_blank_and_keeps_input(self):
        from todo import items

        state = {"next_id": 1, "items": []}
        first_state, first = items.add(state, "  Buy milk ")
        _, second = items.add(first_state, "Call Sam")
        try:
            items.add(state, "   ")
            blank_outcome = "no error"
        except ValueError:
            blank_outcome = "ValueError"

        self.assertEqual(
            (first["id"], first["text"], second["id"], blank_outcome, state),
            (1, "Buy milk", 2, "ValueError", {"next_id": 1, "items": []}),
        )


class MarkDoneTest(unittest.TestCase):
    def test_mark_done_flags_one_item_open_items_keeps_order_rejects_unknown_and_keeps_input(self):
        from todo import items

        state = {"next_id": 1, "items": []}
        state, _ = items.add(state, "Buy milk")
        state, _ = items.add(state, "Call Sam")
        state, _ = items.add(state, "Post letter")

        new_state, marked = items.mark_done(state, 1)
        _, marked_again = items.mark_done(new_state, 1)
        open_ids = [item["id"] for item in items.open_items(new_state)]
        unknown_outcomes = []
        for unknown_id in (9, 0):
            try:
                items.mark_done(state, unknown_id)
                unknown_outcomes.append("no error")
            except KeyError:
                unknown_outcomes.append("KeyError")

        self.assertEqual(
            (marked, open_ids, unknown_outcomes, state["items"][0]["done"], marked_again),
            (
                {"id": 1, "text": "Buy milk", "done": True},
                [2, 3],
                ["KeyError", "KeyError"],
                False,
                {"id": 1, "text": "Buy milk", "done": True},
            ),
        )


class RemoveTest(unittest.TestCase):
    def test_remove_never_reuses_ids_rejects_unknown_and_keeps_input(self):
        from todo import items

        state = {"next_id": 1, "items": []}
        state, _ = items.add(state, "a")
        state, _ = items.add(state, "b")

        last_removed_state, last_removed = items.remove(state, 2)
        _, after_last = items.add(last_removed_state, "c")
        first_removed_state, first_removed = items.remove(state, 1)
        _, after_first = items.add(first_removed_state, "c")
        try:
            items.remove(state, 9)
            unknown_outcome = "no error"
        except KeyError:
            unknown_outcome = "KeyError"

        self.assertEqual(
            (
                last_removed["id"],
                after_last["id"],
                first_removed["id"],
                [item["id"] for item in first_removed_state["items"]],
                after_first["id"],
                unknown_outcome,
                [item["id"] for item in state["items"]],
            ),
            (2, 3, 1, [2], 3, "KeyError", [1, 2]),
        )


class CountsTest(unittest.TestCase):
    def test_counts_returns_open_and_done_totals_and_keeps_input(self):
        import copy

        from todo import items

        state = {"next_id": 1, "items": []}
        state, _ = items.add(state, "a")
        state, _ = items.add(state, "b")
        state, _ = items.add(state, "c")
        state, _ = items.mark_done(state, 2)

        state_before = copy.deepcopy(state)
        built_counts = items.counts(state)
        state_after = state

        self.assertEqual(
            (items.counts({"next_id": 1, "items": []}), built_counts, state_after == state_before),
            ((0, 0), (2, 1), True),
        )


if __name__ == "__main__":
    unittest.main()
