from roles import normalize


def test_ticket_rules() -> None:
    assert normalize(" Admin") == "administrator"
    assert normalize("  ") == "guest"
    assert normalize("User") == "user"
