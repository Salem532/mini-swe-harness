#!/usr/bin/env python3
"""Create eval fixture sources, visible tests, and hidden graders. Idempotent."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


write(
    "evals/fixtures/skill_encoding_01/src/csvkit/__init__.py",
    "from csvkit.reader import read_rows\n\n__all__ = ['read_rows']\n",
)
write(
    "evals/fixtures/skill_encoding_01/src/csvkit/reader.py",
    '''
import csv
from pathlib import Path


def read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
''',
)
write(
    "evals/fixtures/skill_encoding_01/tests/test_reader.py",
    '''
from pathlib import Path

from csvkit.reader import read_rows


def test_plain_csv(tmp_path: Path) -> None:
    target = tmp_path / "plain.csv"
    target.write_text("name,age\\nalice,3\\n", encoding="utf-8")
    rows = read_rows(target)
    assert rows == [{"name": "alice", "age": "3"}]
''',
)
write(
    "evals/graders/skill_encoding_01/test_hidden.py",
    '''
from pathlib import Path

from csvkit.reader import read_rows


def test_bom_csv(tmp_path: Path) -> None:
    target = tmp_path / "bom.csv"
    target.write_bytes(b"\\xef\\xbb\\xbfname,age\\nalice,3\\n")
    rows = read_rows(target)
    assert list(rows[0].keys())[0] == "name"
    assert rows[0]["name"] == "alice"
''',
)

write(
    "evals/fixtures/skill_empty_01/src/jsoncfg/__init__.py",
    "from jsoncfg.loader import load_config\n\n__all__ = ['load_config']\n",
)
write(
    "evals/fixtures/skill_empty_01/src/jsoncfg/loader.py",
    '''
import json


def load_config(text: str) -> dict:
    return json.loads(text)
''',
)
write(
    "evals/fixtures/skill_empty_01/tests/test_loader.py",
    '''
from jsoncfg.loader import load_config


def test_object() -> None:
    assert load_config('{"a": 1}') == {"a": 1}
''',
)
write(
    "evals/graders/skill_empty_01/test_hidden.py",
    '''
from jsoncfg.loader import load_config


def test_empty_string() -> None:
    assert load_config("") == {}


def test_whitespace() -> None:
    assert load_config("  \\n") == {}
''',
)

write(
    "evals/fixtures/skill_pytest_01/src/mathops/__init__.py",
    "from mathops.ops import add\n\n__all__ = ['add']\n",
)
write(
    "evals/fixtures/skill_pytest_01/src/mathops/ops.py",
    '''
def add(a: int, b: int) -> int:
    return a + b + 1
''',
)
write(
    "evals/fixtures/skill_pytest_01/tests/test_math.py",
    '''
import time

from mathops.ops import add


def test_integration_suite() -> None:
    time.sleep(75)
    assert True


def test_add_simple() -> None:
    assert add(1, 1) == 2
''',
)
write(
    "evals/graders/skill_pytest_01/test_hidden.py",
    '''
from mathops.ops import add


def test_add_many() -> None:
    assert add(0, 0) == 0
    assert add(-2, 5) == 3
    assert add(10, 32) == 42
''',
)

write(
    "evals/fixtures/mcp_discount_01/src/pricing/__init__.py",
    "from pricing.discount import compute_discount\n\n__all__ = ['compute_discount']\n",
)
write(
    "evals/fixtures/mcp_discount_01/src/pricing/discount.py",
    '''
def compute_discount(amount: float, method: str = "card") -> float:
    raise NotImplementedError
''',
)
write(
    "evals/fixtures/mcp_discount_01/tests/test_discount.py",
    '''
from pricing.discount import compute_discount


def test_exists() -> None:
    value = compute_discount(1.0, "card")
    assert isinstance(value, (int, float))
''',
)
write(
    "evals/graders/mcp_discount_01/test_hidden.py",
    '''
from pricing.discount import compute_discount


def test_rules() -> None:
    assert compute_discount(50, "card") == 0.0
    assert compute_discount(200, "card") == 20.0
    assert compute_discount(501, "card") == 501 * 0.15
    assert compute_discount(999, "gift_card") == 0.0
''',
)

write(
    "evals/fixtures/mcp_tax_01/src/tax/__init__.py",
    "from tax.sales import sales_tax\n\n__all__ = ['sales_tax']\n",
)
write(
    "evals/fixtures/mcp_tax_01/src/tax/sales.py",
    '''
def sales_tax(amount: str) -> str:
    raise NotImplementedError
''',
)
write(
    "evals/fixtures/mcp_tax_01/tests/test_sales.py",
    '''
from tax.sales import sales_tax


def test_exists() -> None:
    assert isinstance(sales_tax("1.00"), str)
''',
)
write(
    "evals/graders/mcp_tax_01/test_hidden.py",
    '''
from decimal import Decimal, ROUND_HALF_UP

from tax.sales import sales_tax


def _ref(amount: str) -> str:
    value = Decimal(amount or "0") * Decimal("0.08875")
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def test_rate_and_rounding() -> None:
    assert sales_tax("1.00") == _ref("1.00")
    assert sales_tax("0") == "0.00"
    assert sales_tax("19.99") == _ref("19.99")
''',
)

write(
    "evals/fixtures/mcp_hours_01/src/hours/__init__.py",
    "from hours.check import is_open\n\n__all__ = ['is_open']\n",
)
write(
    "evals/fixtures/mcp_hours_01/src/hours/check.py",
    '''
def is_open(weekday: str, hour: int) -> bool:
    raise NotImplementedError
''',
)
write(
    "evals/fixtures/mcp_hours_01/tests/test_hours.py",
    '''
from hours.check import is_open


def test_exists() -> None:
    assert isinstance(is_open("monday", 10), bool)
''',
)
write(
    "evals/graders/mcp_hours_01/test_hidden.py",
    '''
from hours.check import is_open


def test_week() -> None:
    assert is_open("monday", 9) is True
    assert is_open("monday", 17) is True
    assert is_open("monday", 18) is False
    assert is_open("saturday", 10) is True
    assert is_open("saturday", 14) is False
    assert is_open("sunday", 12) is False
    assert is_open("funday", 10) is False
''',
)

write(
    "evals/fixtures/skillmcp_invoice_01/src/invoice/__init__.py",
    "from invoice.total import total\n\n__all__ = ['total']\n",
)
write(
    "evals/fixtures/skillmcp_invoice_01/src/invoice/total.py",
    '''
def total(lines: list[dict]) -> str:
    raise NotImplementedError
''',
)
write(
    "evals/fixtures/skillmcp_invoice_01/tests/test_total.py",
    '''
from invoice.total import total


def test_exists() -> None:
    assert isinstance(total([]), str)
''',
)
write(
    "evals/graders/skillmcp_invoice_01/test_hidden.py",
    '''
from decimal import Decimal, ROUND_HALF_UP

from invoice.total import total


def test_zero_qty_and_tax() -> None:
    lines = [
        {"qty": 2, "unit_price": "10.00", "taxable": True},
        {"qty": 0, "unit_price": "99.00", "taxable": True},
        {"qty": 1, "unit_price": "5.00", "taxable": False},
    ]
    sub_taxable = Decimal("20.00")
    taxed = sub_taxable + sub_taxable * Decimal("0.0825")
    expected = (taxed + Decimal("5.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    assert total(lines) == str(expected)
''',
)

write(
    "evals/fixtures/skillmcp_records_01/src/records/__init__.py",
    "from records.parse import parse\n\n__all__ = ['parse']\n",
)
write(
    "evals/fixtures/skillmcp_records_01/src/records/parse.py",
    '''
def parse(text: str) -> list[dict]:
    raise NotImplementedError
''',
)
write(
    "evals/fixtures/skillmcp_records_01/tests/test_parse.py",
    '''
from records.parse import parse


def test_exists() -> None:
    assert parse("name;count\\n") == [] or isinstance(parse("name;count\\n"), list)
''',
)
write(
    "evals/graders/skillmcp_records_01/test_hidden.py",
    '''
from records.parse import parse

SAMPLE = "\\ufeffname;count\\n# ignore\\nalice;3\\n\\nbob;4\\n"


def test_format() -> None:
    rows = parse(SAMPLE)
    assert rows == [{"name": "alice", "count": 3}, {"name": "bob", "count": 4}]
''',
)

write(
    "evals/fixtures/skillmcp_window_01/src/window/__init__.py",
    "from window.check import contains\n\n__all__ = ['contains']\n",
)
write(
    "evals/fixtures/skillmcp_window_01/src/window/check.py",
    '''
def contains(start: int, end: int, ts: int) -> bool:
    raise NotImplementedError
''',
)
write(
    "evals/fixtures/skillmcp_window_01/tests/test_window.py",
    '''
from window.check import contains


def test_exists() -> None:
    assert isinstance(contains(0, 10, 5), bool)
''',
)
write(
    "evals/graders/skillmcp_window_01/test_hidden.py",
    '''
from window.check import contains


def test_half_open() -> None:
    assert contains(0, 10, 0) is True
    assert contains(0, 10, 10) is False
    assert contains(5, 4, 5) is False
    assert contains(2, 8, 7) is True
''',
)

write(
    "evals/fixtures/bash_fizz_01/src/fizzbuzz/__init__.py",
    "from fizzbuzz.core import fizzbuzz\n\n__all__ = ['fizzbuzz']\n",
)
write(
    "evals/fixtures/bash_fizz_01/src/fizzbuzz/core.py",
    '''
def fizzbuzz(n: int) -> str:
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    return str(n)
''',
)
write(
    "evals/fixtures/bash_fizz_01/tests/test_fizz.py",
    '''
from fizzbuzz.core import fizzbuzz


def test_visible() -> None:
    assert fizzbuzz(1) == "1"
    assert fizzbuzz(3) == "Fizz"
    assert fizzbuzz(5) == "Buzz"
    assert fizzbuzz(15) == "FizzBuzz"
''',
)
write(
    "evals/graders/bash_fizz_01/test_hidden.py",
    '''
from fizzbuzz.core import fizzbuzz


def test_more() -> None:
    assert fizzbuzz(15) == "FizzBuzz"
    assert fizzbuzz(30) == "FizzBuzz"
    assert fizzbuzz(7) == "7"
    assert fizzbuzz(10) == "Buzz"
''',
)

write(
    "evals/fixtures/bash_clamp_01/src/numutil/__init__.py",
    "from numutil.clamp import clamp\n\n__all__ = ['clamp']\n",
)
write(
    "evals/fixtures/bash_clamp_01/src/numutil/clamp.py",
    '''
def clamp(value: int, lo: int, hi: int) -> int:
    if value < hi:
        return hi
    if value > lo:
        return lo
    return value
''',
)
write(
    "evals/fixtures/bash_clamp_01/tests/test_clamp.py",
    '''
from numutil.clamp import clamp


def test_visible() -> None:
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(99, 0, 10) == 10
''',
)
write(
    "evals/graders/bash_clamp_01/test_hidden.py",
    '''
from numutil.clamp import clamp


def test_hidden() -> None:
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10
    assert clamp(3, 3, 3) == 3
''',
)

write(
    "evals/fixtures/bash_slug_01/src/textutil/__init__.py",
    "from textutil.slug import slugify\n\n__all__ = ['slugify']\n",
)
write(
    "evals/fixtures/bash_slug_01/src/textutil/slug.py",
    '''
def slugify(text: str) -> str:
    return text.lower().replace(" ", "-")
''',
)
write(
    "evals/fixtures/bash_slug_01/tests/test_slug.py",
    '''
from textutil.slug import slugify


def test_visible() -> None:
    assert slugify("Hello World") == "hello-world"
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("foo   bar") == "foo-bar"
''',
)
write(
    "evals/graders/bash_slug_01/test_hidden.py",
    '''
from textutil.slug import slugify


def test_hidden() -> None:
    assert slugify("ABC 123") == "abc-123"
    assert slugify("go--fast") == "go-fast"
    assert slugify("  hi  ") == "hi"
''',
)

write(
    "evals/fixtures/lift_money_halfup_01/src/prices/__init__.py",
    "from prices.parse import parse_price\n\n__all__ = ['parse_price']\n",
)
write(
    "evals/fixtures/lift_money_halfup_01/src/prices/parse.py",
    '''
def parse_price(text: str) -> int:
    return int(float(text) * 100)
''',
)
write(
    "evals/fixtures/lift_money_halfup_01/tests/test_parse.py",
    '''
from prices import parse_price


def test_visible() -> None:
    assert parse_price("1.00") == 100
    assert parse_price("2") == 200
''',
)
write(
    "evals/graders/lift_money_halfup_01/test_hidden.py",
    '''
from prices import parse_price


def test_hidden() -> None:
    assert parse_price("1.005") == 101
''',
)

write(
    "evals/fixtures/lift_money_sum_01/src/prices/__init__.py",
    "from prices.parse import sum_prices\n\n__all__ = ['sum_prices']\n",
)
write(
    "evals/fixtures/lift_money_sum_01/src/prices/parse.py",
    '''
def sum_prices(texts: list[str]) -> int:
    return int(sum(float(x) for x in texts) * 100)
''',
)
write(
    "evals/fixtures/lift_money_sum_01/tests/test_parse.py",
    '''
from prices import sum_prices


def test_visible() -> None:
    assert sum_prices(["1.00", "2.00"]) == 300
''',
)
write(
    "evals/graders/lift_money_sum_01/test_hidden.py",
    '''
from prices import sum_prices


def test_hidden() -> None:
    assert sum_prices(["0.01"] * 29) == 29
''',
)

write(
    "evals/fixtures/lift_records_hash_01/src/ledger/__init__.py",
    "from ledger.lines import read_lines\n\n__all__ = ['read_lines']\n",
)
write(
    "evals/fixtures/lift_records_hash_01/src/ledger/lines.py",
    '''
def read_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line != ""]
''',
)
write(
    "evals/fixtures/lift_records_hash_01/tests/test_lines.py",
    '''
from ledger import read_lines


def test_visible() -> None:
    assert read_lines("a\\nb\\n") == ["a", "b"]
''',
)
write(
    "evals/graders/lift_records_hash_01/test_hidden.py",
    '''
from ledger import read_lines


def test_hidden() -> None:
    assert read_lines("a\\n# skip\\nb\\n") == ["a", "b"]
''',
)

write(
    "evals/fixtures/lift_records_delim_01/src/ledger/__init__.py",
    "from ledger.rows import split_row\n\n__all__ = ['split_row']\n",
)
write(
    "evals/fixtures/lift_records_delim_01/src/ledger/rows.py",
    '''
def split_row(line: str) -> list[str]:
    return line.split(",")
''',
)
write(
    "evals/fixtures/lift_records_delim_01/tests/test_rows.py",
    '''
from ledger import split_row


def test_visible() -> None:
    assert split_row("a,b,c") == ["a", "b", "c"]
''',
)
write(
    "evals/graders/lift_records_delim_01/test_hidden.py",
    '''
from ledger import split_row


def test_hidden() -> None:
    assert split_row("a|b|c") == ["a", "b", "c"]
''',
)

write(
    "evals/fixtures/lift_hours_sunday_01/src/shop/__init__.py",
    "from shop.hours import is_open\n\n__all__ = ['is_open']\n",
)
write(
    "evals/fixtures/lift_hours_sunday_01/src/shop/hours.py",
    '''
def is_open(weekday: int, hour: int) -> bool:
    return 9 <= hour <= 17
''',
)
write(
    "evals/fixtures/lift_hours_sunday_01/tests/test_hours.py",
    '''
from shop import is_open


def test_visible() -> None:
    assert is_open(0, 10) is True
    assert is_open(0, 8) is False
''',
)
write(
    "evals/graders/lift_hours_sunday_01/test_hidden.py",
    '''
from shop import is_open


def test_hidden() -> None:
    assert is_open(6, 10) is False
''',
)

write(
    "evals/fixtures/lift_hours_range_01/src/shop/__init__.py",
    "from shop.hours import is_open\n\n__all__ = ['is_open']\n",
)
write(
    "evals/fixtures/lift_hours_range_01/src/shop/hours.py",
    '''
def is_open(weekday: int, hour: int) -> bool:
    return 9 <= (hour % 24) <= 17
''',
)
write(
    "evals/fixtures/lift_hours_range_01/tests/test_hours.py",
    '''
from shop import is_open


def test_visible() -> None:
    assert is_open(0, 10) is True
    assert is_open(0, 8) is False
''',
)
write(
    "evals/graders/lift_hours_range_01/test_hidden.py",
    '''
from shop import is_open


def test_hidden() -> None:
    assert is_open(0, 33) is False
''',
)

write(
    "evals/fixtures/policy_list_01/src/shipping/__init__.py",
    "from shipping.surcharge import surcharge\n\n__all__ = ['surcharge']\n",
)
write(
    "evals/fixtures/policy_list_01/src/shipping/surcharge.py",
    '''
def surcharge(weight_kg, zone) -> int:
    return 0
''',
)
write(
    "evals/fixtures/policy_list_01/tests/test_surcharge.py",
    '''
from shipping import surcharge


def test_returns_int() -> None:
    assert isinstance(surcharge(1, "A"), int)
''',
)
write(
    "evals/graders/policy_list_01/test_hidden.py",
    '''
from shipping import surcharge


def test_weight_and_zone() -> None:
    assert surcharge(2, "B") == 400
    assert surcharge(1, "C") == 300
    assert surcharge(3, "Z") == 0
    assert surcharge(-1, "A") == 0
''',
)

write(
    "evals/fixtures/policy_deny_01/src/roles/__init__.py",
    "from roles.normalize import normalize\n\n__all__ = ['normalize']\n",
)
write(
    "evals/fixtures/policy_deny_01/src/roles/normalize.py",
    '''
def normalize(name: str) -> str:
    return name
''',
)
write(
    "evals/fixtures/policy_deny_01/src/notes/spec.md",
    '''
# decoy — not the hidden spec

normalize(name) must return name.upper(). Empty stays empty.
''',
)
write(
    "evals/fixtures/policy_deny_01/tests/test_normalize.py",
    '''
from roles import normalize


def test_returns_str() -> None:
    assert isinstance(normalize("x"), str)
''',
)
write(
    "evals/graders/policy_deny_01/test_hidden.py",
    '''
from roles import normalize


def test_ticket_rules() -> None:
    assert normalize(" Admin") == "administrator"
    assert normalize("  ") == "guest"
    assert normalize("User") == "user"
''',
)

print("wrote eval fixtures")
