from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_e2_doc_exists_and_core_statements():
    path = Path("docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md")
    assert path.exists()
    t = _read(str(path)).lower()
    for s in [
        "isolated/non-production only",
        "evidence package / boundary planning only",
        "does not authorize host production firewall mutation",
        "does not authorize live firewall read/write",
        "does not authorize `iptables-save` or `iptables-restore`",
        "does not authorize real iptables adapters",
        "does not authorize live apply/rollback/verify",
        "does not authorize db apply writes",
        "does not authorize lock acquisition",
        "does not authorize restore point writes",
        "does not authorize customer nat redirects or customer firewall rules",
    ]:
        assert s in t


def test_e2_doc_preserves_abuse_invariant():
    t = _read("docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md").lower()
    for s in [
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
        "farms-over alone must not harden",
        "worker-over alone must not harden",
        "all active customers in enabled lanes must be covered",
        "no silent skip is allowed",
    ]:
        assert s in t


def test_phase_status_stays_non_accepting_for_e3():
    t = _read("docs/PHASE_STATUS.md")
    assert "current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5" in t
    assert "current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness" in t
    assert "Phase 6-G is accepted as controlled live apply gate planning / pre-apply review only, documentation/test-only and non-authorizing" in t
    assert "Phase 6-E2 accepted" not in t


def test_index_includes_e2_in_required_sections():
    t = _read("docs/INDEX.md")

    start_here = t.split("## Start Here", 1)[1].split("## Core Contracts", 1)[0]
    current_phase = t.split("## Current Phase Contracts", 1)[1].split("## Reading Order by Task", 1)[0]
    doc_summary = t.split("## Documentation Summary", 1)[1].split("## Current Roadmap Snapshot", 1)[0]

    needle = "docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md"
    assert needle in start_here
    assert needle in current_phase
    assert needle in doc_summary


def test_no_e2_authorization_anywhere():
    docs = [
        "docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md",
        "docs/PHASE_STATUS.md",
        "docs/INDEX.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/REMAINING_PHASE_PLAN.md",
    ]
    combined = "\n".join(_read(p).lower() for p in docs)
    banned = [
        "phase 6-e2 authorizes live apply",
        "phase 6-e2 authorizes iptables-save",
        "phase 6-e2 authorizes iptables-restore",
        "phase 6-e2 authorizes a real iptables adapter",
        "phase 6-e2 authorizes db apply writes",
        "phase 6-e2 authorizes locks",
        "phase 6-e2 authorizes restore point writes",
    ]
    for b in banned:
        assert b not in combined
