from pathlib import Path


def _section(text: str, heading: str, next_heading: str) -> str:
    return text.split(heading, 1)[1].split(next_heading, 1)[0]


def test_readme_current_status_is_phase11_accepted():
    text = Path("README.md").read_text()
    current = _section(text, "## Current Status", "Historical compatibility anchors")
    assert "Phase 11 — Production / Customer Activation Gate accepted on farm5" in current
    assert "Latest recorded farm5 sync evidence is 0.1.153" not in current
    assert "Actual canary execution has not been performed" not in current
    assert "Do not use this repository for production customer traffic yet" not in current


def test_readme_current_boundary_has_post_acceptance_invariants_only():
    text = Path("README.md").read_text()
    boundary = _section(text, "## Current Accepted/Working Boundary", "## Implemented So Far")
    for expected in (
        "production_traffic = controlled_cli_limited",
        "firewall_apply_allowed = controlled",
        "abuse_automation_allowed = controlled",
        "customer_onboarding_allowed = controlled_cli_limited",
        "proxy_data_plane_allowed = limited_runtime_local_only",
        "worker_enforcement_allowed = no",
        "ui_allowed = no",
        "telegram_allowed = no",
        "live_snapshot_read_allowed = iptables_save_read_only",
        "restore_lock_record_execution_allowed = controlled_boundary_only",
        "firewall.apply_mode = plan_only",
        "proxy.runtime_activation_allowed = false",
    ):
        assert expected in boundary
    for stale in (
        "production_traffic = none",
        "firewall_apply_allowed = no",
        "abuse_automation_allowed = no",
        "customer_onboarding_allowed = db_only",
    ):
        assert stale not in boundary


def test_readme_forbidden_section_allows_only_controlled_paths():
    text = Path("README.md").read_text()
    boundary = _section(text, "Forbidden now:", "Required invariants remain:")
    assert "unrestricted production traffic expansion" in boundary
    assert "customer onboarding outside the controlled CLI/service-layer path" in boundary
    assert "firewall apply, rollback, or verify outside the controlled operator-gated path" in boundary
    assert "iptables-restore execution outside the accepted controlled path" in boundary
    assert "worker enforcement before Phase 11 operational completion acceptance" in boundary
    assert "\nproduction traffic\n" not in boundary
    assert "\nlive firewall apply\n" not in boundary


def test_ai_coding_rules_marks_old_phase11_stop_condition_historical():
    text = Path("docs/AI_CODING_RULES.md").read_text()
    assert "Historical pre-final-acceptance Phase 11 planning-readiness stop condition (non-authorizing reference only):" in text
    assert "\nPhase 11 planning-readiness stop condition:" not in text


def test_agents_historical_phase6_list_does_not_override_controlled_boundary():
    text = Path("AGENTS.md").read_text()
    assert "historical Phase 6 reference only; this list does not override the accepted Phase 11 controlled boundary" in text
    assert "only controlled CLI/service-layer onboarding, planner-driven customer NAT/firewall handling" in text
    assert "Unrestricted expansion and direct or ad-hoc DB/firewall/runtime mutation remain forbidden" in text
    assert "constraints still forbidden now" not in text


def test_current_contract_docs_have_0_1_235_update():
    for file_name in ("docs/INDEX.md", "docs/PHASE_STATUS.md"):
        assert "0.1.235" in Path(file_name).read_text()
