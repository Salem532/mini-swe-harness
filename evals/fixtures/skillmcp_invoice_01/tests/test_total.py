from invoice.total import total


def test_exists() -> None:
    assert isinstance(total([]), str)
