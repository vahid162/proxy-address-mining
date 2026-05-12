from pathlib import Path


def test_remaining_phase_plan_exists():
    assert Path("docs/REMAINING_PHASE_PLAN.md").exists()


def _read(p):
    return Path(p).read_text(encoding="utf-8")


def test_docs_no_stale_current_steps():
    assert "current_phase6_step: Phase 6-B" not in _read("README.md")
    assert "current_phase6_step: Phase 6-B" not in _read("AGENTS.md")
    assert "Phase 6-C2 — Offline Apply Gate Review Report" not in _read("docs/INDEX.md")
    assert "current_phase6_step: Phase 6-B" not in _read("docs/AI_CODING_RULES.md")


def test_phase6_task_alignment():
    t = _read("docs/AI_PHASE_6_TASK.md")
    assert "Phase 6-C" in t and "accepted" in t
    assert "Phase 6-D0" in t or "Phase 6-D" in t
    assert "documentation/test-only" in t


def test_phase_status_unchanged_gate_values():
    t = _read("docs/PHASE_STATUS.md")
    assert "production_traffic: none" in t
    assert "firewall_apply_allowed: no" in t
    assert "abuse_automation_allowed: no" in t


def test_forbidden_behaviors_stay_forbidden():
    corpus = "\n".join(_read(p) for p in ["README.md", "AGENTS.md", "docs/INDEX.md", "docs/AI_CODING_RULES.md", "docs/AI_PHASE_6_TASK.md", "docs/REMAINING_PHASE_PLAN.md"])
    assert "live firewall apply" in corpus
    assert "iptables-save" in corpus
    assert "iptables-restore" in corpus
    assert "customer NAT" in corpus
    assert "customer firewall" in corpus


def test_remaining_plan_abuse_invariants_and_phase6e():
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "must not be weakened" in t
    assert "normal -> over_tracking -> over_grace -> hard" in t
    assert "Phase 6-E" in t
    assert "host production firewall mutation is forbidden" in t
    assert "Phase 8" in t and "farms-over alone must not harden" in t and "worker-over alone must not harden" in t
