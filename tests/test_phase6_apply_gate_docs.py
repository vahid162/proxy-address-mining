from pathlib import Path


def test_phase6_c0_doc_exists_and_has_required_markers() -> None:
    path = Path("docs/PHASE_6_C0_APPLY_GATE_READINESS.md")
    assert path.exists()
    text = path.read_text(encoding="utf-8")

    required = [
        "Phase 6-C0",
        "does not authorize live apply",
        "firewall_apply_allowed: no",
        "production_traffic: none",
        "abuse_automation_allowed: no",
        "iptables-save execution remains forbidden",
        "iptables-restore execution remains forbidden",
        "mpf firewall apply remains forbidden",
        "mpf firewall rollback remains forbidden",
        "mpf firewall verify remains forbidden",
        "backend direct external exposure remains NO",
        "internal backend reachability remains OK",
        "manual canary",
        "rollback readiness",
        "stop conditions",
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
    ]
    text_lower = text.lower()
    for marker in required:
        assert marker.lower() in text_lower


def test_phase6_c1_doc_exists_and_has_required_markers() -> None:
    path = Path("docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    text_lower = text.lower()

    required = [
        "Phase 6-C1",
        "does not authorize live apply",
        "firewall_apply_allowed: no",
        "production_traffic: none",
        "abuse_automation_allowed: no",
        "mpf firewall apply remains forbidden",
        "mpf firewall rollback remains forbidden",
        "mpf firewall verify remains forbidden",
        "iptables-save execution remains forbidden",
        "iptables-restore execution remains forbidden",
        "backend direct external exposure",
        "internal backend reachability",
        "risk matrix",
        "operator approval checklist",
        "rollback readiness",
        "canary readiness",
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
        "BLOCKED",
        "READY_FOR_FUTURE_GATE_REVIEW",
        "REJECTED_NEEDS_REWORK",
    ]
    for marker in required:
        assert marker.lower() in text_lower


def test_phase6_c_acceptance_doc_exists_and_has_required_markers() -> None:
    path = Path("docs/PHASE_6_C_ACCEPTANCE_EVIDENCE.md")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    text_lower = text.lower()

    required = [
        "Phase 6-C",
        "offline apply-gate readiness/review only",
        "does not authorize live apply",
        "firewall_apply_allowed: no",
        "production_traffic: none",
        "abuse_automation_allowed: no",
        "final_decision remains BLOCKED",
        "mpf firewall apply remains forbidden",
        "mpf firewall rollback remains forbidden",
        "mpf firewall verify remains forbidden",
        "iptables-save execution remains forbidden",
        "iptables-restore execution remains forbidden",
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
    ]
    for marker in required:
        assert marker.lower() in text_lower


def test_phase_status_does_not_enable_live_apply() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "firewall_apply_allowed: no" in text
    assert "production_traffic: none" in text
    assert "abuse_automation_allowed: no" in text


def test_phase_status_next_step_mentions_phase6_d0_and_not_authorize_live_apply() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    tl = text.lower()
    assert "## Next Planned Step" in text
    assert "Phase 6-D0" in text
    assert "does not authorize live apply" in tl or "live apply remains forbidden" in tl


def test_no_stale_json_short_flag_examples_introduced() -> None:
    docs = [
        "docs/PHASE_6_C_ACCEPTANCE_EVIDENCE.md",
        "docs/PHASE_STATUS.md",
        "docs/FIREWALL.md",
    ]
    for path in docs:
        text = Path(path).read_text(encoding="utf-8").lower()
        assert "mpf firewall evidence --json" not in text
        assert "mpf firewall gate-review --json" not in text


def test_phase6_c0_commands_use_output_json_form() -> None:
    text = Path("docs/PHASE_6_C0_APPLY_GATE_READINESS.md").read_text(encoding="utf-8")
    assert "mpf firewall plan --output json" in text
    assert "mpf firewall evidence --output json" in text
    assert "mpf firewall plan --json" not in text.lower()
    assert "mpf firewall evidence --json" not in text.lower()


def test_phase6_docs_no_stale_short_json_flags() -> None:
    docs = [
        "docs/PHASE_6_C0_APPLY_GATE_READINESS.md",
        "docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md",
        "docs/PHASE_6_C_ACCEPTANCE_EVIDENCE.md",
        "docs/PHASE_STATUS.md",
        "docs/FIREWALL.md",
        "docs/INDEX.md",
        "docs/AI_PHASE_6_TASK.md",
        "README.md",
        "AGENTS.md",
        "docs/AI_CODING_RULES.md",
    ]
    stale = [
        "mpf firewall plan --json",
        "mpf firewall diff --json",
        "mpf firewall doctor --json",
        "mpf firewall apply-contract --json",
        "mpf firewall package --json",
        "mpf firewall preflight --json",
        "mpf firewall evidence --json",
        "mpf firewall gate-review --json",
    ]
    for path in docs:
        data = Path(path).read_text(encoding="utf-8").lower()
        for marker in stale:
            assert marker not in data


def test_gate_review_json_examples_use_output_json_if_present() -> None:
    docs = [
        "docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/PHASE_STATUS.md",
    ]
    for path in docs:
        data = Path(path).read_text(encoding="utf-8")
        dl = data.lower()
        if "mpf firewall gate-review" in dl:
            assert "mpf firewall gate-review --json" not in dl
            if "--output json" in dl:
                assert "mpf firewall gate-review --output json" in data
