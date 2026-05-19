from pathlib import Path


def test_phase11_farm5_0_1_145_evidence_doc_present_and_tokens() -> None:
    t = Path("docs/PHASE_11_FARM5_0_1_145_SYNC_TEST_EVIDENCE.md").read_text(encoding="utf-8")
    assert "0.1.145" in t
    assert "806 passed in 135.84s" in t
    assert "mpf doctor: OK" in t
    assert "database: OK" in t
    assert "proxy config: OK" in t
    assert "proxy status: OK" in t
    assert "proxy doctor: OK" in t
    assert "planning safety gate passed" in t
    assert "Production customer traffic remains disabled." in t
    assert "apply mode remains `plan_only`" in t
    assert "no MPF/customer IPv4 firewall references detected" in t
    assert "no MPF/customer IPv6 firewall references detected" in t
    assert "no customer NAT redirects are active" in t
    assert "local-only" in t
    assert "does **not** authorize Phase 11D" in t
