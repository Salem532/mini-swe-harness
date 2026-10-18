from tags import slug


def test_local_spec() -> None:
    assert slug(" Hello World! ") == "hello-world"
    assert slug("A--B") == "a-b"
    assert slug("***") == ""
