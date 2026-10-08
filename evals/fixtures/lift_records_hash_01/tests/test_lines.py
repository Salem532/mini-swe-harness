from ledger import read_lines


def test_visible() -> None:
    assert read_lines("a\nb\n") == ["a", "b"]
