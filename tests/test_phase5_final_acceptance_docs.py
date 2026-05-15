from pathlib import Path


def test_phase5_final_acceptance_doc_exists_and_contains_required_evidence() -> None:
    doc_path = Path("docs/PHASE_5_FINAL_ACCEPTANCE.md")
    assert doc_path.exists()

    text = doc_path.read_text(encoding="utf-8")

    required_fragments = [
        "Phase 5 Final Acceptance",
        "accepted on farm5",
        "0.1.21",
        "0.1.22",
        "174 passed",
        "0002_phase5_customer_lifecycle",
        "no customer NAT redirects",
        "no MPF/customer firewall refs",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "ui_allowed: no",
        "telegram_allowed: no",
        "limited local-only",
        "Phase 6",
        "Firewall Planner",
    ]

    for fragment in required_fragments:
        assert fragment in text


def test_phase_status_reflects_phase5_acceptance_and_phase6_working_gate() -> None:
    status_text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")

    assert "current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in status_text
    assert "current_working_phase: Phase 8 — Abuse 1h Core planning/readiness" in status_text

    for gate in [
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "ui_allowed: no",
        "telegram_allowed: no",
    ]:
        assert gate in status_text


def test_runtime_artifacts_remain_forbidden_in_phase_docs() -> None:
    combined = "\n".join(
        [
            Path("docs/PHASE_5_FINAL_ACCEPTANCE.md").read_text(encoding="utf-8"),
            Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8"),
        ]
    )

    required_forbidden_assertions = [
        "no customer NAT redirects",
        "no customer firewall rules",
        "no production customer traffic",
        "abuse automation",
        "live firewall apply",
    ]

    for fragment in required_forbidden_assertions:
        assert fragment in combined
