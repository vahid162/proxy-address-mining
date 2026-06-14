from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from mpf import __version__
from mpf.services.phase11_verified_filter_hook_binding_service import (
    READY_BINDING,
    READY_PACKAGE_EVIDENCE,
    build_package_evidence,
    build_verified_filter_hook_binding_report,
)
from tests.test_phase11_controlled_filter_packet_path_bundle import _ready_bundle


def test_version_docs_are_0253_after_bump():
    assert __version__ == "0.1.262"
    assert Path("VERSION").read_text().strip() == "0.1.262"
    assert 'version = "0.1.262"' in Path("pyproject.toml").read_text()
    assert "0.1.262" in Path("CHANGELOG.md").read_text()
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
    assert verifier["repository_version"] == "0.1.262"
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
