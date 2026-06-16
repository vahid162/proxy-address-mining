from pathlib import Path


def test_firewall_completion_collector_is_read_only_and_uses_verify():
    text = Path("scripts/phase11_collect_firewall_completion_evidence.sh").read_text(encoding="utf-8")
    assert "firewall-completion-evidence-bundle-verify" in text
    assert "iptables-save" in text
    forbidden = ["--execute", "--rollback-apply", "controlled-artifact-reapply-execute", "iptables-restore", "conntrack -F", "systemctl restart", "docker restart"]
    for needle in forbidden:
        assert needle not in text


def test_firewall_completion_collector_avoids_verify_output_self_scan():
    text = Path("scripts/phase11_collect_firewall_completion_evidence.sh").read_text(encoding="utf-8")
    assert "VERIFY_REPORT_TMP=\"$(mktemp)\"" in text
    assert "FINAL_VERIFY_REPORT_TMP=\"$(mktemp)\"" in text
    assert "run_json \"${VERIFY_REPORT_TMP}\" \"${MPF_BIN}\" production firewall-completion-evidence-bundle-verify" in text
    assert "run_json \"${OUT_DIR}/firewall-completion-evidence-bundle-verify.json\" \"${MPF_BIN}\" production firewall-completion-evidence-bundle-verify" not in text
    assert "cp \"${VERIFY_REPORT_TMP}\" \"${OUT_DIR}/firewall-completion-evidence-bundle-verify.json\"" in text


def test_operational_surfaces_collector_references_optional_firewall_bundle():
    text = Path("scripts/phase11_collect_operational_surfaces_evidence.sh").read_text(encoding="utf-8")
    assert "MPF_FIREWALL_COMPLETION_EVIDENCE_DIR" in text
    assert "--firewall-completion-evidence-dir" in text
    assert "firewall-completion-evidence-manifest.json" in text
    assert "firewall-completion-evidence-SHA256SUMS.txt" in text
