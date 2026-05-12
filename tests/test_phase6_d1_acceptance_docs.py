from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_phase6_d1_acceptance_evidence_exists_and_contains_required_lines() -> None:
    text = _read("docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md")
    required = [
        "Version accepted: 0.1.59",
        "pytest with venv: 357 passed",
        "verify_current_phase_gate.sh: passed",
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "no customer NAT redirects",
        "no customer firewall rules",
        "no MPF/customer firewall refs",
        "no live firewall read",
        "no live firewall write",
        "no live firewall apply",
        "no iptables-save execution",
        "no iptables-restore execution",
        "no lock acquisition",
        "no restore point write",
        "no DB apply write",
    ]
    for item in required:
        assert item in text


def test_phase_status_current_state_unchanged_and_phase6_d1_doce0_present() -> None:
    text = _read("docs/PHASE_STATUS.md")
    current_state_required = [
        "current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5",
        "current_working_phase: Phase 6 — Firewall Planner",
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "customer_onboarding_allowed: db_only",
        "proxy_data_plane_allowed: limited_runtime_local_only",
        "ui_allowed: no",
        "telegram_allowed: no",
    ]
    for item in current_state_required:
        assert item in text

    for item in [
        "Phase 6-D1 — Live-Apply Boundary Contract",
        "Phase 6-E0",
        "isolated/non-production",
        "Live apply remains forbidden",
    ]:
        assert item in text


def test_index_remaining_plan_and_non_authorization_constraints() -> None:
    index_text = _read("docs/INDEX.md")
    remaining_text = _read("docs/REMAINING_PHASE_PLAN.md")
    acceptance_text = _read("docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md")
    ai_phase6_text = _read("docs/AI_PHASE_6_TASK.md")
    firewall_text = _read("docs/FIREWALL.md")

    assert "docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md" in index_text
    assert "must not mutate the host production firewall" in remaining_text

    for item in [
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
        "farms-over alone must not harden",
        "worker-over alone must not harden",
        "all active customers in enabled lanes must be covered",
        "no silent skip",
    ]:
        assert item in acceptance_text

    combined = "\n".join([index_text, remaining_text, acceptance_text, ai_phase6_text, firewall_text])
    assert "Phase 6-E0 authorizes live apply" not in combined
    assert "Phase 6-E0 authorizes host production firewall mutation" not in combined
    assert "iptables-save is allowed now" not in combined
    assert "iptables-restore is allowed now" not in combined
