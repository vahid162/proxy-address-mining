from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.abuse_transition_plan import build_db_mutation_plan, build_operator_approval_contract, build_transition_intent_from_dry_run_result
from mpf.interfaces.cli import app
from mpf.services.phase8_db_transition_readiness_service import build_phase8_db_transition_readiness_report


def cfg_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_domain_transition_plan_contracts() -> None:
    class R:
        current_state = "normal"; proposed_state = "over_tracking"; decision = "would_enter_over_tracking"
        would_transition = True; would_harden = False; transition_allowed = False; hardening_allowed = False
        dry_run = True; evidence_status = "complete"; sustained_over_seconds = 0; threshold_seconds = 3600; grace_seconds = 900
        reason = "dry_run_only"; blockers = []; warnings = []
    i1 = build_transition_intent_from_dry_run_result(customer_id=1, lane_id=1, customer_key="c1", port=1, evidence_source="synthetic", observed_at_iso="2026-01-01T00:00:00", dry_run_result=R())
    p1 = build_db_mutation_plan(i1)
    p2 = build_db_mutation_plan(i1)
    assert p1.idempotency_key == p2.idempotency_key
    assert p1.writes_allowed is False and p1.execution_allowed is False
    assert p1.future_write_tables == ["abuse_states", "abuse_events"]
    assert p1.audit_payload["current_state"] == "normal"

    r2 = R(); r2.proposed_state = "normal"; r2.decision = "stays_normal"; r2.would_transition = False; r2.evidence_status = "complete"
    p3 = build_db_mutation_plan(build_transition_intent_from_dry_run_result(customer_id=1, lane_id=1, customer_key="c1", port=1, evidence_source="synthetic", observed_at_iso="2026-01-01T00:00:00", dry_run_result=r2))
    assert p3.future_write_tables == [] and "no_state_change" in p3.blocked_reason

    approval = build_operator_approval_contract()
    assert approval.required is True
    assert approval.approval_allowed_in_this_pr is False and approval.execution_allowed_in_this_pr is False


def test_phase8_db_transition_readiness_service_cli_and_docs() -> None:
    cfg = load_config(cfg_path())
    r = build_phase8_db_transition_readiness_report(cfg)
    assert r["component"] == "phase8_db_transition_readiness"
    assert r["final_decision"] == "BLOCKED"
    assert r["execution_allowed"] is False and r["db_reads_authorized"] is False and r["db_writes_authorized"] is False
    assert r["synthetic_transition_plan_scenarios_passed"] is True
    assert r["blockers"] == []

    runner = CliRunner()
    out = runner.invoke(app, ["phase8", "db-transition-readiness", "--config", str(cfg_path())])
    assert out.exit_code == 0
    js = runner.invoke(app, ["phase8", "db-transition-readiness", "--config", str(cfg_path()), "--output", "json"])
    payload = json.loads(js.stdout)
    assert payload["final_decision"] == "BLOCKED"

    phase_status = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "current_accepted_phase: Phase 7" in phase_status
    assert "current_working_phase: Phase 8" in phase_status
    assert "Phase 8 DB-Only Controlled Transition Readiness Boundary" in phase_status
    assert "synced to 0.1.110" in phase_status
    assert "synced to 0.1.114" not in phase_status
