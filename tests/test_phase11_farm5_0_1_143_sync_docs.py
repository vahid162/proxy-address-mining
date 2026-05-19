from pathlib import Path


def test_phase11_farm5_0_1_143_evidence_doc_present_and_tokens() -> None:
    t = Path("docs/PHASE_11_FARM5_0_1_143_SYNC_TEST_EVIDENCE.md").read_text(encoding="utf-8")
    assert "server version after sync: `0.1.143`" in t
    assert "798 passed in 151.30s" in t
    assert "mpf doctor: `OK`" in t
    assert "proxy config: `OK`" in t
    assert "proxy status: `OK`" in t
    assert "proxy doctor: `OK`" in t
    assert "phase safety gate: `OK`" in t
    assert "Production customer traffic remains disabled." in t
    assert "No MPF/customer NAT redirects are active." in t

