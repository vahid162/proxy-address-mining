#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/phase11_controlled_artifact_refresh.sh MODE [options]

Modes:
  --plan               Build the controlled stale-artifact refresh plan (read-only).
  --package            Build the controlled stale-artifact refresh package (read-only).
  --execute-preflight  Run hash/drift/restore-test preflight before any execute.
  --execute            Execute only after READY preflight and explicit env/script gates.
  --verify             Verify corrected post-DNAT graph after controlled refresh.
  --rollback-test      Emit rollback-test placeholder; manual rollback review is required.

Common options:
  --out-dir DIR
  --config PATH
  --expected-version VERSION

Package/preflight/execute options:
  --package-json PATH
  --package-sha256 SHA256
  --operator NAME
  --reason TEXT
  --yes

This wrapper never starts Docker/systemd, never flushes conntrack, and never
performs DB/customer/policy/abuse mutation. The only mutating mode is --execute,
and it requires MPF_PHASE11_CONTROLLED_ARTIFACT_REFRESH=allow,
MPF_PHASE11_CONTROLLED_ARTIFACT_REFRESH_EXECUTE=allow, --yes, a valid package
hash, a fresh READY live preflight, an exclusive lock, and iptables-restore
--test --noflush success before iptables-restore --noflush.
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

MODE="$1"
shift
OUT_DIR=""
CONFIG="/etc/mpf/mpf.yaml"
EXPECTED_VERSION=""
PACKAGE_JSON=""
PACKAGE_SHA256=""
OPERATOR=""
REASON=""
YES="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out-dir) OUT_DIR="${2:-}"; shift 2 ;;
    --config) CONFIG="${2:-}"; shift 2 ;;
    --expected-version) EXPECTED_VERSION="${2:-}"; shift 2 ;;
    --package-json) PACKAGE_JSON="${2:-}"; shift 2 ;;
    --package-sha256) PACKAGE_SHA256="${2:-}"; shift 2 ;;
    --operator) OPERATOR="${2:-}"; shift 2 ;;
    --reason) REASON="${2:-}"; shift 2 ;;
    --yes) YES="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$EXPECTED_VERSION" ]]; then
  EXPECTED_VERSION="$(python - <<'PY'
from mpf import __version__
print(__version__)
PY
)"
fi

if [[ -n "$OUT_DIR" ]]; then
  if [[ -L "$OUT_DIR" ]]; then
    echo "out-dir symlink forbidden" >&2
    exit 2
  fi
  mkdir -p "$OUT_DIR"
fi

run_refresh_python() {
  local action="$1"
  ACTION="$action" OUT_DIR="$OUT_DIR" CONFIG="$CONFIG" EXPECTED_VERSION="$EXPECTED_VERSION" PACKAGE_JSON="$PACKAGE_JSON" PACKAGE_SHA256="$PACKAGE_SHA256" OPERATOR="$OPERATOR" REASON="$REASON" YES="$YES" python - <<'PY'
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from mpf.config import load_config
from mpf.repositories import firewall_planner_read_repo
from mpf.services import phase11_controlled_artifact_refresh_service as refresh
from mpf.services import phase11_controlled_backend_target_service


def emit(report: dict) -> None:
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, default=str))


def fail(blockers: list[str], component: str = "phase11_controlled_artifact_refresh_script") -> None:
    emit({"component": component, "repository_version": os.environ["EXPECTED_VERSION"], "blockers": blockers, "final_decision": "BLOCKED_CONTROLLED_ARTIFACT_REFRESH_SCRIPT", "mutation_performed": False})
    sys.exit(1)


def cmd_stdout(argv: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, input=input_text, text=True, capture_output=True, check=False)


def load_inputs() -> tuple[list[dict], list[dict], dict, str, str, str]:
    cfg = load_config(Path(os.environ["CONFIG"]))
    loaded = firewall_planner_read_repo.load_firewall_planner_input(cfg)
    if not loaded.ok:
        fail(["postgresql_planner_input_read_failed", loaded.message])
    backend = phase11_controlled_backend_target_service.build_controlled_backend_target_report(expected_version=os.environ["EXPECTED_VERSION"])
    ipt = cmd_stdout(["iptables-save"])
    ip6 = cmd_stdout(["ip6tables-save"])
    if ipt.returncode != 0 or ip6.returncode != 0:
        fail(["iptables_snapshot_failed"])
    phase = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8") if Path("docs/PHASE_STATUS.md").exists() else ""
    return loaded.lanes, loaded.customers, backend, ipt.stdout, ip6.stdout, phase


def live_plan() -> dict:
    lanes, customers, backend, ipt, ip6, phase = load_inputs()
    return refresh.build_refresh_plan(lanes=lanes, customers=customers, backend_target=backend, iptables_save_text=ipt, ip6tables_save_text=ip6, phase_status_text=phase, expected_version=os.environ["EXPECTED_VERSION"])


def write_json(name: str, data: dict) -> None:
    out_dir = os.environ.get("OUT_DIR") or ""
    if out_dir:
        path = Path(out_dir) / name
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        tmp.chmod(0o600)
        os.replace(tmp, path)


def read_package() -> dict:
    path = os.environ.get("PACKAGE_JSON") or ""
    expected_sha = os.environ.get("PACKAGE_SHA256") or ""
    if not path or not expected_sha:
        fail(["package_json_and_sha256_required"])
    raw = Path(path).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha:
        fail(["package_sha256_mismatch"])
    return json.loads(raw.decode())


action = os.environ["ACTION"]
if action == "plan":
    plan = live_plan()
    write_json("controlled-artifact-refresh-plan.json", plan)
    emit(plan)
elif action == "package":
    plan = live_plan()
    package = refresh.build_refresh_package_from_plan(plan)
    verify = refresh.verify_refresh_package(package, live_plan=plan)
    write_json("controlled-artifact-refresh-plan.json", plan)
    write_json("controlled-artifact-refresh-package.json", package)
    write_json("controlled-artifact-refresh-verify.json", verify)
    emit(package)
elif action in {"execute-preflight", "execute"}:
    package = read_package()
    plan = live_plan()
    restore_test = cmd_stdout(["iptables-restore", "--test", "--noflush"], input_text=str(package.get("payload", "")))
    preflight = refresh.build_refresh_execute_preflight(package, live_plan=plan, restore_test_result={"returncode": restore_test.returncode, "stderr": restore_test.stderr})
    write_json("controlled-artifact-refresh-execute-preflight.json", preflight)
    if action == "execute-preflight":
        emit(preflight)
        sys.exit(0 if preflight.get("final_decision") == refresh.REFRESH_PREFLIGHT_READY else 1)
    if os.environ.get("YES") != "true" or os.environ.get("MPF_PHASE11_CONTROLLED_ARTIFACT_REFRESH") != "allow" or os.environ.get("MPF_PHASE11_CONTROLLED_ARTIFACT_REFRESH_EXECUTE") != "allow":
        preflight["blockers"] = sorted(set([*preflight.get("blockers", []), "explicit_execute_gates_required"]))
        preflight["final_decision"] = refresh.REFRESH_PREFLIGHT_BLOCKED
        emit(preflight)
        sys.exit(1)
    if preflight.get("final_decision") != refresh.REFRESH_PREFLIGHT_READY:
        emit(preflight)
        sys.exit(1)
    out_dir = Path(os.environ.get("OUT_DIR") or ".")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pre-apply-iptables-save.txt").write_text(cmd_stdout(["iptables-save"]).stdout, encoding="utf-8")
    (out_dir / "pre-apply-ip6tables-save.txt").write_text(cmd_stdout(["ip6tables-save"]).stdout, encoding="utf-8")
    apply_result = cmd_stdout(["iptables-restore", "--noflush"], input_text=str(package.get("payload", "")))
    report = {"component": "phase11_controlled_artifact_refresh_execute", "repository_version": os.environ["EXPECTED_VERSION"], "package_id": package.get("package_id"), "operator": os.environ.get("OPERATOR"), "reason": os.environ.get("REASON"), "restore_test_invoked": True, "apply_invoked": True, "apply_returncode": apply_result.returncode, "stderr": apply_result.stderr, "firewall_mutation_performed": apply_result.returncode == 0, "final_decision": "CONTROLLED_ARTIFACT_REFRESH_EXECUTED_PENDING_REVIEW" if apply_result.returncode == 0 else "BLOCKED_CONTROLLED_ARTIFACT_REFRESH_EXECUTE", "blockers": [] if apply_result.returncode == 0 else ["iptables_restore_apply_failed"]}
    write_json("controlled-artifact-refresh-execute.json", report)
    emit(report)
    sys.exit(0 if apply_result.returncode == 0 else 1)
elif action == "verify":
    package = read_package()
    plan = live_plan()
    # Caller should pass a current-controlled-artifact-gate report separately in a later PR; this script keeps verify fail-closed unless such report is wired.
    report = refresh.verify_post_apply_refresh(package=package, post_apply_plan=plan, current_gate_report=None)
    write_json("controlled-artifact-refresh-post-apply-verify.json", report)
    emit(report)
    sys.exit(0 if report.get("final_decision") == refresh.REFRESH_VERIFY_READY else 1)
elif action == "rollback-test":
    package = read_package()
    report = {"component": "phase11_controlled_artifact_refresh_rollback_test", "repository_version": os.environ["EXPECTED_VERSION"], "package_id": package.get("package_id"), "manual_review_required": True, "automatic_rollback_execution_available": False, "mutation_performed": False, "final_decision": "CONTROLLED_ARTIFACT_REFRESH_ROLLBACK_TEST_READY", "blockers": []}
    emit(report)
else:
    fail([f"unsupported_action:{action}"])
PY
}

case "$MODE" in
  --plan) run_refresh_python plan ;;
  --package) run_refresh_python package ;;
  --execute-preflight)
    [[ -n "$PACKAGE_JSON" && -n "$PACKAGE_SHA256" ]] || { echo "--execute-preflight requires --package-json and --package-sha256" >&2; exit 2; }
    run_refresh_python execute-preflight
    ;;
  --execute)
    [[ "$YES" == "true" ]] || { echo "--execute requires --yes" >&2; exit 2; }
    [[ -n "$PACKAGE_JSON" && -n "$PACKAGE_SHA256" && -n "$OPERATOR" && -n "$REASON" ]] || { echo "--execute requires --package-json, --package-sha256, --operator, --reason" >&2; exit 2; }
    mkdir -p /run
    exec 9>/run/mpf-phase11-controlled-artifact-refresh.lock
    flock -n 9 || { echo "controlled artifact refresh lock is already held" >&2; exit 1; }
    run_refresh_python execute
    ;;
  --verify)
    [[ -n "$PACKAGE_JSON" && -n "$PACKAGE_SHA256" ]] || { echo "--verify requires --package-json and --package-sha256" >&2; exit 2; }
    run_refresh_python verify
    ;;
  --rollback-test)
    [[ -n "$PACKAGE_JSON" && -n "$PACKAGE_SHA256" ]] || { echo "--rollback-test requires --package-json and --package-sha256" >&2; exit 2; }
    run_refresh_python rollback-test
    ;;
  -h|--help) usage ;;
  *) echo "unknown mode: ${MODE}" >&2; usage; exit 2 ;;
esac
