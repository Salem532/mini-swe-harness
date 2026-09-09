from __future__ import annotations

from pathlib import Path

from mini_swe_harness.skills import render_catalog, scan_skills


def test_scan_builtin_skills() -> None:
    skills, skipped = scan_skills()
    names = {skill.name for skill in skills}
    assert names == {"pytest-debug", "repo-qa", "mcp-ticket-context"}
    assert skipped == []
    for skill in skills:
        assert "when" in skill.description.lower() or "Use when" in skill.description


def test_catalog_omits_bodies() -> None:
    skills, _ = scan_skills()
    catalog = render_catalog(skills)
    assert "Available skills" in catalog or "pytest-debug" in catalog
    for skill in skills:
        marker = skill.body.strip().splitlines()[0]
        if marker.startswith("#"):
            assert marker not in catalog
    assert "SKILL.md" in catalog
    assert "scripts/" not in catalog or "Load" in catalog


def test_invalid_skill_is_skipped(tmp_path: Path) -> None:
    bad = tmp_path / "NotValid"
    bad.mkdir()
    (bad / "SKILL.md").write_text("no frontmatter\n", encoding="utf-8")
    good = tmp_path / "ok-skill"
    good.mkdir()
    (good / "SKILL.md").write_text(
        "---\nname: ok-skill\ndescription: Does a thing. Use when testing the loader.\n---\n\n# SecretBodyTokenXYZ\n",
        encoding="utf-8",
    )
    skills, skipped = scan_skills(tmp_path)
    assert [s.name for s in skills] == ["ok-skill"]
    assert len(skipped) == 1
    catalog = render_catalog(skills)
    assert "SecretBodyTokenXYZ" not in catalog
