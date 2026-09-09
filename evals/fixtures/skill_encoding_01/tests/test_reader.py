from pathlib import Path

from csvkit.reader import read_rows


def test_plain_csv(tmp_path: Path) -> None:
    target = tmp_path / "plain.csv"
    target.write_text("name,age\nalice,3\n", encoding="utf-8")
    rows = read_rows(target)
    assert rows == [{"name": "alice", "age": "3"}]
