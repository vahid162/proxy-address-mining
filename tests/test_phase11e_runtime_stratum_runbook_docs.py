from pathlib import Path


def test_phase11e_runtime_stratum_runbook_contains_required_steps() -> None:
    t = Path("docs/PHASE_11E_SINGLE_CUSTOMER_RUNTIME_STRATUM_EVIDENCE_RUNBOOK.md").read_text(encoding="utf-8")
    assert "single-customer runtime + external Stratum evidence" in t
    assert "outside farm5" in t
    assert "sudo iptables-save > \"$RTE_DIR/live-iptables-save.txt\"" in t
    assert "sudo conntrack -L > \"$RTE_DIR/conntrack.txt\"" in t
    assert "mpf production single-customer-runtime-probe-diagnostics" in t
    assert "mpf production single-customer-runtime-path-evidence" in t
    assert "mpf production single-customer-stratum-transcript-evidence" in t
    assert "mpf production single-customer-visibility-bundle" in t
    assert "expected-version 0.1.208" in t
    assert "does not authorize or perform production activation" in t
