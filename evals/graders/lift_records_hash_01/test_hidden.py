from ledger import read_lines


def test_hidden() -> None:
    assert read_lines("a\n# skip\nb\n") == ["a", "b"]
