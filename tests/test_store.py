"""Tests for resolving the todo file path in todo.store."""

import os
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class TodoPathTest(unittest.TestCase):
    def test_todo_path_uses_todo_file_env_or_defaults_without_touching_disk(self):
        from todo import store

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                with unittest.mock.patch.dict(os.environ, {"TODO_FILE": "/tmp/x/my.json"}):
                    from_env = store.todo_path()
                with unittest.mock.patch.dict(os.environ):
                    os.environ.pop("TODO_FILE", None)
                    when_unset = store.todo_path()
                with unittest.mock.patch.dict(os.environ, {"TODO_FILE": ""}):
                    when_empty = store.todo_path()
                created = sorted(os.listdir(tmp))
            finally:
                os.chdir(original_cwd)

        self.assertEqual(
            (from_env, when_unset, when_empty, created),
            ("/tmp/x/my.json", "todo.json", "todo.json", []),
        )


class LoadTest(unittest.TestCase):
    def test_load_missing_file_returns_empty_state_without_creating_it(self):
        from todo import store

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "todo.json")
            loaded = store.load(path)
            exists_after = os.path.exists(path)

        self.assertEqual(
            (loaded, exists_after),
            ({"next_id": 1, "items": []}, False),
        )

    def test_load_rejects_corrupt_or_wrongly_shaped_file_naming_path_without_writing(self):
        from todo import store

        contents = [
            b"not json",
            b"[]",
            b'{"items": []}',
            b'{"next_id": 1}',
            b'{"next_id": 1, "items": {}}',
            b'{"next_id": "1", "items": []}',
            b'{"next_id": true, "items": []}',
            b'{"next_id": 1.5, "items": []}',
            b'{"next_id": 2, "items": [null]}',
            b'{"next_id": 2, "items": [{"id": 1, "text": "a"}]}',
            b'{"next_id": 2, "items": [{"id": "1", "text": "a", "done": false}]}',
            b'{"next_id": 3, "items": [{"id": 1, "text": "a", "done": false}, {"id": 1, "text": "b", "done": false}]}',
            b'{"next_id": 1, "items": [{"id": 1, "text": "a", "done": false}]}',
            b'{"next_id": 1, "items": [{"id": 0, "text": "a", "done": false}]}',
            b'{"next_id": 0, "items": [{"id": -1, "text": "a", "done": false}]}',
            b'{"next_id": 0, "items": []}',
            b'{"next_id": ' + b"1" * 5000 + b', "items": []}',
        ]
        outcomes = []
        with tempfile.TemporaryDirectory() as d:
            for i, content in enumerate(contents):
                path = os.path.join(d, f"todo{i}.json")
                with open(path, "wb") as f:
                    f.write(content)
                try:
                    store.load(path)
                    outcome = "no error"
                except ValueError as e:
                    outcome = path in str(e)
                with open(path, "rb") as f:
                    unchanged = f.read() == content
                outcomes.append((outcome, unchanged))

        self.assertEqual(outcomes, [(True, True)] * len(contents))

    def test_load_reports_deeply_nested_file_as_invalid_instead_of_recursion_error(self):
        from todo import store

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "todo.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("[" * 100000 + "]" * 100000)
            try:
                store.load(path)
                outcome = ("no error", None)
            except Exception as e:
                outcome = (type(e), str(e))

        self.assertEqual(outcome, (ValueError, f"{path} is not a valid todo file"))


class SaveTest(unittest.TestCase):
    def test_save_round_trips_atomically_and_failed_replace_keeps_old_bytes(self):
        from todo import store

        data = {"next_id": 3, "items": [{"id": 1, "text": "Buy milk", "done": True}]}
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "todo.json")
            store.save(p, data)
            loaded = store.load(p)
            listing_after_save = os.listdir(d)
            with open(p, "rb") as f:
                bytes_before = f.read()

            raised = False
            with unittest.mock.patch("os.replace", side_effect=OSError("boom")) as replace_mock:
                try:
                    store.save(p, {"next_id": 9, "items": []})
                except OSError:
                    raised = True
            with open(p, "rb") as f:
                bytes_after = f.read()
            listing_after_failure = os.listdir(d)

        self.assertEqual(
            (
                loaded,
                listing_after_save,
                raised,
                bytes_after,
                listing_after_failure,
                os.path.dirname(os.path.abspath(replace_mock.call_args[0][0]))
                == os.path.dirname(os.path.abspath(replace_mock.call_args[0][1])),
            ),
            (data, ["todo.json"], True, bytes_before, ["todo.json"], True),
        )


if __name__ == "__main__":
    unittest.main()
