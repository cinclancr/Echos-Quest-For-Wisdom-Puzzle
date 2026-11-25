"""End-to-end CLI behaviour on the synthetic fixture (no network, no secrets)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "synthetic_fixture.txt"
FIXTURE_SHA256 = "a90833bcffd70afca2a25dc586091ab41727808b28f5dcea5cf233763b7233c6"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "echoquest", *args],
        capture_output=True,
        text=True,
        cwd=REPO,
        env={"PYTHONPATH": str(REPO / "src"), "PATH": "/usr/bin:/bin", "HOME": "/tmp"},
    )


def test_ingest_ok() -> None:
    r = _run("ingest", "--input", str(FIXTURE), "--sha256", FIXTURE_SHA256)
    assert r.returncode == 0, r.stderr
    assert FIXTURE_SHA256 in r.stdout


def test_ingest_wrong_hash_fails() -> None:
    r = _run("ingest", "--input", str(FIXTURE), "--sha256", "00" * 32)
    assert r.returncode != 0


def test_audit_runs() -> None:
    r = _run("audit", "--input", str(FIXTURE), "--sha256", "none")
    assert r.returncode == 0, r.stderr
    assert "94" in r.stdout  # token count


def test_positions_csv(tmp_path) -> None:
    out = tmp_path / "pos.csv"
    r = _run("positions", "--input", str(FIXTURE), "--sha256", "none", "--output", str(out))
    assert r.returncode == 0, r.stderr
    lines = out.read_text().strip().splitlines()
    assert lines[0].startswith("index,")
    assert len(lines) == 95  # header + 94 tokens


def test_extract_all_writes_csv(tmp_path) -> None:
    out = tmp_path / "ext.csv"
    r = _run(
        "extract", "--input", str(FIXTURE), "--sha256", "none", "--method", "all", "--output", str(out)
    )
    assert r.returncode == 0, r.stderr
    assert out.exists()


def test_list_methods() -> None:
    r = _run("list-methods")
    assert r.returncode == 0
    assert "midpoint-32" in r.stdout


def test_verify_against_target_is_readonly(tmp_path) -> None:
    # a candidate file with one (checksum-invalid) synthetic 12-word line
    cand = tmp_path / "cand.txt"
    cand.write_text("echo silk identify echo silk identify echo silk identify echo silk army\n")
    out = tmp_path / "verification.json"
    r = _run(
        "verify",
        "--candidate-file",
        str(cand),
        "--output",
        str(out),
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(out.read_text())
    assert data["target"] == "1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx"
    assert data["matches"] == 0
    # checksum-invalid candidate is still derived (no checksum gate)
    assert data["reports"][0]["comparisons"] > 0


def test_hypotheses_listing() -> None:
    r = _run("hypotheses")
    assert r.returncode == 0, r.stderr
    assert "midpoint-32" in r.stdout or "HYPOTHESIS" in r.stdout
