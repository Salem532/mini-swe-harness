from pathlib import Path

from csvkit.reader import read_rows


def test_bom_csv(tmp_path: Path) -> None:
    target = tmp_path / "bom.csv"
    target.write_bytes(b"\xef\xbb\xbfname,age\nalice,3\n")
    rows = read_rows(target)
    assert list(rows[0].keys())[0] == "name"
    assert rows[0]["name"] == "alice"
