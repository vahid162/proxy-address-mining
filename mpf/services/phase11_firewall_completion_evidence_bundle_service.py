"""Read-only Phase 11 firewall completion evidence bundle builder/verifier."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from mpf import __version__

READY = "PHASE11_FIREWALL_COMPLETION_EVIDENCE_BUNDLE_PREFLIGHT_READY"
BLOCKED = "BLOCKED_PHASE11_FIREWALL_COMPLETION_EVIDENCE_BUNDLE_PREFLIGHT"

_REQUIRED_JSON = (
    "controlled-backend-target.json",
    "current-controlled-artifact-gate-with-target.json",
    "production-firewall-apply-verify-rollback-readiness.json",
    "manifest.json",
)
_REQUIRED_TEXT = ("iptables-save.txt", "ip6tables-save.txt", "SHA256SUMS.txt")
_ALTERNATIVES = (
    ("controlled-artifact-reapply-plan-target-aware.json", "controlled-artifact-reapply-plan.json"),
    ("controlled-artifact-reapply-package-target-aware.json", "controlled-artifact-reapply-package.json"),
    ("controlled-artifact-reapply-readiness-target-aware.json", "controlled-artifact-reapply-readiness.json"),
)
_MUTATION_KEYS = (
    "mutation_performed", "db_mutation_performed", "firewall_apply_performed", "iptables_restore_performed",
    "rollback_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed",
    "abuse_execute_performed", "customer_mutation_performed", "policy_mutation_performed", "event_audit_mutation_performed",
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path, blockers: list[str]) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"malformed_json:{path.name}")
        return {"_load_error": str(exc)}
    if not isinstance(data, dict):
        blockers.append(f"json_root_not_object:{path.name}")
        return {"_load_error": "json_root_not_object"}
    return data


def _read_sha256s(path: Path, base: Path, blockers: list[str]) -> dict[str, str]:
    sums: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"sha256s_unreadable:{exc}")
        return sums
    for line in lines:
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2:
            blockers.append("sha256s_malformed")
            continue
        digest, rel = parts
        rel = rel[1:] if rel.startswith("*") else rel
        rel = rel[2:] if rel.startswith("./") else rel
        if rel == "SHA256SUMS.txt":
            continue
        sums[rel] = digest
        target = base / rel
        if not target.exists():
            blockers.append(f"sha256s_references_missing_file:{rel}")
        elif _sha256(target) != digest:
            blockers.append(f"sha256_mismatch:{rel}")
    return sums


def write_manifest_and_sha256s(bundle_dir: Path | str) -> dict[str, object]:
    base = Path(bundle_dir)
    base.mkdir(parents=True, exist_ok=True)
    files = sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS.txt"})
    manifest = {"component": "phase11_firewall_completion_evidence_bundle_manifest", "repository_version": __version__, "files": files}
    (base / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    all_files = sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
    (base / "SHA256SUMS.txt").write_text("".join(f"{_sha256(base / rel)}  {rel}\n" for rel in all_files), encoding="utf-8")
    return manifest


def verify_firewall_completion_evidence_bundle(bundle_dir: Path | str | None) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    if bundle_dir is None:
        blockers.append("bundle_dir_missing")
        base = None
    else:
        base = Path(bundle_dir)
        if not base.is_dir():
            blockers.append("bundle_dir_missing")
    docs: dict[str, dict[str, Any]] = {}
    selected: dict[str, str | None] = {}
    if base is not None and base.is_dir():
        for name in (*_REQUIRED_JSON, *_REQUIRED_TEXT):
            if not (base / name).exists():
                blockers.append(f"required_file_missing:{name}")
        for group in _ALTERNATIVES:
            found = next((name for name in group if (base / name).exists()), None)
            selected[group[0]] = found
            if found is None:
                blockers.append(f"required_file_missing:{'|'.join(group)}")
        for path in sorted(base.glob("*.json")):
            docs[path.name] = _load_json(path, blockers)
        if (base / "manifest.json").exists():
            manifest = docs.get("manifest.json") or _load_json(base / "manifest.json", blockers)
            manifest_files = manifest.get("files")
            if not isinstance(manifest_files, list):
                blockers.append("manifest_files_missing_or_invalid")
            else:
                actual = sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS.txt"})
                for rel in actual:
                    if rel not in manifest_files:
                        blockers.append(f"manifest_missing_file:{rel}")
                for rel in manifest_files:
                    if not (base / str(rel)).exists():
                        blockers.append(f"manifest_references_missing_file:{rel}")
        if (base / "SHA256SUMS.txt").exists():
            sums = _read_sha256s(base / "SHA256SUMS.txt", base, blockers)
            for rel in sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"):
                if rel not in sums:
                    blockers.append(f"sha256s_missing_file:{rel}")

    backend = docs.get("controlled-backend-target.json", {})
    gate = docs.get("current-controlled-artifact-gate-with-target.json", {})
    readiness = docs.get("production-firewall-apply-verify-rollback-readiness.json", {})
    gate_target = gate.get("backend_target") if isinstance(gate.get("backend_target"), dict) else {}
    target_host = backend.get("resolved_ipv4") or backend.get("target_host") or gate_target.get("host")
    target_port = backend.get("target_port") or gate_target.get("port")
    if not target_host or not target_port:
        blockers.append("backend_target_missing")
    if backend.get("backend_public_exposure") is True or gate.get("backend_public_exposure") is True:
        blockers.append("backend_public_exposure_true")
    if gate.get("unknown_mpf_artifacts"):
        blockers.append("unknown_mpf_artifacts_non_empty")
    if int(gate.get("duplicate_nat_redirect_count") or 0) != 0:
        blockers.append("duplicate_nat_redirect_count_non_zero")
    if gate.get("forbidden_public_runtime_exposure") is True:
        blockers.append("forbidden_public_runtime_exposure_true")
    if gate and gate.get("current_phase_gate_ok") is not True:
        blockers.append("current_phase_gate_not_ok")
    phase = str(gate.get("current_working_phase") or gate.get("current_phase") or "Phase 11 operational completion")
    production_traffic = str(gate.get("production_traffic") or "controlled_cli_limited")
    customer_onboarding = str(gate.get("customer_onboarding_allowed") or "controlled_cli_limited")
    if "Phase 11" not in phase or "operational completion" not in phase:
        blockers.append("current_phase_gate_not_phase11_operational_completion")
    if production_traffic != "controlled_cli_limited" or customer_onboarding != "controlled_cli_limited":
        blockers.append("current_phase_gate_not_controlled_cli_limited")
    if gate.get("phase12_start_allowed") in (True, "true", "yes") or readiness.get("phase12_start_allowed") in (True, "true", "yes"):
        blockers.append("phase12_start_allowed_true")
    for name, doc in docs.items():
        for key in _MUTATION_KEYS:
            if doc.get(key) is True:
                blockers.append(f"mutation_flag_true:{name}:{key}")
    clean = not blockers
    return {
        "component": "phase11_firewall_completion_evidence_bundle",
        "repository_version": __version__,
        "evidence_dir": str(bundle_dir) if bundle_dir is not None else None,
        "bundle_preflight_ready": clean,
        "production_firewall_apply_verify_rollback": "missing_or_partial",
        "full_cli_production_operations": "missing_or_partial",
        "selected_alternative_files": selected,
        "safety_state": {
            "backend_target": f"{target_host}:{target_port}" if target_host and target_port else None,
            "backend_public_exposure": bool(backend.get("backend_public_exposure") or gate.get("backend_public_exposure")),
            "unknown_mpf_artifacts": gate.get("unknown_mpf_artifacts", []),
            "duplicate_nat_redirect_count": gate.get("duplicate_nat_redirect_count"),
            "forbidden_public_runtime_exposure": gate.get("forbidden_public_runtime_exposure"),
            "phase12_start_allowed": False,
            "mutation_performed": False,
        },
        "blockers": sorted(set(blockers)),
        "warnings": warnings,
        "final_decision": READY if clean else BLOCKED,
        "next_required_step": "production_firewall_apply_verify_rollback",
        "phase12_start_allowed": False,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
    }


def build_firewall_completion_evidence_bundle(out_dir: Path | str, *, iptables_save_file: Path | None = None, ip6tables_save_file: Path | None = None) -> dict[str, object]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    def copy_or_run(name: str, src: Path | None, cmd: str) -> None:
        dest = out / name
        if src is not None:
            shutil.copyfile(src, dest)
            return
        try:
            with dest.open("w", encoding="utf-8") as fh:
                subprocess.run([cmd], check=True, stdout=fh, text=True)  # noqa: S603,S607 - read-only snapshot command.
        except FileNotFoundError:
            dest.write_text("", encoding="utf-8")
    copy_or_run("iptables-save.txt", iptables_save_file, "iptables-save")
    copy_or_run("ip6tables-save.txt", ip6tables_save_file, "ip6tables-save")
    write_manifest_and_sha256s(out)
    return verify_firewall_completion_evidence_bundle(out)
