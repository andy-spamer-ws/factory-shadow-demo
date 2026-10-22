"""Command-line entry point: python -m roman <number-or-numeral>."""

from __future__ import annotations

import re
import sys

from roman import from_roman, to_roman

INTEGER = re.compile(r"-?[0-9]+")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("error: expected exactly one argument", file=sys.stderr)
        return 2
    arg = args[0]
    try:
        if INTEGER.fullmatch(arg):
            digits = arg.removeprefix("-").lstrip("0")
            if len(digits) > 4:
                raise ValueError("number must be between 1 and 3999")
            n = int(digits or "0")
            print(to_roman(-n if arg.startswith("-") else n))
        else:
            print(from_roman(arg))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
