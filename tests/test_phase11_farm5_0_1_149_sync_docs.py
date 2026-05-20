from pathlib import Path


def test_phase11_farm5_0_1_149_evidence_doc_and_gate_tokens() -> None:
    t = Path("docs/PHASE_11_FARM5_0_1_149_SYNC_TEST_EVIDENCE.md").read_text(encoding="utf-8")
    assert "0.1.149" in t
    assert "819 passed in 139.70s" in t
    assert "mpf production canary-execution-gate --output json" in t
    assert "READY_FOR_FARM5_SYNC_EVIDENCE" in t
    assert "MANUAL_CANARY_EXECUTION_GATE_NON_AUTHORIZING" in t
    assert "execution_allowed: false" in t
    assert "actual_canary_execution_performed: false" in t
    assert "production_traffic_enabled: false" in t
    assert "validation_errors: []" in t
    assert "does **not** authorize Phase 11D actual execution" in t
    assert "from `/root`" in t
    assert "planning safety gate passed" in t
    assert "firewall apply" in t and "abuse automation" in t and "UI" in t and "Telegram" in t


def test_docs_plan_and_script_alignment_for_0_1_149() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    plan = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    script = Path("scripts/verify_current_phase_gate.sh").read_text(encoding="utf-8")

    assert "Latest recorded farm5 sync evidence is 0.1.153." in readme
    assert "execution gate package is implemented on GitHub as non-authorizing and has farm5 sync/test evidence recorded" in readme

    assert "latest recorded farm5 sync evidence is 0.1.153." in plan
    assert "Phase 11D manual canary execution gate package is implemented and farm5 evidence is recorded." in plan
    assert "Phase 11D actual execution remains not accepted." in plan
    assert "Next target: one explicit operator-approved manual canary execution run on farm5 and evidence collection." in plan
    assert "Current accepted phase is Phase 10." in plan
    assert "Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in plan

    assert 'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"' in script
    assert 'REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"' in script
    assert 'cd "${REPO_ROOT}"' in script
    assert "[ -f docs/PHASE_STATUS.md ]" in script
