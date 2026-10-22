"""Convert integers to Roman numerals and Roman numerals to integers."""

from __future__ import annotations

NUMERALS = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)


def to_roman(n: int) -> str:
    """Return the standard Roman numeral for n."""
    if n < 1 or n > 3999:
        raise ValueError("number must be between 1 and 3999")
    parts = []
    for value, symbol in NUMERALS:
        while n >= value:
            parts.append(symbol)
            n -= value
    return "".join(parts)


SYMBOL_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def from_roman(s: str) -> int:
    """Return the integer value of the Roman numeral s, in any letter case."""
    if not s.strip():
        raise ValueError("empty input")
    if any(symbol not in "IVXLCDMivxlcdm" for symbol in s):
        raise ValueError(f"invalid Roman numeral: {s!r}")
    upper = s.upper()
    total = 0
    for i, symbol in enumerate(upper):
        value = SYMBOL_VALUES[symbol]
        if i + 1 < len(upper) and SYMBOL_VALUES[upper[i + 1]] > value:
            total -= value
        else:
            total += value
    if total < 1 or total > 3999 or to_roman(total) != upper:
        raise ValueError(f"invalid Roman numeral: {s!r}")
    return total


def is_valid(s: str) -> bool:
    """Return True if s is a Roman numeral that from_roman accepts."""
    if not isinstance(s, str):
        return False
    try:
        from_roman(s)
    except ValueError:
        return False
    return True
