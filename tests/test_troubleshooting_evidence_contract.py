from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_doc(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _scenario_blocks(text: str) -> list[str]:
    blocks = re.findall(
        r"\n(\d+\) .*?)(?=\n\d+\) |\n## Safety invariants)",
        "\n" + text,
        flags=re.S,
    )
    return [block.strip() for block in blocks]


def test_troubleshooting_evidence_doc_exists() -> None:
    assert (ROOT / "docs/TROUBLESHOOTING_EVIDENCE.md").exists()


def test_required_scenarios_and_phase_placement_are_documented() -> None:
    text = read_doc("docs/TROUBLESHOOTING_EVIDENCE.md")

    assert "customer cannot connect" in text
    assert "unexpected IP" in text
    assert "whitelist reject" in text
    assert "maxconn/connlimit" in text
    assert "hashlimit/rate" in text
    assert "backend reachable but pool/upstream issue" in text
    assert "worker mismatch" in text
    assert "first-connect activation evidence" in text
    assert "abuse evidence timeline" in text
    assert "time-sync-dependent evidence warning" in text
    assert "Phase 6 owns firewall planner evidence" in text
    assert "Phase 7 owns usage/policy/reject accounting" in text
    assert "Phase 8 owns abuse runtime" in text
    assert "Phase 9 owns check/report/diagnostic verdicts" in text
    assert "Phase 10 owns session/worker/policy timeline" in text


def test_all_18_scenarios_follow_explicit_template() -> None:
    text = read_doc("docs/TROUBLESHOOTING_EVIDENCE.md")
    blocks = _scenario_blocks(text)

    assert len(blocks) == 18

    required_labels = (
        "Required evidence:",
        "Future table(s):",
        "Future service owner:",
        "Future command:",
        "Phase placement:",
        "Forbidden in Phase 5:",
        "Expected verdict:",
    )

    for idx, block in enumerate(blocks, start=1):
        for label in required_labels:
            assert label in block, f"scenario {idx} missing {label}"


def test_required_tables_and_future_only_notes_are_documented() -> None:
    text = read_doc("docs/TROUBLESHOOTING_EVIDENCE.md")

    assert "flow_sessions" in text
    assert "flow_events" in text
    assert "worker_events" in text
    assert "customer_workers" in text
    assert "usage_samples" in text
    assert "policy_events" in text
    assert "firewall_applies" in text
    assert "firewall_rules_desired" in text
    assert "firewall_rules_live" in text
    assert "share_events" in text
    assert "future-only" in text


def test_phase5_forbids_runtime_collection_and_requires_retention_guard() -> None:
    text = read_doc("docs/TROUBLESHOOTING_EVIDENCE.md")

    assert "Phase 5 is **DB-only**" in text
    assert "no runtime evidence collection" in text
    assert "no collector" in text
    assert "no usage collector" in text
    assert "No high-volume collector may be activated without retention policy" in text
    assert "retention class" in text


def test_no_forbidden_runtime_files_added() -> None:
    forbidden_paths = {
        "mpf/services/flow_collector_service.py",
        "mpf/services/worker_scanner_service.py",
        "mpf/services/usage_collector_service.py",
        "systemd/mpf-flow-collector.service",
        "systemd/mpf-flow-collector.timer",
    }

    for relative_path in forbidden_paths:
        assert not (ROOT / relative_path).exists(), relative_path
