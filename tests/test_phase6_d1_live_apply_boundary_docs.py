from pathlib import Path


def test_phase6_d1_doc_exists() -> None:
    assert Path("docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md").exists()


def test_phase6_d1_required_content() -> None:
    text = Path("docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md").read_text(encoding="utf-8").lower()
    required = [
        "documentation/test-only",
        "does not authorize live apply",
        "live firewall reads remain forbidden now",
        "live firewall writes remain forbidden now",
        "iptables-save remains forbidden now",
        "iptables-restore remains forbidden now",
        "customer nat/customer firewall rules remain forbidden now",
        "no-op/fake apply adapter contract",
        "restore point boundary",
        "lock boundary",
        "verify boundary",
        "rollback boundary",
        "future phase 6-e entry criteria",
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
        "farms-over alone must not harden",
        "worker-over alone must not harden",
        "no silent skip",
    ]
    for item in required:
        assert item in text


def test_phase_status_gate_values_unchanged() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    required = [
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "customer_onboarding_allowed: db_only",
        "proxy_data_plane_allowed: limited_runtime_local_only",
        "ui_allowed: no",
        "telegram_allowed: no",
    ]
    for item in required:
        assert item in text


def test_no_docs_authorize_live_apply_or_iptables_now() -> None:
    docs_text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in Path("docs").glob("*.md")
    )
    forbidden = [
        "phase 6-d1 authorizes live apply",
        "phase 6 d1 authorizes live apply",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
    ]
    for item in forbidden:
        assert item not in docs_text
