from limits import clip


def test_inside() -> None:
    assert clip(5, 0, 10) == 5
