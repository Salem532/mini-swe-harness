from ledger import split_row


def test_visible() -> None:
    assert split_row("a,b,c") == ["a", "b", "c"]
