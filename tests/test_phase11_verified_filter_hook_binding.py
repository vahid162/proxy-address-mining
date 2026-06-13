from __future__ import annotations

import json
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


def test_package_evidence_happy_path_and_verify(tmp_path, monkeypatch):
    bundle = _ready_bundle(tmp_path, monkeypatch)
    package_dir = tmp_path / "package"
    report = build_package_evidence(bundle, package_dir)
    assert report["final_decision"] == READY_PACKAGE_EVIDENCE
    package = json.loads((package_dir / "package.json").read_text())
    assert package["iptables_restore_invocation_allowed"] is False
    assert package["production_execution_available"] is False
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


def test_version_docs_are_0253_after_bump():
    assert __version__ == "0.1.253"
    assert Path("VERSION").read_text().strip() == "0.1.253"
    assert 'version = "0.1.253"' in Path("pyproject.toml").read_text()
    assert "0.1.253" in Path("CHANGELOG.md").read_text()
    readme = Path("README.md").read_text()
    phase = Path("docs/PHASE_STATUS.md").read_text()
    assert "artifact_graph_binding_ready=true" in readme
    assert "controlled_artifact_reapply_package_evidence_ready=true" in phase
