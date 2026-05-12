from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_phase6_g_doc_exists() -> None:
    assert Path("docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md").exists()


def test_phase_status_current_state_block_unchanged() -> None:
    text = _read("docs/PHASE_STATUS.md")
    expected = """## Current State\n\n```text\ncurrent_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5\ncurrent_working_phase: Phase 6 — Firewall Planner\nserver_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\nproxy_data_plane_allowed: limited_runtime_local_only\nui_allowed: no\ntelegram_allowed: no\n```"""
    assert expected in text


def test_phase_status_phase6g_planned_not_accepted_and_non_authorizing() -> None:
    text = _read("docs/PHASE_STATUS.md")
    assert "Phase 6-F is accepted as manual canary gate definition only" in text
    assert "The next planned implementation step is Phase 6-G" in text
    assert "docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md" in text
    assert "Phase 6-G accepted" not in text
    assert "Phase 6-G does not authorize host production firewall mutation" in text


def test_index_lists_phase6g_in_required_sections() -> None:
    text = _read("docs/INDEX.md")
    assert "19. `docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md`" in text
    assert "Current Phase Contracts add-on: `docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md`" in text
    assert "### `docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md`" in text
    assert "Phase 6-G is planned, not accepted" in text


def test_no_doc_authorizes_live_apply_now() -> None:
    docs = [
        "docs/PHASE_STATUS.md",
        "docs/INDEX.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/ROADMAP.md",
        "docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md",
    ]
    combined = "\n".join(_read(p) for p in docs)
    forbidden = [
        "live apply is authorized now",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
        "real iptables adapter is allowed now",
        "DB apply writes are allowed now",
        "locks are allowed now",
        "restore point writes are allowed now",
        "customer NAT redirects are allowed now",
        "customer firewall rules are allowed now",
    ]
    for phrase in forbidden:
        assert phrase not in combined


def test_no_stale_phase6f_next_planned_wording() -> None:
    docs = ["README.md", "docs/INDEX.md", "docs/AI_PHASE_6_TASK.md", "docs/REMAINING_PHASE_PLAN.md", "docs/ROADMAP.md"]
    combined = "\n".join(_read(p) for p in docs)
    assert "next planned step is Phase 6-F" not in _read("README.md") + _read("docs/AI_PHASE_6_TASK.md") + _read("docs/REMAINING_PHASE_PLAN.md") + _read("docs/ROADMAP.md")


def test_abuse_invariant_preserved() -> None:
    text = _read("docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md") + "\n" + _read("docs/ABUSE.md")
    for phrase in [
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
        "farms-over alone must not harden",
        "worker-over alone must not harden",
        "all active customers in enabled lanes must be covered",
        "no silent skip is allowed",
    ]:
        assert phrase in text
