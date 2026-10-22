"""Tests for converting integers to Roman numerals, Roman numerals to integers, and the python -m roman CLI."""

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "roman", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


class ToRomanTest(unittest.TestCase):
    def test_to_roman_returns_standard_numerals(self):
        import roman

        cases = {
            1: "I",
            4: "IV",
            9: "IX",
            40: "XL",
            90: "XC",
            400: "CD",
            900: "CM",
            1994: "MCMXCIV",
            3999: "MMMCMXCIX",
        }
        for n, expected in cases.items():
            with self.subTest(n=n):
                self.assertEqual(roman.to_roman(n), expected)

    def test_to_roman_rejects_out_of_range_numbers(self):
        import roman

        for n in (0, 4000, -5):
            with self.subTest(n=n):
                with self.assertRaises(ValueError) as ctx:
                    roman.to_roman(n)
                self.assertEqual(
                    str(ctx.exception), "number must be between 1 and 3999"
                )


class FromRomanTest(unittest.TestCase):
    def test_from_roman_round_trips_every_number(self):
        import roman

        for n in range(1, 4000):
            with self.subTest(n=n):
                self.assertEqual(roman.from_roman(roman.to_roman(n)), n)

    def test_from_roman_accepts_lowercase_numerals(self):
        import roman

        self.assertEqual(
            (roman.from_roman("mcmxciv"), roman.from_roman("MCMXCIV")),
            (1994, 1994),
        )

    def test_from_roman_rejects_invalid_and_non_canonical_numerals(self):
        import roman

        for s in ("IIII", "VX", "ABC", ""):
            with self.subTest(s=s):
                with self.assertRaises(ValueError):
                    roman.from_roman(s)


class IsValidTest(unittest.TestCase):
    def test_is_valid_accepts_any_letter_case(self):
        import roman

        for s in ("MCMXCIV", "mcmxciv", "McMxCiV"):
            with self.subTest(s=s):
                self.assertIs(roman.is_valid(s), True)

    def test_is_valid_accepts_every_numeral_to_roman_produces(self):
        import roman

        for n in range(1, 4000):
            with self.subTest(n=n):
                self.assertIs(roman.is_valid(roman.to_roman(n)), True)

    def test_is_valid_rejects_invalid_numerals(self):
        import roman

        for s in ("", "   ", "IIII", "MMMM", "ABC"):
            with self.subTest(s=s):
                self.assertIs(roman.is_valid(s), False)

    def test_is_valid_rejects_padded_numerals(self):
        import roman

        for s in (" XIV", "XIV ", "XIV\n"):
            with self.subTest(s=s):
                self.assertIs(roman.is_valid(s), False)

    def test_is_valid_agrees_with_from_roman(self):
        import roman

        def from_roman_accepts(s):
            try:
                roman.from_roman(s)
            except ValueError:
                return False
            return True

        for s in (
            "MCMXCIV",
            "mcmxciv",
            "McMxCiV",
            "XIV",
            "MMMCMXCIX",
            "VX",
            "IC",
            "IL",
            "VV",
            "IIII",
            "MMMM",
            "ABC",
            "\u0131v",
            "",
            "   ",
            " XIV",
            "XIV\n",
        ):
            with self.subTest(s=s):
                self.assertEqual(roman.is_valid(s), from_roman_accepts(s))


class CliTest(unittest.TestCase):
    def test_cli_converts_numbers_and_numerals(self):
        cases = (
            ("1994", "MCMXCIV\n"),
            ("3999", "MMMCMXCIX\n"),
            ("MCMXCIV", "1994\n"),
            ("mcmxciv", "1994\n"),
        )
        for arg, expected in cases:
            with self.subTest(arg=arg):
                result = run_cli(arg)
                self.assertEqual(
                    (result.returncode, result.stdout, result.stderr),
                    (0, expected, ""),
                )

    def test_cli_fails_cleanly_with_one_error_line(self):
        out_of_range = "error: number must be between 1 and 3999"
        cases = (["0"], ["4000"], ["-5"], ["IIII"], ["VX"], ["ABC"], [""], [])
        for args in cases:
            with self.subTest(args=args):
                result = run_cli(*args)
                lines = result.stderr.splitlines()
                observed = (
                    result.returncode,
                    result.stdout,
                    len(lines),
                    bool(lines) and lines[0].startswith("error:"),
                    "Traceback" in result.stderr,
                    result.stderr.strip() == out_of_range
                    if args in (["0"], ["4000"], ["-5"])
                    else True,
                )
                self.assertEqual(observed, (2, "", 1, True, False, True))

    def test_cli_treats_trailing_newline_the_same_for_numbers_and_numerals(self):
        for arg in ("1994\n", "MCMXCIV\n", "5\n", "199\n", "V\n", "CXCIX\n"):
            with self.subTest(arg=arg):
                result = run_cli(arg)
                observed = (
                    result.returncode,
                    result.stdout,
                    len(result.stderr.splitlines()),
                    result.stderr.startswith("error:"),
                    "Traceback" in result.stderr,
                )
                self.assertEqual(observed, (2, "", 1, True, False))

    def test_cli_rejects_non_ascii_digits(self):
        for arg in ("\u0661\u0669\u0669\u0664", "\uff11\uff19\uff19\uff14"):
            with self.subTest(arg=arg):
                result = run_cli(arg)
                observed = (
                    result.returncode,
                    result.stdout,
                    len(result.stderr.splitlines()),
                    result.stderr.startswith("error:"),
                    "Traceback" in result.stderr,
                )
                self.assertEqual(observed, (2, "", 1, True, False))

    def test_cli_rejects_dotless_i(self):
        result = run_cli("\u0131v")
        observed = (
            result.returncode,
            result.stdout,
            len(result.stderr.splitlines()),
            result.stderr.startswith("error:"),
            "Traceback" in result.stderr,
        )
        self.assertEqual(observed, (2, "", 1, True, False))

    def test_cli_reports_range_error_for_very_long_number(self):
        for arg in ("9" * 5000, "0" * 5000):
            with self.subTest(arg=arg):
                result = run_cli(arg)
                self.assertEqual(
                    (result.returncode, result.stdout, result.stderr),
                    (2, "", "error: number must be between 1 and 3999\n"),
                )

    def test_cli_converts_zero_padded_numbers(self):
        cases = (
            ("00001", "I\n"),
            ("0001994", "MCMXCIV\n"),
            ("0" * 100 + "1994", "MCMXCIV\n"),
        )
        for arg, expected in cases:
            with self.subTest(arg=arg):
                result = run_cli(arg)
                self.assertEqual(
                    (result.returncode, result.stdout, result.stderr),
                    (0, expected, ""),
                )


class DocstringTest(unittest.TestCase):
    def test_module_docstring_describes_both_directions(self):
        import roman

        self.assertIn("Roman numerals to integers", roman.__doc__)


if __name__ == "__main__":
    unittest.main()
