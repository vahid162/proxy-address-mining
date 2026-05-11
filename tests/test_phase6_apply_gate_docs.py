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

    if "mpf firewall" in text_lower and "json" in text_lower:
        assert "--output json" in text

    assert "mpf firewall evidence --json" not in text_lower
    assert "mpf firewall plan --json" not in text_lower


def test_phase_status_does_not_enable_live_apply() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "firewall_apply_allowed: no" in text
    assert "production_traffic: none" in text
    assert "abuse_automation_allowed: no" in text


def test_phase6_c0_commands_use_output_json_form() -> None:
    text = Path("docs/PHASE_6_C0_APPLY_GATE_READINESS.md").read_text(encoding="utf-8")
    assert "mpf firewall plan --output json" in text
    assert "mpf firewall evidence --output json" in text
    assert "mpf firewall plan --json" not in text
    assert "mpf firewall evidence --json" not in text


def test_phase_status_next_step_mentions_phase6_c2_not_6b() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "## Next Planned Step" in text
    assert "Phase 6-C2" in text
    assert "Phase 6-B is the next step" not in text
