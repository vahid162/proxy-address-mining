from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_roadmap_phase7_phase8_unchanged() -> None:
    t = _read("docs/ROADMAP.md")
    assert "## Phase 7 — Usage + Policy/Reject Accounting" in t
    assert "## Phase 8 — Abuse 1h Core" in t


def test_remaining_plan_marks_phase6g_h_as_substeps_and_finite_slices() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "Remaining Phase 6 Alignment With Master Roadmap" in t
    assert "Phase 6-G and Phase 6-H are safety sub-steps inside Phase 6, not new top-level roadmap phases." in t
    for s in [
        "Phase 6 Apply Slice 1 — Live Snapshot Readiness Boundary",
        "Phase 6 Apply Slice 2 — Restore Point + Lock + DB Apply Record Readiness",
        "Phase 6 Apply Slice 3 — Controlled No-Customer Apply Harness",
        "Phase 6 Apply Slice 4 — Manual Canary Apply Gate Proposal",
    ]:
        assert s in t
    assert "Phase 7 starts only after Phase 6 final acceptance." in t


def test_phase_status_current_state_unchanged() -> None:
    t = _read("docs/PHASE_STATUS.md")
    assert "current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5" in t
    assert "current_working_phase: Phase 7 — Usage + Policy/Reject Accounting" in t
    assert "production_traffic: none" in t
    assert "firewall_apply_allowed: no" in t
    assert "abuse_automation_allowed: no" in t
    assert "customer_onboarding_allowed: db_only" in t
    assert "proxy_data_plane_allowed: limited_runtime_local_only" in t
    assert "ui_allowed: no" in t
    assert "telegram_allowed: no" in t


def test_forbidden_authorizations_not_introduced() -> None:
    docs = [
        "docs/ROADMAP.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/PHASE_STATUS.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/SAFETY.md",
        "docs/ABUSE.md",
    ]
    text = "\n".join(_read(d) for d in docs).lower()
    forbidden = [
        "live firewall read is authorized now",
        "live firewall write is authorized now",
        "live apply is authorized now",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
        "real iptables adapter is allowed now",
        "db apply writes are allowed now",
        "locks are allowed now",
        "restore point writes are allowed now",
        "customer nat redirects are allowed now",
        "customer firewall rules are allowed now",
        "production traffic is allowed now",
        "usage automation is allowed now",
        "abuse automation is allowed now",
        "ui is allowed now",
        "telegram is allowed now",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_abuse_invariant_preserved() -> None:
    text = _read("docs/ABUSE.md") + "\n" + _read("docs/REMAINING_PHASE_PLAN.md")
    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "must not be weakened" in text
