from ledger import split_row


def test_hidden() -> None:
    assert split_row("a|b|c") == ["a", "b", "c"]
