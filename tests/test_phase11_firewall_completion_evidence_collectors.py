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


def test_operational_surfaces_collector_resolves_firewall_wrapper_and_preserves_readiness():
    text = Path("scripts/phase11_collect_operational_surfaces_evidence.sh").read_text(encoding="utf-8")
    assert "FIREWALL_COMPLETION_EVIDENCE_DIR}/production-firewall-apply-verify-rollback-readiness.json" in text
    assert "FIREWALL_COMPLETION_EVIDENCE_DIR}/firewall-completion-evidence/production-firewall-apply-verify-rollback-readiness.json" in text
    assert "recomputed_nested_raw_evidence" in text
    assert "recomputed_raw_evidence" in text
    assert "copied_readiness_json" in text
    assert "copied_nested_readiness_json" in text
    assert "invalid_readiness_json" in text
    assert "firewall_completion_readiness_json_unsafe" in text
    assert "firewall_completion_readiness_json_invalid" in text
    assert "FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED" in text
    assert "firewall_completion_evidence_dir_resolved" in text
    assert "firewall_completion_readiness_source" in text


def test_operational_surfaces_collector_does_not_fallback_from_invalid_readiness_to_recompute():
    text = Path("scripts/phase11_collect_operational_surfaces_evidence.sh").read_text(encoding="utf-8")
    invalid_idx = text.index('FIREWALL_COMPLETION_READINESS_SOURCE="invalid_readiness_json"')
    next_recompute = text.find('production-firewall-apply-verify-rollback-readiness --evidence-dir', invalid_idx)
    next_branch = text.find('elif [[ -d', invalid_idx)
    assert next_recompute == -1 or (next_branch != -1 and next_branch < next_recompute)
