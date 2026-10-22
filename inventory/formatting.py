"""Render a plain-text stock report."""

from __future__ import annotations

from inventory.parsing import StockRow

LOW_STOCK_LIMIT = 5
REPORT_WIDTH = 52
NAME_WIDTH = 20
TOP_COUNT = 3


def format_cents(cents: int) -> str:
    dollars, remainder = divmod(cents, 100)
    return f"${dollars:,}.{remainder:02d}"


def is_low_stock(row: StockRow) -> bool:
    return row.quantity <= LOW_STOCK_LIMIT


def group_by_category(rows: list[StockRow]) -> dict[str, list[StockRow]]:
    groups: dict[str, list[StockRow]] = {}
    for row in rows:
        groups.setdefault(row.category, []).append(row)
    return dict(sorted(groups.items()))


def top_by_value(rows: list[StockRow], count: int = TOP_COUNT) -> list[StockRow]:
    return sorted(rows, key=lambda row: (-row.value_cents, row.sku))[:count]


def format_row(row: StockRow) -> str:
    flag = "  LOW" if is_low_stock(row) else ""
    name = row.name[:NAME_WIDTH]
    value = format_cents(row.value_cents)
    return f"  {row.sku:<8} {name:<{NAME_WIDTH}} {row.quantity:>5} {value:>12}{flag}"


def format_category(category: str, rows: list[StockRow]) -> list[str]:
    total = sum(row.value_cents for row in rows)
    noun = "item" if len(rows) == 1 else "items"
    lines = [f"{category.title()}: {len(rows)} {noun}, {format_cents(total)}"]
    lines.extend(format_row(row) for row in sorted(rows, key=lambda row: row.sku))
    return lines


def format_report(rows: list[StockRow]) -> str:
    if not rows:
        return "No stock rows.\n"
    lines = ["Stock report", "=" * REPORT_WIDTH]
    for category, members in group_by_category(rows).items():
        lines.extend(format_category(category, members))
        lines.append("")
    lines.append("Top by value:")
    lines.extend(f"  {row.sku:<8} {format_cents(row.value_cents):>12}" for row in top_by_value(rows))
    lines.append("")
    low = sorted(row.sku for row in rows if is_low_stock(row))
    lines.append(f"Total value: {format_cents(sum(row.value_cents for row in rows))}")
    lines.append(f"Low stock: {', '.join(low) if low else 'none'}")
    return "\n".join(lines) + "\n"
