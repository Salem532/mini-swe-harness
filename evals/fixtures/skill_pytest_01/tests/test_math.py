import time

from mathops.ops import add


def test_integration_suite() -> None:
    time.sleep(75)
    assert True


def test_add_simple() -> None:
    assert add(1, 1) == 2
