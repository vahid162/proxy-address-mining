#!/usr/bin/env bash
set -euo pipefail

MODE="--plan"
YES="no"
OUT_DIR="${MPF_PHASE11_FIX_EVIDENCE_DIR:-/tmp/phase11-restart-autostart-persistence-fix-$(date +%Y%m%dT%H%M%S%z)}"
MPF_BIN="${MPF_BIN:-mpf}"
PACKAGE_JSON=""

while [ $# -gt 0 ]; do
  case "$1" in
    --plan) MODE="--plan"; shift ;;
    --execute) MODE="--execute"; shift ;;
    --yes) YES="yes"; shift ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [ "$MODE" = "--execute" ] && [ "$YES" != "yes" ]; then
  echo "--execute requires --yes" >&2
  exit 2
fi
if [ "$MODE" != "--plan" ] && [ "$MODE" != "--execute" ]; then
  echo "mode must be --plan or --execute --yes" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"
VERSION_FILE="VERSION"
EXPECTED_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
PACKAGE_JSON="$OUT_DIR/restart_autostart_persistence_fix_package.json"
PLAN_JSON="$OUT_DIR/restart_autostart_persistence_fix_plan.json"
PHASE_STATUS_TXT="$OUT_DIR/phase_status.txt"

"$MPF_BIN" production restart-autostart-persistence-fix-package --expected-version "$EXPECTED_VERSION" --output json | tee "$PACKAGE_JSON"
"$MPF_BIN" production restart-autostart-persistence-fix-plan --expected-version "$EXPECTED_VERSION" --output json | tee "$PLAN_JSON"
"$MPF_BIN" phase-status | tee "$PHASE_STATUS_TXT"

python - "$PACKAGE_JSON" "$PLAN_JSON" "$EXPECTED_VERSION" "$MODE" <<'PY'
import json, sys
package_path, plan_path, expected, mode = sys.argv[1:5]
package = json.load(open(package_path, encoding="utf-8"))
plan = json.load(open(plan_path, encoding="utf-8"))
required_command = "docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime up -d --no-build --pull never"
if package.get("final_decision") != "RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE_READY":
    raise SystemExit("package final_decision is not READY")
if package.get("repository_version") != expected or package.get("expected_version") != expected:
    raise SystemExit("package version does not match repository version")
if package.get("safety_blockers") != []:
    raise SystemExit("package safety_blockers must be empty before execute")
if plan.get("safety_blockers") != []:
    raise SystemExit("plan safety_blockers must be empty before execute")
if mode == "--execute" and not plan.get("repair_reasons"):
    raise SystemExit("plan repair_reasons must identify a controlled runtime repair target")
summary = package.get("phase_gate_summary", {})
if summary.get("phase12_start_allowed") is not False:
    raise SystemExit("Phase 12 must remain blocked")
if summary.get("worker_enforcement_allowed") != "no":
    raise SystemExit("worker enforcement must remain blocked")
if summary.get("ui_allowed") != "no" or summary.get("telegram_allowed") != "no":
    raise SystemExit("UI/Telegram must remain blocked")
if plan.get("phase12_start_allowed") is not False:
    raise SystemExit("plan opened Phase 12")
if plan.get("worker_enforcement_allowed") != "no":
    raise SystemExit("plan opened worker enforcement")
if plan.get("ui_allowed") != "no" or plan.get("telegram_allowed") != "no":
    raise SystemExit("plan opened UI/Telegram")
if package.get("exact_allowed_operation_set") != ["controlled_docker_compose_runtime_reconciliation_up_no_build_pull_never"]:
    raise SystemExit("unexpected allowed operation set")
if plan.get("backend_public_exposure_detected") is True:
    raise SystemExit("backend public exposure detected before execution")
cmd_plan = package.get("exact_docker_compose_command_plan", {})
if cmd_plan.get("project_name") != "mpf-proxy":
    raise SystemExit("unexpected compose project name")
if cmd_plan.get("compose_file") != "compose/mpf-proxy.compose.yaml":
    raise SystemExit("unexpected compose file")
if cmd_plan.get("profile") != "phase4-runtime":
    raise SystemExit("unexpected compose profile")
if package.get("required_execute_command") != required_command:
    raise SystemExit("unexpected execute command")
commands = []
for key in ("required_pre_check_commands", "required_post_check_commands"):
    commands.extend(str(item) for item in package.get(key, []))
commands.append(str(package.get("required_execute_command", "")))
deny = [
    "re" + "boot", "shut" + "down", "system" + "ctl enable", "system" + "ctl start",
    "system" + "ctl restart", "iptables" + "-restore", "conn" + "track -F",
    "mpf customer " + "add", "mpf customer " + "edit", "mpf customer " + "delete", "mpf customer " + "renew",
    "mpf firewall apply", "mpf abuse controlled-execute",
]
for command in commands:
    for token in deny:
        if token in command:
            raise SystemExit(f"forbidden token in reviewed command plan: {token}")
listener_state = plan.get("local_only_listener_state", {}).get("checks", {})
for name, state in listener_state.items():
    if state.get("public_bind_detected") is True:
        raise SystemExit(f"backend public exposure detected before execution: {name}")
PY

# Phase gate text validation is intentionally plain-text and read-only.
grep -q 'current_working_phase: Phase 11 operational completion — Full CLI Production Operations' "$PHASE_STATUS_TXT"
grep -q 'phase12_start_allowed: no' "$PHASE_STATUS_TXT"
grep -q 'worker_enforcement_allowed: no' "$PHASE_STATUS_TXT"
grep -q 'ui_allowed: no' "$PHASE_STATUS_TXT"
grep -q 'telegram_allowed: no' "$PHASE_STATUS_TXT"

if [ "$MODE" = "--plan" ]; then
  python - <<PY
import json
print(json.dumps({"mode":"plan","mutation_performed":False,"evidence_dir":"$OUT_DIR"}, indent=2))
PY
  exit 0
fi

# Only the reviewed Compose reconciliation command is executed in --execute --yes mode.
docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime up -d --no-build --pull never | tee "$OUT_DIR/execute_docker_compose_up.txt"

docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime ps -a | tee "$OUT_DIR/docker_compose_ps_after.txt"
"$MPF_BIN" proxy status | tee "$OUT_DIR/mpf_proxy_status_after.txt"
"$MPF_BIN" proxy doctor | tee "$OUT_DIR/mpf_proxy_doctor_after.txt"
"$MPF_BIN" production restart-autostart-persistence-diagnosis --output json | tee "$OUT_DIR/restart_autostart_persistence_diagnosis_after.json"
"$MPF_BIN" production restart-autostart-proof --output json | tee "$OUT_DIR/restart_autostart_proof_after.json"
"$MPF_BIN" production phase11-operational-completion-gap-inventory --output json | tee "$OUT_DIR/phase11_operational_completion_gap_inventory_after.json"

python - <<PY
import json
print(json.dumps({"mode":"execute","mutation_performed":True,"docker_compose_up_performed":True,"evidence_dir":"$OUT_DIR"}, indent=2))
PY
