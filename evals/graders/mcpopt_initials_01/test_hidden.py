from names.initials import initials


def test_rules() -> None:
    assert initials("Ada Lovelace") == "A.L."
    assert initials("  grace   hopper ") == "G.H."
    assert initials("") == ""
    assert initials("   ") == ""
    assert initials("x") == "X."
