from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.abuse_worker_integration_readiness import (
    build_abuse_worker_failure_modes,
    build_abuse_worker_loop_contract,
    build_abuse_worker_readiness_contract,
)
from mpf.interfaces.cli import app
from mpf.services.phase8_runtime_worker_integration_readiness_service import (
    build_phase8_runtime_worker_integration_readiness_report,
)


def cfg_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_worker_domain_contracts_disabled_by_default() -> None:
    w = build_abuse_worker_readiness_contract()
    loop = build_abuse_worker_loop_contract()
    fails = {f.failure: f for f in build_abuse_worker_failure_modes()}
    assert w.enabled_by_default is False and w.scheduler_enabled_by_default is False
    assert w.runtime_execution_allowed is False and w.real_customer_evaluation_allowed is False
    assert w.production_db_execution_allowed is False
    assert w.firewall_mutation_allowed is False and w.customer_mutation_allowed is False
    assert loop.default_mode in {"report_only", "dry_run"}
    assert fails["missing_evidence"].harden_allowed is False
    assert fails["stale_evidence"].harden_allowed is False
    assert fails["db_failure"].harden_allowed is False
    assert fails["firewall_failure"].harden_allowed is False
    assert "explicit_skip" in fails["lock_contention"].action


def test_runtime_worker_readiness_service_and_cli() -> None:
    r = build_phase8_runtime_worker_integration_readiness_report(load_config(cfg_path()))
    assert r["component"] == "phase8_runtime_worker_integration_readiness"
    assert r["final_decision"] == "BLOCKED"
    assert r["execution_allowed"] is False and r["phase8_acceptance_allowed"] is False
    assert r["farm5_0_1_115_sync_evidence_present"] is True
    assert r["no_farm5_0_1_116_sync_evidence_claimed"] is True
    assert r["db_transition_readiness_present"] is True
    assert r["worker_readiness_contract_defined"] is True
    assert r["worker_loop_contract_defined"] is True
    assert r["worker_failure_modes_defined"] is True
    assert r["worker_synthetic_scenarios_passed"] is True
    assert r["runtime_worker_authorized"] is False and r["scheduler_authorized"] is False
    assert r["abuse_runner_authorized"] is False and r["production_db_execution_authorized"] is False
    assert r["db_reads_authorized"] is False and r["db_writes_authorized"] is False
    assert r["firewall_apply_authorized"] is False and r["production_traffic_authorized"] is False
    assert r["hard_block_authorized"] is False and r["pause_automation_authorized"] is False
    assert r["blockers"] == []

    out = CliRunner().invoke(app, ["phase8", "runtime-worker-readiness", "--config", str(cfg_path()), "--output", "json"])
    assert out.exit_code == 0
    data = json.loads(out.stdout)
    assert data["final_decision"] == "BLOCKED"
    assert data["execution_allowed"] is False
    assert data["runtime_worker_authorized"] is False
    assert data["scheduler_authorized"] is False
    assert data["abuse_runner_authorized"] is False
    assert data["production_db_execution_authorized"] is False
    assert data["firewall_apply_authorized"] is False
    assert data["blockers"] == []


def test_fail_closed_for_missing_115_or_fabricated_116(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs/history").mkdir(parents=True)
    (repo / "README.md").write_text("runtime/worker integration readiness package", encoding="utf-8")
    (repo / "docs/INDEX.md").write_text("runtime/worker integration readiness", encoding="utf-8")
    (repo / "docs/AI_CODING_RULES.md").write_text("Phase 8 runtime/worker readiness stop condition", encoding="utf-8")
    (repo / "docs/AI_PHASE_8_TASK.md").write_text("Runtime/Worker Integration Readiness", encoding="utf-8")
    (repo / "docs/REMAINING_PHASE_PLAN.md").write_text("Current target is Phase 8 runtime/worker integration readiness package.", encoding="utf-8")
    (repo / "docs/history/PHASE_STATUS_LEGACY_0.1.302.md").write_text("current_accepted_phase: Phase 7\ncurrent_working_phase: Phase 8\nsynced to 0.1.116\n", encoding="utf-8")
    r = build_phase8_runtime_worker_integration_readiness_report(load_config(cfg_path()), repo_root=repo)
    assert "farm5_0_1_115_sync_evidence_present_missing_or_failed" in r["blockers"]
    assert "no_farm5_0_1_116_sync_evidence_claimed_missing_or_failed" in r["blockers"]


def test_static_safety_new_files() -> None:
    banned = ["subprocess.run", "subprocess.popen", "os.system", "iptables-save", "iptables-restore", " conntrack ", " docker ", " systemctl ", "psycopg.connect", "create_engine", "session.add", "session.commit", "write_text", 'open(']
    for fp in ["mpf/domain/abuse_worker_integration_readiness.py", "mpf/services/phase8_runtime_worker_integration_readiness_service.py"]:
        txt = Path(fp).read_text(encoding="utf-8").lower()
        for b in banned:
            assert b not in txt
