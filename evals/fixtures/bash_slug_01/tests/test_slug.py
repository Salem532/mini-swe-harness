from textutil.slug import slugify


def test_visible() -> None:
    assert slugify("Hello World") == "hello-world"
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("foo   bar") == "foo-bar"
