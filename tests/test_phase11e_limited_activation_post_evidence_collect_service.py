import json
from pathlib import Path
from types import SimpleNamespace

from mpf import __version__
from mpf.services import phase11e_limited_activation_post_evidence_collect_service as service
from tests.test_phase11e_limited_activation_execute_service import _j, _rows, _sha


def _kwargs(tmp_path: Path, source_evidence: object | None = None) -> dict[str, object]:
    scope = {
        "candidate_customer_key": "limited-btc-001",
        "lane": "btc",
        "public_port": 20101,
        "backend_target": "172.18.0.3:60010",
    }
    execution = _j(tmp_path / "execution.json", {"final_decision": "PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE", **scope})
    artifact = _j(tmp_path / "artifact.json", {
        "final_decision": "PASS_NO_CUSTOMER_ARTIFACTS",
        "unknown_mpf_artifacts": [],
        "forbidden_public_runtime_exposure": False,
        "production_gates_remain_closed": True,
    })
    source = _j(tmp_path / "source.json", source_evidence or {"db_ok": True, "proxy_ok": True, "changed_customers": ["limited-btc-001"]})
    kwargs: dict[str, object] = {
        "expected_version": __version__,
        "activation_execution_json": str(execution),
        "activation_execution_json_sha256": _sha(execution),
        "artifact_gate_json": str(artifact),
        "artifact_gate_json_sha256": _sha(artifact),
        "source_evidence_json": str(source),
        "source_evidence_json_sha256": _sha(source),
        "operator": "operator",
        "reason": "collect read-only post-evidence",
    }
    kwargs.update({confirmation: True for confirmation in service.CONFIRMATIONS})
    return kwargs


def _collect(monkeypatch, tmp_path: Path, source_evidence: object | None = None) -> dict[str, object]:
    monkeypatch.setattr(service.customer_read_service, "list_customer_status", lambda *args, **kwargs: _rows("active"))
    return service.build_phase11e_limited_activation_post_evidence_collect_report(SimpleNamespace(), **_kwargs(tmp_path, source_evidence))


def _assert_ready_and_read_only(report: dict[str, object]) -> None:
    assert report["final_decision"] == "PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY"
    assert report["db_ok"] is True
    assert report["proxy_ok"] is True
    for field in (
        "mutation_performed",
        "db_mutation_performed",
        "firewall_apply_performed",
        "conntrack_flush_performed",
        "docker_restart_performed",
        "systemd_restart_performed",
    ):
        assert report[field] is False


def test_post_evidence_ready_with_legacy_top_level_source_evidence(monkeypatch, tmp_path: Path) -> None:
    _assert_ready_and_read_only(_collect(monkeypatch, tmp_path, {"db_ok": True, "proxy_ok": True}))


def test_post_evidence_ready_with_real_source_bundle_shape(monkeypatch, tmp_path: Path) -> None:
    source = {
        "db_status": {"ok": True, "status": "OK"},
        "proxy_doctor": {"ok": True, "final_verdict": "OK"},
    }
    _assert_ready_and_read_only(_collect(monkeypatch, tmp_path, source))


def test_post_evidence_blocks_when_db_status_is_not_ok(monkeypatch, tmp_path: Path) -> None:
    source = {"db_status": {"ok": False, "status": "ERROR"}, "proxy_doctor": {"ok": True, "final_verdict": "OK"}}
    assert _collect(monkeypatch, tmp_path, source)["final_decision"] == "BLOCKED"


def test_post_evidence_blocks_when_proxy_doctor_is_not_ok(monkeypatch, tmp_path: Path) -> None:
    source = {"db_status": {"ok": True, "status": "OK"}, "proxy_doctor": {"ok": False, "final_verdict": "ERROR"}}
    assert _collect(monkeypatch, tmp_path, source)["final_decision"] == "BLOCKED"


def test_post_evidence_blocks_source_evidence_hash_mismatch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(service.customer_read_service, "list_customer_status", lambda *args, **kwargs: _rows("active"))
    kwargs = _kwargs(tmp_path)
    kwargs["source_evidence_json_sha256"] = "0" * 64
    report = service.build_phase11e_limited_activation_post_evidence_collect_report(SimpleNamespace(), **kwargs)
    assert report["final_decision"] == "BLOCKED"
    assert "source_evidence_json_hash_mismatch" in report["blockers"]


def test_post_evidence_blocks_malformed_source_evidence(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(service.customer_read_service, "list_customer_status", lambda *args, **kwargs: _rows("active"))
    kwargs = _kwargs(tmp_path)
    source_path = Path(str(kwargs["source_evidence_json"]))
    source_path.write_text("not-json", encoding="utf-8")
    kwargs["source_evidence_json_sha256"] = _sha(source_path)
    report = service.build_phase11e_limited_activation_post_evidence_collect_report(SimpleNamespace(), **kwargs)
    assert report["final_decision"] == "BLOCKED"
    assert "source_evidence_json_invalid" in report["blockers"]


def test_post_evidence_blocks_unknown_exposure_and_customer_states(monkeypatch, tmp_path: Path) -> None:
    for rows, artifact_edit in [
        (_rows("paused"), None),
        (_rows("active", "paused"), None),
        (_rows("active"), {"unknown_mpf_artifacts": ["unexpected"]}),
        (_rows("active"), {"forbidden_public_runtime_exposure": True}),
    ]:
        monkeypatch.setattr(service.customer_read_service, "list_customer_status", lambda *args, _rows=rows, **kwargs: _rows)
        kwargs = _kwargs(tmp_path)
        if artifact_edit:
            artifact_path = Path(str(kwargs["artifact_gate_json"]))
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            artifact.update(artifact_edit)
            _j(artifact_path, artifact)
            kwargs["artifact_gate_json_sha256"] = _sha(artifact_path)
        assert service.build_phase11e_limited_activation_post_evidence_collect_report(SimpleNamespace(), **kwargs)["final_decision"] == "BLOCKED"
