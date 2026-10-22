"""Tests for the todo command-line interface in todo.__main__."""

import contextlib
import importlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args, env):
    return subprocess.run(
        [sys.executable, "-m", "todo", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


class CliTest(unittest.TestCase):
    def test_commands_persist_state_across_processes_and_empty_list_creates_no_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            todo_file = os.path.join(tmp, "todo.json")
            env = {**os.environ, "TODO_FILE": todo_file}

            commands = [
                ("add", "Buy milk"),
                ("add", "Call Sam"),
                ("list",),
                ("done", "1"),
                ("done", "1"),
                ("list",),
                ("list", "--open"),
                ("remove", "2"),
                ("add", "Post letter"),
            ]
            results = []
            for command in commands:
                result = run_cli(*command, env=env)
                results.append((result.returncode, result.stderr, result.stdout))

            fresh_file = os.path.join(tmp, "fresh.json")
            fresh = run_cli("list", env={**os.environ, "TODO_FILE": fresh_file})
            fresh_result = (
                fresh.returncode,
                fresh.stderr,
                fresh.stdout,
                os.path.exists(fresh_file),
            )

            fresh_open_file = os.path.join(tmp, "fresh_open.json")
            fresh_open = run_cli("list", "--open", env={**os.environ, "TODO_FILE": fresh_open_file})
            fresh_open_result = (
                fresh_open.returncode,
                fresh_open.stderr,
                fresh_open.stdout,
                os.path.exists(fresh_open_file),
            )

        self.assertEqual(
            (results, fresh_result, fresh_open_result),
            (
                [
                    (0, "", "added 1: Buy milk\n"),
                    (0, "", "added 2: Call Sam\n"),
                    (0, "", "1 [ ] Buy milk\n2 [ ] Call Sam\n"),
                    (0, "", "done 1: Buy milk\n"),
                    (0, "", "done 1: Buy milk\n"),
                    (0, "", "1 [x] Buy milk\n2 [ ] Call Sam\n"),
                    (0, "", "2 [ ] Call Sam\n"),
                    (0, "", "removed 2: Call Sam\n"),
                    (0, "", "added 3: Post letter\n"),
                ],
                (0, "", "", False),
                (0, "", "", False),
            ),
        )


BAD_INPUT_CASES = [
    ("done", "9"),
    ("remove", "9"),
    ("done", "abc"),
    ("done", "-1"),
    ("done", "+1"),
    ("done", "1_0"),
    ("done", "1.5"),
    ("done", "\u0661"),
    ("done", "9" * 5000),
    ("add", ""),
    ("add", "   "),
    (),
    ("frobnicate",),
    ("done",),
    ("add",),
]

EXACT_STDERR = {
    ("done", "9"): "error: no item 9\n",
    ("remove", "9"): "error: no item 9\n",
}


class CliBadInputTest(unittest.TestCase):
    def test_bad_input_reports_one_error_line_exits_2_and_leaves_file_unchanged(self):
        observed = []
        expected = []
        for seeded in (False, True):
            for case in BAD_INPUT_CASES:
                with tempfile.TemporaryDirectory() as tmp:
                    todo_file = os.path.join(tmp, "todo.json")
                    env = {**os.environ, "TODO_FILE": todo_file}
                    if seeded:
                        seed = run_cli("add", "Buy milk", env=env)
                        assert seed.returncode == 0, seed.stderr
                    before = Path(todo_file).read_bytes() if os.path.exists(todo_file) else None

                    result = run_cli(*case, env=env)

                    after = Path(todo_file).read_bytes() if os.path.exists(todo_file) else None
                    stderr = result.stderr
                    if case in EXACT_STDERR:
                        stderr_summary = stderr
                    else:
                        lines = stderr.splitlines(keepends=True)
                        well_formed = (
                            len(lines) == 1
                            and lines[0].startswith("error:")
                            and lines[0].endswith("\n")
                            and "Traceback" not in stderr
                        )
                        stderr_summary = "one error line" if well_formed else stderr[-300:]
                    label = (case[0], case[1][:20]) if len(case) > 1 else case
                    observed.append(
                        (label, seeded, result.returncode, result.stdout, stderr_summary, after == before)
                    )
                    expected.append(
                        (label, seeded, 2, "", EXACT_STDERR.get(case, "one error line"), True)
                    )

        self.assertEqual(observed, expected)

    def test_newline_in_unexpected_argument_gives_one_error_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TODO_FILE": os.path.join(tmp, "todo.json")}
            result = run_cli("list", "unexpected\nargument", env=env)

        self.assertEqual(
            (
                result.returncode,
                result.stdout,
                len(result.stderr.splitlines()),
                result.stderr.startswith("error:"),
                "Traceback" in result.stderr,
            ),
            (2, "", 1, True, False),
        )


class CliCorruptFileTest(unittest.TestCase):
    def test_corrupt_todo_file_is_reported_exits_2_and_is_not_overwritten(self):
        observed = []
        with tempfile.TemporaryDirectory() as tmp:
            todo_file = os.path.join(tmp, "todo.json")
            Path(todo_file).write_bytes(b"not json")
            env = {**os.environ, "TODO_FILE": todo_file}
            for command in (("list",), ("add", "x")):
                result = run_cli(*command, env=env)
                observed.append(
                    (command, result.returncode, result.stdout, result.stderr, Path(todo_file).read_bytes())
                )

        expected_stderr = f"error: {todo_file} is not a valid todo file\n"
        self.assertEqual(
            observed,
            [
                (("list",), 2, "", expected_stderr, b"not json"),
                (("add", "x"), 2, "", expected_stderr, b"not json"),
            ],
        )

    def test_deeply_nested_todo_file_is_reported_exits_2_and_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            todo_file = os.path.join(tmp, "todo.json")
            Path(todo_file).write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
            original_bytes = Path(todo_file).read_bytes()
            result = run_cli("list", env={**os.environ, "TODO_FILE": todo_file})
            observed = (result.returncode, result.stdout, result.stderr, Path(todo_file).read_bytes())

        self.assertEqual(
            observed,
            (2, "", f"error: {todo_file} is not a valid todo file\n", original_bytes),
        )


class CliCountTest(unittest.TestCase):
    def test_count_reports_open_and_done_without_writing_and_rejects_corrupt_file(self):
        observed = []
        with tempfile.TemporaryDirectory() as tmp:
            fresh_file = os.path.join(tmp, "fresh.json")
            fresh = run_cli("count", env={**os.environ, "TODO_FILE": fresh_file})
            observed.append((fresh.returncode, fresh.stdout, fresh.stderr, os.path.exists(fresh_file)))

            todo_file = os.path.join(tmp, "todo.json")
            env = {**os.environ, "TODO_FILE": todo_file}
            for command in (("add", "a"), ("add", "b"), ("done", "1")):
                result = run_cli(*command, env=env)
                assert result.returncode == 0, result.stderr
            bytes_before = Path(todo_file).read_bytes()
            counted = run_cli("count", env=env)
            bytes_after = Path(todo_file).read_bytes()
            observed.append((counted.returncode, counted.stdout, counted.stderr, bytes_before == bytes_after))

            corrupt_file = os.path.join(tmp, "corrupt.json")
            Path(corrupt_file).write_bytes(b"not json")
            corrupt = run_cli("count", env={**os.environ, "TODO_FILE": corrupt_file})
            observed.append(
                (corrupt.returncode, corrupt.stdout, corrupt.stderr, Path(corrupt_file).read_bytes())
            )

        self.assertEqual(
            observed,
            [
                (0, "0 open, 0 done\n", "", False),
                (0, "1 open, 1 done\n", "", True),
                (2, "", f"error: {corrupt_file} is not a valid todo file\n", b"not json"),
            ],
        )

    def test_count_on_persisted_empty_file_reports_zero_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            todo_file = os.path.join(tmp, "todo.json")
            Path(todo_file).write_text('{"next_id": 1, "items": []}', encoding="utf-8")
            result = run_cli("count", env={**os.environ, "TODO_FILE": todo_file})

        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "0 open, 0 done\n", ""))


class CliCountNoWriteTest(unittest.TestCase):
    def test_count_on_existing_file_never_calls_store_save(self):
        cli = importlib.import_module("todo.__main__")
        with tempfile.TemporaryDirectory() as tmp:
            todo_file = os.path.join(tmp, "todo.json")
            Path(todo_file).write_text(
                '{"next_id": 3, "items": [{"id": 1, "text": "a", "done": true}, '
                '{"id": 2, "text": "b", "done": false}]}',
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"TODO_FILE": todo_file}), mock.patch(
                "todo.store.save"
            ) as save_spy, contextlib.redirect_stdout(io.StringIO()):
                exit_code = cli.main(["count"])

        self.assertEqual((exit_code, save_spy.call_count), (0, 0))


class CliNoLockFileTest(unittest.TestCase):
    def test_add_done_remove_create_no_lock_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            todo_file = os.path.join(tmp, "todo.json")
            env = {**os.environ, "TODO_FILE": todo_file}
            for command in (("add", "Buy milk"), ("done", "1"), ("remove", "1")):
                result = run_cli(*command, env=env)
                assert result.returncode == 0, result.stderr
            listing = sorted(os.listdir(tmp))

        self.assertEqual(listing, ["todo.json"])


class ReadmeTodoSectionTest(unittest.TestCase):
    def test_readme_todo_section_mentions_count_in_one_line(self):
        lines = (REPO_ROOT / "README.md").read_text(encoding="utf-8").splitlines()
        start = lines.index("## To-do list") + 1
        end = next(
            (i for i in range(start, len(lines)) if lines[i].startswith("## ")),
            len(lines),
        )
        todo_section_lines = lines[start:end]
        self.assertEqual(sum("python3 -m todo count" in line for line in todo_section_lines), 1)
