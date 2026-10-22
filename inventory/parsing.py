"""Read CSV stock rows."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass

REQUIRED_COLUMNS = ("sku", "name", "category", "quantity", "unit_price")
PRICE_PATTERN = re.compile(r"^\$?([0-9]+)(?:\.([0-9]{1,2}))?$")


class StockParseError(ValueError):
    """A CSV stock row could not be read."""


@dataclass(frozen=True)
class StockRow:
    sku: str
    name: str
    category: str
    quantity: int
    unit_price_cents: int

    @property
    def value_cents(self) -> int:
        return self.quantity * self.unit_price_cents


def parse_quantity(text: str, line: int) -> int:
    try:
        quantity = int(text.strip())
    except ValueError:
        raise StockParseError(f"line {line}: quantity {text!r} is not a whole number") from None
    if quantity < 0:
        raise StockParseError(f"line {line}: quantity {quantity} is negative")
    return quantity


def parse_price_cents(text: str, line: int) -> int:
    match = PRICE_PATTERN.match(text.strip())
    if not match:
        raise StockParseError(f"line {line}: price {text!r} is not a price")
    whole, fraction = match.groups()
    return int(whole) * 100 + int((fraction or "").ljust(2, "0"))


def parse_row(raw: dict[str, str], line: int) -> StockRow:
    sku = (raw.get("sku") or "").strip().upper()
    if not sku:
        raise StockParseError(f"line {line}: sku is empty")
    name = (raw.get("name") or "").strip()
    category = (raw.get("category") or "").strip().lower()
    return StockRow(
        sku=sku,
        name=name or sku,
        category=category or "uncategorised",
        quantity=parse_quantity(raw.get("quantity") or "", line),
        unit_price_cents=parse_price_cents(raw.get("unit_price") or "", line),
    )


def parse_stock_rows(text: str) -> list[StockRow]:
    reader = csv.DictReader(io.StringIO(text))
    missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
    if missing:
        raise StockParseError("missing columns: " + ", ".join(missing))
    rows: list[StockRow] = []
    seen: set[str] = set()
    for raw in reader:
        row = parse_row(raw, reader.line_num)
        if row.sku in seen:
            raise StockParseError(f"line {reader.line_num}: duplicate sku {row.sku}")
        seen.add(row.sku)
        rows.append(row)
    return rows
