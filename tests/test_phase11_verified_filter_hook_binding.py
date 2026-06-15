from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from mpf import __version__
from mpf.interfaces.cli import app
from mpf.services.phase11_controlled_filter_packet_path_bundle_service import write_packet_path_bundle
from mpf.services.phase11_controlled_filter_packet_path_service import _collect
from mpf.services.phase11_verified_filter_hook_binding_service import (
    READY_BINDING,
    READY_PACKAGE_EVIDENCE,
    READY_VERIFY,
    build_package_evidence,
    build_verified_filter_hook_binding_report,
    verify_package_evidence,
)
from tests.test_phase11_controlled_filter_packet_path import FakeAdapter, PHASE, _stable_proc


def _ready_bundle(tmp_path: Path, monkeypatch, *, outputs=None, require_ready: bool = True) -> Path:
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "0" if "rp_filter" in path else "1")
    monkeypatch.setattr(svc, "_route_localnet_values", lambda: {"ens192": "0", "ens224": "0"})
    ip = json.dumps([
        {"ifname": "ens192", "addr_info": [{"family": "inet", "local": "203.0.113.10", "prefixlen": 24}]},
        {"ifname": "ens224", "addr_info": [{"family": "inet", "local": "203.0.113.11", "prefixlen": 24}]},
    ])
    merged = {"ip_address": ip, **(outputs or {})}
    tmp_path.mkdir(parents=True, exist_ok=True)
    bundle = _collect(adapter=FakeAdapter(outputs=merged), phase_status_text=PHASE, write_dir=None)["bundle"]
    if require_ready:
        assert bundle["decision"]["final_decision"] == "READY_CONTROLLED_FILTER_PACKET_PATH_PROOF"
    out = tmp_path / "bundle"
    write_packet_path_bundle(bundle, out)
    return out


def test_binding_happy_path(tmp_path, monkeypatch):
    bundle = _ready_bundle(tmp_path, monkeypatch)
    report = build_verified_filter_hook_binding_report(bundle)
    assert report["final_decision"] == READY_BINDING
    assert report["artifact_graph_binding_ready"] is True
    assert report["packet_view_at_hook"] == "post_dnat_forward_filter"
    assert report["verified_hook"] == "DOCKER-USER"
    assert report["verified_builtin_filter_path"] == "FORWARD"
    assert report["production_execution_available"] is False
    assert report["iptables_restore_invocation_allowed"] is False
    assert report["binding_decision_sha256"]
    changed = dict(report)
    original_sha = changed.pop("binding_decision_sha256")
    changed["packet_view_at_hook"] = "changed"
    from mpf.services.phase11_controlled_artifact_reapply_core import _canonical_sha
    assert _canonical_sha(changed) != original_sha


def test_package_evidence_happy_path_and_verify(tmp_path, monkeypatch):
    bundle = _ready_bundle(tmp_path, monkeypatch)
    package_dir = tmp_path / "package"
    report = build_package_evidence(bundle, package_dir)
    assert report["final_decision"] == READY_PACKAGE_EVIDENCE
    package = json.loads((package_dir / "package.json").read_text())
    binding = build_verified_filter_hook_binding_report(bundle)
    assert package["binding_decision_sha256"] == binding["binding_decision_sha256"]
    assert package["iptables_restore_invocation_allowed"] is False
    assert package["production_execution_available"] is False
    assert package["controlled_artifact_execute_available"] is False
    assert package["live_ready_package_available"] is False
    assert package["package_template_only"] is True
    assert package["package_evidence_kind"] == "template_only_from_verified_packet_path_binding"
    assert package["mutation_performed"] is False
    verify = verify_package_evidence(package_dir)
    assert verify["final_decision"] == READY_VERIFY
    assert verify["iptables_restore_invocation_allowed"] is False


def test_cli_smoke_for_binding_package_verify(tmp_path, monkeypatch):
    bundle = _ready_bundle(tmp_path, monkeypatch)
    runner = CliRunner()
    b = runner.invoke(app, ["production", "verified-filter-hook-binding-plan", "--packet-path-evidence-dir", str(bundle), "--output", "json"])
    assert b.exit_code == 0
    assert json.loads(b.stdout)["final_decision"] == READY_BINDING
    out = tmp_path / "cli-package"
    p = runner.invoke(app, ["production", "controlled-artifact-reapply-package-plan", "--packet-path-evidence-dir", str(bundle), "--output-dir", str(out), "--output", "json"])
    assert p.exit_code == 0
    assert json.loads(p.stdout)["final_decision"] == READY_PACKAGE_EVIDENCE
    v = runner.invoke(app, ["production", "controlled-artifact-reapply-package-verify", "--package-dir", str(out), "--output", "json"])
    assert v.exit_code == 0
    assert json.loads(v.stdout)["final_decision"] == READY_VERIFY


def test_old_input_public_port_semantics_and_wrong_hook_rejected(tmp_path, monkeypatch):
    bundle = _ready_bundle(tmp_path, monkeypatch)
    decision_path = bundle / "decision.json"
    decision = json.loads(decision_path.read_text())
    decision["verified_user_policy_hook"] = "INPUT"
    decision["verified_builtin_filter_path"] = "INPUT"
    decision["packet_view_at_verified_hook"] = "public_port_filter_input"
    decision_path.write_text(json.dumps(decision, sort_keys=True))
    report = build_verified_filter_hook_binding_report(bundle)
    assert report["final_decision"] != READY_BINDING
    assert "bundle_integrity_invalid" in report["blockers"]


def test_missing_scenario_and_accept_before_docker_user_block(tmp_path, monkeypatch):
    bundle = _ready_bundle(tmp_path, monkeypatch)
    graph_path = bundle / "packet-path-graph.json"
    graph = json.loads(graph_path.read_text())
    graph["packet_scenarios"] = graph["packet_scenarios"][:-1]
    graph_path.write_text(json.dumps(graph, sort_keys=True))
    report = build_verified_filter_hook_binding_report(bundle)
    assert report["final_decision"] != READY_BINDING
    assert "bundle_integrity_invalid" in report["blockers"]

    blocked = _ready_bundle(tmp_path / "b2", monkeypatch, require_ready=False, outputs={"iptables_save": __import__("tests.test_phase11_controlled_filter_packet_path", fromlist=["IPT_READY"]).IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", "-A FORWARD -j ACCEPT\n-A FORWARD -j DOCKER-USER\n")})
    assert build_verified_filter_hook_binding_report(blocked)["final_decision"] != READY_BINDING


def test_route_membership_scope_and_package_safety_blocks(tmp_path, monkeypatch):
    wrong_route = _ready_bundle(tmp_path / "r", monkeypatch, require_ready=False, outputs={"ip_route_get_backend_ingress": json.dumps([{"dst": "172.30.0.5", "dev": "lo"}])})
    assert build_verified_filter_hook_binding_report(wrong_route)["final_decision"] != READY_BINDING
    missing_fdb = _ready_bundle(tmp_path / "f", monkeypatch, require_ready=False, outputs={"bridge_fdb_backend": json.dumps([])})
    assert build_verified_filter_hook_binding_report(missing_fdb)["final_decision"] != READY_BINDING


def test_helper_script_does_not_contain_iptables_restore_execute_surface():
    script = Path("scripts/phase11_build_verified_controlled_artifact_package_evidence.sh").read_text()
    assert "iptables-restore" not in script
    assert "controlled-artifact-reapply-execute" not in script
    assert "sys.exit(70)" in script


def test_helper_script_exits_nonzero_on_blocked_decisions(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_mpf = fake_bin / "mpf"
    calls = tmp_path / "calls.log"
    fake_mpf.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        f"calls = pathlib.Path({str(calls)!r})\n"
        "line = ' '.join(sys.argv[1:]) + '\\n'\n"
        "calls.write_text((calls.read_text() if calls.exists() else '') + line)\n"
        "cmd = ' '.join(sys.argv[1:])\n"
        "if 'verified-filter-hook-binding-plan' in cmd:\n"
        "    print(json.dumps({'final_decision': 'BLOCKED_VERIFIED_FILTER_HOOK_BINDING'}))\n"
        "elif 'controlled-artifact-reapply-package-plan' in cmd:\n"
        "    out = pathlib.Path(sys.argv[sys.argv.index('--output-dir') + 1])\n"
        "    out.mkdir(parents=True, exist_ok=True)\n"
        "    print(json.dumps({'final_decision': 'BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_EVIDENCE', 'package_dir': str(out), 'manifest_sha256': 'm', 'package_sha256': 'p'}))\n"
        "elif 'controlled-artifact-reapply-package-verify' in cmd:\n"
        "    print(json.dumps({'final_decision': 'BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_VERIFY_EVIDENCE'}))\n"
        "else:\n"
        "    raise SystemExit(3)\n",
        encoding="utf-8",
    )
    fake_mpf.chmod(0o755)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    result = subprocess.run(
        ["scripts/phase11_build_verified_controlled_artifact_package_evidence.sh", str(evidence), str(tmp_path / "out")],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"},
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 70
    assert "blocked_decision_detected=true" in result.stderr
    assert "iptables-restore" not in calls.read_text(encoding="utf-8")
    assert "controlled-artifact-reapply-execute" not in calls.read_text(encoding="utf-8")


def test_version_docs_are_0253_after_bump():
    assert __version__ == "0.1.272"
    assert Path("VERSION").read_text().strip() == "0.1.272"
    assert 'version = "0.1.272"' in Path("pyproject.toml").read_text()
    assert "0.1.272" in Path("CHANGELOG.md").read_text()
    readme = Path("README.md").read_text()
    phase = Path("docs/PHASE_STATUS.md").read_text()
    assert "artifact_graph_binding_ready=true" in readme
    assert "controlled_artifact_reapply_package_evidence_ready=true" in phase


def _rewrite_bundle_as_source_0252(bundle: Path) -> None:
    from mpf.services.phase11_controlled_filter_packet_path_bundle_service import canonical_json_bytes, sha256_bytes
    manifested = [
        "evidence.json",
        "decision.json",
        "sanitized-backend-target.json",
        "sanitized-docker-network.json",
        "iptables-save.txt",
        "ip6tables-save.txt",
        "parsed-firewall.json",
        "host-network-topology.json",
        "packet-path-graph.json",
        "command-results.json",
    ]
    evidence_path = bundle / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["repository_version"] = "0.1.252"
    evidence["expected_version"] = "0.1.252"
    evidence_path.write_bytes(canonical_json_bytes(evidence))
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["repository_version"] = "0.1.252"
    manifest["expected_version"] = "0.1.252"
    manifest["files"] = {
        name: {"size": (bundle / name).stat().st_size, "sha256": sha256_bytes((bundle / name).read_bytes())}
        for name in manifested
    }
    manifest["decision_hash"] = manifest["files"]["decision.json"]["sha256"]
    manifest["graph_hash"] = manifest["files"]["packet-path-graph.json"]["sha256"]
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    manifest_sha = sha256_bytes(manifest_path.read_bytes())
    (bundle / "manifest.sha256").write_text(f"{manifest_sha}  manifest.json\n", encoding="utf-8")


def test_source_0252_bundle_verifies_under_0254_runtime_and_package_helpers(tmp_path, monkeypatch):
    from mpf.services.phase11_controlled_filter_packet_path_bundle_service import verify_packet_path_bundle

    bundle = _ready_bundle(tmp_path, monkeypatch)
    _rewrite_bundle_as_source_0252(bundle)

    verifier = verify_packet_path_bundle(bundle)
    assert verifier["repository_version"] == "0.1.272"
    assert verifier["source_repository_version"] == "0.1.252"
    assert verifier["bundle_integrity_valid"] is True
    assert verifier["readiness_eligible"] is True
    assert verifier["recollection_required"] is False
    assert verifier["final_decision"] == "READY_CONTROLLED_FILTER_PACKET_PATH_PROOF"
    assert verifier["manifest_sha256"]

    report = build_verified_filter_hook_binding_report(bundle)
    assert report["final_decision"] == READY_BINDING
    assert report["source_repository_version"] == "0.1.252"
    assert report["production_execution_available"] is False
    assert report["iptables_restore_invocation_allowed"] is False
    assert report["controlled_artifact_execute_available"] is False
    assert report["live_ready_package_available"] is False

    package_dir = tmp_path / "source-0252-package"
    package = build_package_evidence(bundle, package_dir)
    assert package["final_decision"] == READY_PACKAGE_EVIDENCE
    assert package["production_execution_available"] is False
    assert package["iptables_restore_invocation_allowed"] is False
    assert package["controlled_artifact_execute_available"] is False
    assert package["live_ready_package_available"] is False
    verify = verify_package_evidence(package_dir)
    assert verify["final_decision"] == READY_VERIFY
    assert verify["production_execution_available"] is False
    assert verify["iptables_restore_invocation_allowed"] is False


def test_source_0252_tamper_fails_closed_and_0251_still_recollects(tmp_path, monkeypatch):
    from mpf.services.phase11_controlled_filter_packet_path_bundle_service import verify_packet_path_bundle

    tampered = _ready_bundle(tmp_path / "tampered", monkeypatch)
    _rewrite_bundle_as_source_0252(tampered)
    decision = json.loads((tampered / "decision.json").read_text(encoding="utf-8"))
    decision["verified_user_policy_hook"] = "INPUT"
    (tampered / "decision.json").write_text(json.dumps(decision, sort_keys=True), encoding="utf-8")
    tampered_result = verify_packet_path_bundle(tampered)
    assert tampered_result["bundle_integrity_valid"] is False
    assert "file_hash_mismatch:decision.json" in tampered_result["blockers"] or "decision_hash_mismatch" in tampered_result["blockers"]
    assert build_verified_filter_hook_binding_report(tampered)["final_decision"] != READY_BINDING

    legacy = _ready_bundle(tmp_path / "legacy", monkeypatch)
    _rewrite_bundle_as_source_0252(legacy)
    from mpf.services.phase11_controlled_filter_packet_path_bundle_service import canonical_json_bytes, sha256_bytes

    evidence = json.loads((legacy / "evidence.json").read_text(encoding="utf-8"))
    evidence["packet_path_schema_version"] = "0.1.251"
    evidence["repository_version"] = "0.1.251"
    (legacy / "evidence.json").write_bytes(canonical_json_bytes(evidence))
    manifest = json.loads((legacy / "manifest.json").read_text(encoding="utf-8"))
    manifest["repository_version"] = "0.1.251"
    manifest["files"]["evidence.json"] = {"size": (legacy / "evidence.json").stat().st_size, "sha256": sha256_bytes((legacy / "evidence.json").read_bytes())}
    (legacy / "manifest.json").write_bytes(canonical_json_bytes(manifest))
    (legacy / "manifest.sha256").write_text(f"{sha256_bytes((legacy / 'manifest.json').read_bytes())}  manifest.json\n", encoding="utf-8")
    legacy_result = verify_packet_path_bundle(legacy)
    assert legacy_result["bundle_integrity_valid"] is True
    assert legacy_result["readiness_eligible"] is False
    assert legacy_result["recollection_required"] is True
    assert "legacy_packet_path_schema_recollection_required" in legacy_result["blockers"]
    assert build_verified_filter_hook_binding_report(legacy)["final_decision"] != READY_BINDING
