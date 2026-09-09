from mathops.ops import add


def test_add_many() -> None:
    assert add(0, 0) == 0
    assert add(-2, 5) == 3
    assert add(10, 32) == 42
