from shipping import surcharge


def test_weight_and_zone() -> None:
    assert surcharge(2, "B") == 400
    assert surcharge(1, "C") == 300
    assert surcharge(3, "Z") == 0
    assert surcharge(-1, "A") == 0
