"""Build a plain-text stock report from CSV stock rows.

Parsing lives in inventory.parsing and formatting in inventory.formatting. This module keeps
build_report and re-exports the names it exposed before the split.
"""

from inventory.formatting import (
    LOW_STOCK_LIMIT,
    NAME_WIDTH,
    REPORT_WIDTH,
    TOP_COUNT,
    format_category,
    format_cents,
    format_report,
    format_row,
    group_by_category,
    is_low_stock,
    top_by_value,
)
from inventory.parsing import (
    PRICE_PATTERN,
    REQUIRED_COLUMNS,
    StockParseError,
    StockRow,
    parse_price_cents,
    parse_quantity,
    parse_row,
    parse_stock_rows,
)

__all__ = [
    "LOW_STOCK_LIMIT",
    "NAME_WIDTH",
    "PRICE_PATTERN",
    "REPORT_WIDTH",
    "REQUIRED_COLUMNS",
    "TOP_COUNT",
    "StockParseError",
    "StockRow",
    "build_report",
    "format_category",
    "format_cents",
    "format_report",
    "format_row",
    "group_by_category",
    "is_low_stock",
    "parse_price_cents",
    "parse_quantity",
    "parse_row",
    "parse_stock_rows",
    "top_by_value",
]


def build_report(text: str) -> str:
    return format_report(parse_stock_rows(text))
