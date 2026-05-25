from pathlib import Path


def test_phase11e_runbook_enforces_two_terminal_workflow() -> None:
    t = Path("docs/PHASE_11E_SINGLE_CUSTOMER_RUNTIME_STRATUM_EVIDENCE_RUNBOOK.md").read_text(encoding="utf-8").lower()

    assert "scripts/phase11e_external_stratum_probe.py" in t
    assert "scripts/phase11e_collect_runtime_stratum_evidence.sh" in t
    assert "ready_to_copy_transcript" in t
    assert "scp /tmp/limited-btc-001-20101-transcript.json" in t
    assert "--wait-for-transcript-seconds 300" in t
    assert "--capture-delay-seconds 0" in t
    assert "--expected-version 0.1.211" in t
    assert "outside farm5" in t
    assert ("no hairpin" in t) or ("no self" in t)
    assert "does not authorize or perform production activation" in t
    assert "sudo scripts/phase11e_collect_runtime_stratum_evidence.sh" in t
    assert "do" in t and "run this from farm5" in t and "not" in t
