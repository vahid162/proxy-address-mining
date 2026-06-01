import hashlib
import json
import os
import subprocess
from pathlib import Path

SCRIPT_PATH = Path("scripts/phase11_run_limited_acceptance_decision_gate.sh")
SCRIPT = SCRIPT_PATH.read_text()


def test_helper_runs_only_decision_gate_and_writes_manifests():
    assert '"$MPF_BIN" production phase11-limited-acceptance-decision-gate' in SCRIPT
    assert SCRIPT.count('"$MPF_BIN" production ') == 1
    assert "manifest.json" in SCRIPT and "sha256-manifest.txt" in SCRIPT and "sudo -u mpf" in SCRIPT


def test_helper_has_no_forbidden_mutation_commands():
    for marker in ("iptables-restore", "conntrack -F", "conntrack -D", "docker restart", "docker compose up", "docker compose down", "docker compose restart", "systemctl restart", "systemctl enable", "mpf customer activate", "mpf abuse hard", "mpf abuse unhard", "INSERT ", "UPDATE ", "DELETE ", "ALTER ", "DROP ", "TRUNCATE ", "psql "):
        assert marker not in SCRIPT


def test_helper_writes_output_hash_and_manifest(tmp_path):
    def artifact(name):
        path = tmp_path / f"{name}.json"; path.write_text("{}\n")
        return path, hashlib.sha256(path.read_bytes()).hexdigest()
    window, window_sha = artifact("window"); readiness, readiness_sha = artifact("readiness"); gate, gate_sha = artifact("gate")
    fake = tmp_path / "fake-mpf"
    fake.write_text("#!/usr/bin/env bash\nset -euo pipefail\nout=\nwhile [ $# -gt 0 ]; do if [ \"$1\" = --out-json ]; then out=$2; shift 2; else shift; fi; done\nprintf '%s\\n' '{\"final_decision\":\"PHASE11_LIMITED_ACCEPTANCE_DECISION_GATE_READY\"}' > \"$out\"\n")
    fake.chmod(0o755); out = tmp_path / "out"
    env = {**os.environ, "MPF_BIN": str(fake)}
    subprocess.run([str(SCRIPT_PATH), "--expected-version", "0.1.231", "--observation-window-json", str(window), "--observation-window-json-sha256", window_sha,
        "--final-readiness-planning-json", str(readiness), "--final-readiness-planning-json-sha256", readiness_sha, "--artifact-gate-json", str(gate),
        "--artifact-gate-json-sha256", gate_sha, "--out-dir", str(out), "--operator", "operator", "--reason", "read-only"], check=True, env=env)
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["component"] == "phase11_limited_acceptance_decision_gate_helper"
    assert manifest["mutation_performed"] is False
    assert (out / "phase11-limited-acceptance-decision-gate.sha256").is_file()
    assert (out / "sha256-manifest.txt").is_file()
