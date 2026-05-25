from pathlib import Path


def test_phase11e_runtime_stratum_runbook_matches_real_cli_flags() -> None:
    t = Path("docs/PHASE_11E_SINGLE_CUSTOMER_RUNTIME_STRATUM_EVIDENCE_RUNBOOK.md").read_text(encoding="utf-8")

    assert "bash scripts/verify_current_phase_gate.sh" in t
    assert "do not bypass" in t

    step7 = t.split("## Step 7)", 1)[1].split("## Step 8)", 1)[0]
    assert "--i-understand-runtime-evidence-only" in step7
    assert "--i-understand-no-production-traffic-acceptance" in step7
    assert "--i-understand-no-miner-traffic-acceptance" in step7
    assert "--i-understand-no-db-activation" in step7
    assert "--i-confirm-stratum-transcript-required" in step7
    assert "--i-confirm-visibility-bundle-required" in step7
    assert "--i-confirm-abuse-1h-required-before-customer-traffic" in step7
    assert "--i-confirm-restart-container-order-required-before-limited-acceptance" in step7
    assert "--i-understand-read-only-evidence" not in step7
    assert "--i-understand-no-runtime-activation" not in step7

    step8 = t.split("## Step 8)", 1)[1].split("## Step 9)", 1)[0]
    assert "--transcript-json \"$RTE_DIR/stratum-transcript.json\"" in step8
    for bad in ("--expected-version", "--transcript-json-sha256", "--operator", "--reason", "--operator-confirmed"):
        assert bad not in step8

    step9 = t.split("## Step 9)", 1)[1].split("## Step 10)", 1)[0]
    assert "--runtime-path-evidence-json-sha256" in step9
    assert "--stratum-transcript-evidence-json-sha256" in step9
    for bad in ("--expected-version", "--operator", "--reason", "--operator-confirmed"):
        assert bad not in step9
