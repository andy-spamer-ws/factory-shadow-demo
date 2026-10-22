"""Command-line entry point: python -m todo."""

from __future__ import annotations

import argparse
import re
import sys

from todo import items, store

MAX_ID_DIGITS = 4000


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        flat = re.sub(r"\r\n|\r|\n", " ", message)
        sys.stderr.write(f"error: {flat}\n")
        sys.exit(2)


def _item_id(text: str) -> int:
    if len(text) > MAX_ID_DIGITS or not re.fullmatch("[0-9]+", text, re.ASCII):
        raise argparse.ArgumentTypeError("id must be a non-negative whole number")
    return int(text)


def _fail(message: str) -> int:
    sys.stderr.write(f"error: {message}\n")
    return 2


def main(argv=None) -> int:
    parser = _Parser(prog="todo")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    add_parser = sub.add_parser("add")
    add_parser.add_argument("text")
    done_parser = sub.add_parser("done")
    done_parser.add_argument("id", type=_item_id)
    remove_parser = sub.add_parser("remove")
    remove_parser.add_argument("id", type=_item_id)
    list_parser = sub.add_parser("list")
    list_parser.add_argument("--open", action="store_true")
    args = parser.parse_args(argv)

    path = store.todo_path()
    return _run(args, path)


def _run(args, path: str) -> int:
    try:
        data = store.load(path)
    except ValueError:
        return _fail(f"{path} is not a valid todo file")

    if args.command == "list":
        rows = items.open_items(data) if args.open else data["items"]
        for item in rows:
            mark = "x" if item["done"] else " "
            print(f"{item['id']} [{mark}] {item['text']}")
        return 0

    try:
        if args.command == "add":
            data, item = items.add(data, args.text)
            verb = "added"
        elif args.command == "done":
            data, item = items.mark_done(data, args.id)
            verb = "done"
        else:
            data, item = items.remove(data, args.id)
            verb = "removed"
    except KeyError:
        return _fail(f"no item {args.id}")
    except ValueError:
        return _fail("text is empty")
    store.save(path, data)
    print(f"{verb} {item['id']}: {item['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
