from numutil.clamp import clamp


def test_hidden() -> None:
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10
    assert clamp(3, 3, 3) == 3
