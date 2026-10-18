from limits import clip


def test_bounds() -> None:
    assert clip(-1, 0, 10) == 0
    assert clip(11, 0, 10) == 10
    assert clip(3, 3, 3) == 3
