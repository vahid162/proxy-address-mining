from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_remaining_phase_plan_exists():
    assert Path("docs/REMAINING_PHASE_PLAN.md").exists()


def test_docs_no_stale_current_steps():
    assert "current_phase6_step: Phase 6-B" not in _read("README.md")
    assert "current_phase6_step: Phase 6-B" not in _read("AGENTS.md")
    assert "Phase 6-C2 — Offline Apply Gate Review Report" not in _read("docs/INDEX.md")
    assert "current_phase6_step: Phase 6-B" not in _read("docs/AI_CODING_RULES.md")


def test_no_stale_phase6b_current_wording():
    stale_phrases = [
        "During current Phase 6-B",
        "Allowed in current Phase 6-B",
        "Forbidden in current Phase 6-B",
        "current Phase 6-B inspection commands",
        "Current Phase 6-B Scope",
        "Phase 6-C2 — Offline Apply Gate Review Report",
    ]
    targets = [
        "README.md",
        "AGENTS.md",
        "docs/AI_CODING_RULES.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/INDEX.md",
    ]
    for target in targets:
        text = _read(target)
        for phrase in stale_phrases:
            assert phrase not in text, f"stale phrase found in {target}: {phrase}"


def test_phase6_task_alignment():
    t = _read("docs/AI_PHASE_6_TASK.md")
    assert "Phase 6-C" in t and "accepted" in t
    assert "Phase 6-D0" in t or "Phase 6-D" in t
    assert "documentation/test-only" in t


def test_phase_status_unchanged_gate_values():
    t = _read("docs/PHASE_STATUS.md")
    assert "current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in t
    assert "current_working_phase: Phase 8 — Abuse 1h Core planning/readiness" in t
    assert "production_traffic: none" in t
    assert "firewall_apply_allowed: no" in t
    assert "abuse_automation_allowed: no" in t
    assert "customer_onboarding_allowed: db_only" in t
    assert "proxy_data_plane_allowed: limited_runtime_local_only" in t
    assert "ui_allowed: no" in t
    assert "telegram_allowed: no" in t
    assert "Live firewall apply remains forbidden" in t


def test_forbidden_behaviors_stay_forbidden():
    corpus = "\n".join(
        _read(p)
        for p in [
            "README.md",
            "AGENTS.md",
            "docs/INDEX.md",
            "docs/AI_CODING_RULES.md",
            "docs/AI_PHASE_6_TASK.md",
            "docs/REMAINING_PHASE_PLAN.md",
        ]
    )
    assert "live firewall apply" in corpus
    assert "iptables-save" in corpus
    assert "iptables-restore" in corpus
    assert "customer NAT" in corpus
    assert "customer firewall" in corpus
    assert "abuse automation" in corpus


def test_remaining_plan_abuse_invariants_and_phase6e():
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "must not be weakened" in t
    assert "normal -> over_tracking -> over_grace -> hard" in t
    assert "Phase 6-E" in t
    assert "host production firewall mutation is forbidden" in t
    assert "Phase 8" in t and "farms-over alone must not harden" in t and "worker-over alone must not harden" in t


def test_remaining_plan_finite_path_includes_execution_and_next_steps():
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "Phase 8 DB-only controlled transition execution — done and synced on farm5 in 0.1.115" in t
    assert "- GitHub main repository version before this PR is 0.1.117." in t
    assert "- Next target after this PR is Phase 8 farm5 batched sync/evidence package for 0.1.116/0.1.117/0.1.118." in t
    assert "11. Phase 8 controlled worker pre-acceptance — current target in 0.1.118" in t
    assert "Phase 8 final Abuse 1h acceptance — future" in t


def test_remaining_plan_finite_path_numbering_and_order():
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    finite = t.split("## Finite Remaining Path", 1)[1].split("## Historical/Compatibility Notes", 1)[0]
    assert finite.count("9. Phase 8 runtime/worker integration readiness") == 1
    assert finite.count("10. Phase 8 runtime worker dry-run harness") == 1
    assert finite.count("11. ") == 1
    assert finite.count("12. ") == 1
    assert finite.count("13. ") == 1
    assert finite.count("14. ") == 1
    assert finite.count("Phase 8 final Abuse 1h acceptance — future") == 1
    assert finite.index("11. Phase 8 controlled worker pre-acceptance — current target in 0.1.118") < finite.index("12. Phase 8 farm5 batched sync/evidence — next")
