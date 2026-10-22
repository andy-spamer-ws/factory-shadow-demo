"""Tests for the stock report: parsing, formatting and the two together."""

import pytest

from inventory.report import (
    StockParseError,
    StockRow,
    build_report,
    format_category,
    format_cents,
    format_report,
    format_row,
    group_by_category,
    is_low_stock,
    parse_price_cents,
    parse_quantity,
    parse_row,
    parse_stock_rows,
    top_by_value,
)

HEADER = "sku,name,category,quantity,unit_price"

SAMPLE_CSV = (
    "\n".join(
        [
            HEADER,
            "a100,Hex bolt M8,hardware,120,0.35",
            "a200,Torque wrench,tools,3,45.00",
            "a300,Claw hammer,tools,18,12.50",
            "b100,Safety goggles,safety,4,8.99",
            "b200,Work gloves,safety,40,6.25",
            "c100,Cable ties 100pk,hardware,5,3.10",
        ]
    )
    + "\n"
)

SAMPLE_REPORT = (
    "\n".join(
        [
            "Stock report",
            "=" * 52,
            "Hardware: 2 items, $57.50",
            "  A100     Hex bolt M8            120       $42.00",
            "  C100     Cable ties 100pk         5       $15.50  LOW",
            "",
            "Safety: 2 items, $285.96",
            "  B100     Safety goggles           4       $35.96  LOW",
            "  B200     Work gloves             40      $250.00",
            "",
            "Tools: 2 items, $360.00",
            "  A200     Torque wrench            3      $135.00  LOW",
            "  A300     Claw hammer             18      $225.00",
            "",
            "Top by value:",
            "  B200          $250.00",
            "  A300          $225.00",
            "  A200          $135.00",
            "",
            "Total value: $703.46",
            "Low stock: A200, B100, C100",
        ]
    )
    + "\n"
)


def make_row(sku="A1", name="Widget", category="tools", quantity=10, price=100):
    return StockRow(sku, name, category, quantity, price)


@pytest.mark.parametrize(("text", "expected"), [("7", 7), (" 12 ", 12), ("0", 0)])
def test_parse_quantity_reads_whole_numbers(text, expected):
    assert parse_quantity(text, 2) == expected


@pytest.mark.parametrize("text", ["abc", "", "1.5"])
def test_parse_quantity_rejects_non_integers(text):
    with pytest.raises(StockParseError, match="line 4: quantity .* is not a whole number"):
        parse_quantity(text, 4)


def test_parse_quantity_rejects_negative_numbers():
    with pytest.raises(StockParseError, match="line 3: quantity -3 is negative"):
        parse_quantity("-3", 3)


@pytest.mark.parametrize(
    ("text", "cents"),
    [("12.50", 1250), ("$3", 300), (" $0.05 ", 5), ("7.5", 750), ("0", 0), ("1000.00", 100000)],
)
def test_parse_price_cents_reads_prices(text, cents):
    assert parse_price_cents(text, 2) == cents


@pytest.mark.parametrize("text", ["abc", "", "1.234", "-2", "1.", ".5"])
def test_parse_price_cents_rejects_bad_prices(text):
    with pytest.raises(StockParseError, match="line 5: price .* is not a price"):
        parse_price_cents(text, 5)


def test_parse_row_normalises_fields():
    raw = {"sku": " ab12 ", "name": " Hex bolt ", "category": " Hardware ", "quantity": "7", "unit_price": "$1.50"}
    assert parse_row(raw, 2) == StockRow("AB12", "Hex bolt", "hardware", 7, 150)


def test_parse_row_falls_back_to_sku_and_uncategorised():
    parsed = parse_row({"sku": "x1", "name": "", "category": None, "quantity": "1", "unit_price": "1"}, 2)
    assert (parsed.name, parsed.category) == ("X1", "uncategorised")


def test_parse_row_rejects_empty_sku():
    with pytest.raises(StockParseError, match="line 6: sku is empty"):
        parse_row({"sku": "  ", "quantity": "1", "unit_price": "1"}, 6)


def test_parse_row_rejects_missing_quantity():
    with pytest.raises(StockParseError, match="quantity"):
        parse_row({"sku": "a1", "quantity": None, "unit_price": "1"}, 2)


def test_parse_stock_rows_reads_every_row_in_order():
    rows = parse_stock_rows(SAMPLE_CSV)
    assert [row.sku for row in rows] == ["A100", "A200", "A300", "B100", "B200", "C100"]
    assert rows[0] == StockRow("A100", "Hex bolt M8", "hardware", 120, 35)


def test_parse_stock_rows_header_only_gives_no_rows():
    assert parse_stock_rows(HEADER + "\n") == []


def test_parse_stock_rows_names_every_missing_column():
    with pytest.raises(StockParseError, match="missing columns: category, unit_price"):
        parse_stock_rows("sku,name,quantity\na1,Widget,3\n")


def test_parse_stock_rows_rejects_empty_input():
    with pytest.raises(StockParseError, match="missing columns: sku, name, category, quantity, unit_price"):
        parse_stock_rows("")


def test_parse_stock_rows_rejects_duplicate_skus_ignoring_case():
    text = f"{HEADER}\na1,Widget,tools,1,1.00\nA1,Other,tools,2,2.00\n"
    with pytest.raises(StockParseError, match="line 3: duplicate sku A1"):
        parse_stock_rows(text)


def test_parse_stock_rows_reports_physical_line_numbers_after_blank_lines():
    text = f"{HEADER}\na1,Widget,tools,1,1.00\n\na2,Gadget,tools,many,2.00\n"
    with pytest.raises(StockParseError, match="line 4: quantity 'many'"):
        parse_stock_rows(text)


def test_value_cents_multiplies_quantity_by_price():
    assert make_row(quantity=3, price=250).value_cents == 750


@pytest.mark.parametrize(
    ("cents", "text"),
    [(0, "$0.00"), (5, "$0.05"), (100, "$1.00"), (123456, "$1,234.56")],
)
def test_format_cents(cents, text):
    assert format_cents(cents) == text


@pytest.mark.parametrize(("quantity", "low"), [(0, True), (5, True), (6, False)])
def test_is_low_stock_includes_the_limit(quantity, low):
    assert is_low_stock(make_row(quantity=quantity)) is low


def test_group_by_category_sorts_categories_and_keeps_row_order():
    rows = [make_row("B", category="tools"), make_row("A", category="safety"), make_row("C", category="tools")]
    groups = group_by_category(rows)
    assert list(groups) == ["safety", "tools"]
    assert [row.sku for row in groups["tools"]] == ["B", "C"]


def test_top_by_value_orders_by_value_then_sku():
    rows = [
        make_row("C", quantity=1, price=500),
        make_row("B", quantity=5, price=100),
        make_row("A", quantity=5, price=100),
        make_row("D", quantity=1, price=1),
    ]
    assert [row.sku for row in top_by_value(rows)] == ["A", "B", "C"]
    assert [row.sku for row in top_by_value(rows, count=1)] == ["A"]


def test_format_row_aligns_columns_and_flags_low_stock():
    row = make_row("A1", "Widget", quantity=3, price=250)
    assert format_row(row) == "  A1       Widget                   3        $7.50  LOW"


def test_format_row_truncates_long_names_and_omits_the_flag_when_stocked():
    row = make_row("A1", "A very long product name indeed", quantity=50, price=100)
    assert format_row(row) == "  A1       A very long product     50       $50.00"


def test_format_category_pluralises_and_sorts_by_sku():
    lines = format_category("tools", [make_row("B", quantity=1, price=100), make_row("A", quantity=2, price=100)])
    assert lines[0] == "Tools: 2 items, $3.00"
    assert [line.split()[0] for line in lines[1:]] == ["A", "B"]


def test_format_category_uses_the_singular_for_one_item():
    assert format_category("tools", [make_row()])[0] == "Tools: 1 item, $10.00"


def test_format_report_without_rows():
    assert format_report([]) == "No stock rows.\n"


def test_format_report_without_low_stock_says_none():
    text = format_report([make_row("A1", quantity=50)])
    assert text.endswith("Total value: $50.00\nLow stock: none\n")


def test_build_report_end_to_end():
    assert build_report(SAMPLE_CSV) == SAMPLE_REPORT


def test_build_report_propagates_parse_errors():
    with pytest.raises(StockParseError, match="line 2: sku is empty"):
        build_report(f"{HEADER}\n,Widget,tools,1,1.00\n")
