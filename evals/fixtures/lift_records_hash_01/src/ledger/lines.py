def read_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line != ""]
