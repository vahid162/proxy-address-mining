from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "phase11_controlled_artifact_reapply.sh"
READY_PREFLIGHT = "READY_CONTROLLED_ARTIFACT_REAPPLY_EXECUTION_GATE_PREFLIGHT"
EXECUTED = "CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_fake_mpf(tmp_path: Path, *, preflight: object | str, execute: object | str | None = None) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    state = tmp_path / "state.json"
    config = {"preflight": preflight, "execute": execute, "log": str(tmp_path / "calls.jsonl")}
    state.write_text(json.dumps(config), encoding="utf-8")
    mpf = bin_dir / "mpf"
    mpf.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        f"state = pathlib.Path({str(state)!r})\n"
        "cfg = json.loads(state.read_text())\n"
        "with open(cfg['log'], 'a', encoding='utf-8') as fh:\n"
        "    fh.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "cmd = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == 'production' else ''\n"
        "def emit(value):\n"
        "    if isinstance(value, str):\n"
        "        print(value)\n"
        "    else:\n"
        "        print(json.dumps(value))\n"
        "if cmd == 'controlled-artifact-reapply-execution-gate-preflight':\n"
        "    emit(cfg['preflight']); sys.exit(0)\n"
        "if cmd == 'controlled-artifact-reapply-execute':\n"
        "    emit(cfg['execute']); sys.exit(0)\n"
        "print(json.dumps({'final_decision':'UNEXPECTED'})); sys.exit(0)\n",
        encoding="utf-8",
    )
    mpf.chmod(mpf.stat().st_mode | stat.S_IXUSR)
    return bin_dir


def _package(tmp_path: Path) -> tuple[Path, str]:
    path = tmp_path / "package.json"
    path.write_text('{"package_id":"pkg-1"}\n', encoding="utf-8")
    return path, _sha(path)


def _run(tmp_path: Path, args: list[str], *, preflight: object | str | None = None, execute: object | str | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    bin_dir = _write_fake_mpf(
        tmp_path,
        preflight=preflight if preflight is not None else {"final_decision": READY_PREFLIGHT, "blockers": []},
        execute=execute if execute is not None else {"final_decision": EXECUTED, "blockers": []},
    )
    run_env = os.environ.copy()
    run_env["PATH"] = f"{bin_dir}:{run_env['PATH']}"
    if env:
        run_env.update(env)
    return subprocess.run([str(SCRIPT), *args], cwd=ROOT, env=run_env, text=True, capture_output=True, check=False)


def _base_args(tmp_path: Path, out_dir: Path | None = None) -> list[str]:
    package, package_sha = _package(tmp_path)
    args = [
        "--package-json", str(package),
        "--package-sha256", package_sha,
        "--package-id", "pkg-1",
        "--operator", "operator-1",
        "--reason", "guarded test",
    ]
    if out_dir is not None:
        args.extend(["--out-dir", str(out_dir)])
    return args


def _calls(tmp_path: Path) -> list[list[str]]:
    log = tmp_path / "calls.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def test_execute_preflight_writes_json_manifest_and_exits_zero(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    result = _run(tmp_path, ["--execute-preflight", *_base_args(tmp_path, out_dir)])
    assert result.returncode == 0, result.stderr
    report = out_dir / "controlled-artifact-reapply-execution-gate-preflight.json"
    assert json.loads(report.read_text(encoding="utf-8"))["final_decision"] == READY_PREFLIGHT
    assert "controlled-artifact-reapply-execution-gate-preflight.json" in (out_dir / "manifest.sha256").read_text(encoding="utf-8")
    assert [call[1] for call in _calls(tmp_path)] == ["controlled-artifact-reapply-execution-gate-preflight"]


def test_execute_preflight_blocked_never_calls_execute(tmp_path: Path) -> None:
    result = _run(tmp_path, ["--execute-preflight", *_base_args(tmp_path, tmp_path / "out")], preflight={"final_decision": "BLOCKED", "blockers": []})
    assert result.returncode != 0
    assert all("controlled-artifact-reapply-execute" not in call for call in _calls(tmp_path))


def test_execute_preflight_malformed_json_exits_nonzero(tmp_path: Path) -> None:
    result = _run(tmp_path, ["--execute-preflight", *_base_args(tmp_path, tmp_path / "out")], preflight="not-json")
    assert result.returncode != 0


def test_execute_preflight_non_empty_blockers_exits_nonzero(tmp_path: Path) -> None:
    result = _run(tmp_path, ["--execute-preflight", *_base_args(tmp_path, tmp_path / "out")], preflight={"final_decision": READY_PREFLIGHT, "blockers": ["blocked"]})
    assert result.returncode != 0


def test_execute_without_yes_exits_before_execute(tmp_path: Path) -> None:
    result = _run(tmp_path, ["--execute", *_base_args(tmp_path, tmp_path / "out")], env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY": "allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE": "allow"})
    assert result.returncode != 0
    assert _calls(tmp_path) == []


def test_execute_without_required_env_gates_exits_before_execute(tmp_path: Path) -> None:
    result = _run(tmp_path, ["--execute", "--yes", *_base_args(tmp_path, tmp_path / "out")])
    assert result.returncode != 0
    assert _calls(tmp_path) == []


def test_execute_without_explicit_out_dir_exits_before_execute(tmp_path: Path) -> None:
    result = _run(tmp_path, ["--execute", "--yes", *_base_args(tmp_path)], env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY": "allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE": "allow"})
    assert result.returncode != 0
    assert _calls(tmp_path) == []


def test_execute_with_gates_and_yes_runs_preflight_then_execute_exact_args(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    base = _base_args(tmp_path, out_dir)
    result = _run(tmp_path, ["--execute", "--yes", *base], env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY": "allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE": "allow"})
    assert result.returncode == 0, result.stderr
    calls = _calls(tmp_path)
    assert [call[1] for call in calls] == ["controlled-artifact-reapply-execution-gate-preflight", "controlled-artifact-reapply-execute"]
    execute_call = calls[1]
    package, package_sha = tmp_path / "package.json", _sha(tmp_path / "package.json")
    assert execute_call == [
        "production", "controlled-artifact-reapply-execute",
        "--package-json", str(package),
        "--package-sha256", package_sha,
        "--package-id", "pkg-1",
        "--operator", "operator-1",
        "--reason", "guarded test",
        "--execute", "--yes", "--output", "json",
    ]
    assert (out_dir / "controlled-artifact-reapply-execute.json").exists()
    manifest = (out_dir / "manifest.sha256").read_text(encoding="utf-8")
    assert "controlled-artifact-reapply-execution-gate-preflight.json" in manifest
    assert "controlled-artifact-reapply-execute.json" in manifest


def test_execute_refuses_sha_mismatch(tmp_path: Path) -> None:
    package, _ = _package(tmp_path)
    result = _run(tmp_path, ["--execute", "--yes", "--package-json", str(package), "--package-sha256", "0" * 64, "--package-id", "pkg-1", "--operator", "operator-1", "--reason", "guarded test", "--out-dir", str(tmp_path / "out")], env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY": "allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE": "allow"})
    assert result.returncode != 0
    assert _calls(tmp_path) == []


def test_execute_non_ready_preflight_exits_before_execute(tmp_path: Path) -> None:
    result = _run(tmp_path, ["--execute", "--yes", *_base_args(tmp_path, tmp_path / "out")], preflight={"final_decision": "BLOCKED", "blockers": []}, env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY": "allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE": "allow"})
    assert result.returncode != 0
    assert [call[1] for call in _calls(tmp_path)] == ["controlled-artifact-reapply-execution-gate-preflight"]


def test_execute_failed_decisions_exit_nonzero(tmp_path: Path) -> None:
    for decision in ["FAILED_PRE_APPLY", "FAILED_APPLY", "FAILED_POST_APPLY_VERIFICATION"]:
        case_dir = tmp_path / decision
        case_dir.mkdir()
        result = _run(case_dir, ["--execute", "--yes", *_base_args(case_dir, case_dir / "out")], execute={"final_decision": decision, "blockers": []}, env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY": "allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE": "allow"})
        assert result.returncode != 0, decision


def test_static_safety_no_forbidden_direct_command_invocations() -> None:
    forbidden = {"iptables", "iptables-restore", "ip6tables", "docker", "systemctl", "service", "conntrack", "psql"}
    text = SCRIPT.read_text(encoding="utf-8")
    invocations: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        for segment in re.split(r"(?:^|[;&|])\s*", line):
            segment = segment.strip()
            if not segment or segment.startswith(("then", "do", "else", "elif", "if ", "while ")):
                continue
            try:
                parts = shlex.split(segment, comments=False, posix=True)
            except ValueError:
                continue
            if parts and parts[0] in forbidden:
                invocations.append(parts[0])
    assert invocations == []


def test_static_env_gates_are_not_set_or_exported_to_allow() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for name in ["MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE"]:
        assert not re.search(rf"(^|\n)\s*(?:export\s+)?{name}=allow(?:\s|$)", text)
