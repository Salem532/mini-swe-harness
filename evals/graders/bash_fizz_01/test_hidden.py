from fizzbuzz.core import fizzbuzz


def test_more() -> None:
    assert fizzbuzz(15) == "FizzBuzz"
    assert fizzbuzz(30) == "FizzBuzz"
    assert fizzbuzz(7) == "7"
    assert fizzbuzz(10) == "Buzz"
