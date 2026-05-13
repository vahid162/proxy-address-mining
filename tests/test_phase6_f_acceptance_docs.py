from pathlib import Path


def test_phase6_f_acceptance_doc_exists():
    assert Path("docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md").exists()


def test_phase_status_current_state_unchanged():
    text = Path("docs/PHASE_STATUS.md").read_text()
    expected = """## Current State

```text
current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
```"""
    assert expected in text


def test_phase6_f_block_in_accepted_results_before_warning():
    text = Path("docs/PHASE_STATUS.md").read_text()
    accepted = text.index("## Accepted Server Results")
    warning = text.index("## Current Server Warning")
    block = text[accepted:warning]
    assert "### Phase 6-F — Manual Canary Gate Definition" in block
    assert "version accepted on farm5: 0.1.73" in block


def test_phase_status_next_step_and_no_authorization_tokens():
    text = Path("docs/PHASE_STATUS.md").read_text().lower()
    assert "phase 6-g — controlled live apply gate planning / pre-apply review" in text
    assert "documentation/test-only and non-authorizing" in text
    forbidden = [
        "live apply is authorized",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
        "real iptables adapter is allowed now",
        "db apply writes are allowed now",
        "locks are allowed now",
        "restore point writes are allowed now",
        "customer nat redirects are allowed now",
        "customer firewall rules are allowed now",
    ]
    for token in forbidden:
        assert token not in text


def test_no_doc_authorizes_live_actions_now():
    docs = [
        "docs/PHASE_STATUS.md",
        "docs/INDEX.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/ROADMAP.md",
        "docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md",
    ]
    text = "\n".join(Path(p).read_text().lower() for p in docs)
    for token in [
        "live apply is authorized now",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
        "real iptables adapter is allowed now",
        "db apply writes are allowed now",
        "locks are allowed now",
        "restore point writes are allowed now",
        "customer nat redirects are allowed now",
        "customer firewall rules are allowed now",
    ]:
        assert token not in text


def test_index_contains_phase6_f_acceptance_in_required_sections():
    idx = Path("docs/INDEX.md").read_text()
    assert "docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md" in idx


def test_abuse_invariant_preserved_in_f_acceptance_doc():
    text = Path("docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md").read_text()
    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "sustained miner-abuse hardens after about 3600 seconds" in text
    assert "farms-over alone must not harden" in text
    assert "worker-over alone must not harden" in text
    assert "all active customers in enabled lanes must be covered" in text
    assert "no silent skip is allowed" in text


def test_index_phase6_f_acceptance_location_and_wording():
    idx = Path("docs/INDEX.md").read_text()

    start_here = idx[idx.index("## Start Here"):idx.index("## Core Contracts")]
    assert "docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md" in start_here

    current = idx[idx.index("## Current Phase Contracts"):idx.index("## Reading Order by Task")]
    assert "Phase 6-G accepted as controlled live apply gate planning / pre-apply review only, documentation/test-only and non-authorizing." in current
    assert "Phase 6-E3 accepted (isolated/non-production evidence review / non-authorizing gate checklist)" not in current

    read_block = current[current.index("Read:"): ]
    f_doc = "docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md"
    f_acc = "docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md"
    assert f_doc in read_block and f_acc in read_block
    assert read_block.index(f_acc) > read_block.index(f_doc)

    assert "### `docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md`" in idx


def test_remaining_phase_plan_no_longer_points_to_phase6f_as_next_step():
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text()
    assert "The next planned implementation step is Phase 6-F" not in text
    assert "Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review" in text
