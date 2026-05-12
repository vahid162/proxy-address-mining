from pathlib import Path

from mpf.adapters.firewall_harness import FakeNoopFirewallHarnessAdapter
from mpf.services.firewall_harness_service import run_apply_verify_harness, run_verify_failure_with_rollback_guidance


def test_fake_noop_adapter_records_deterministic_call_order() -> None:
    adapter = FakeNoopFirewallHarnessAdapter()
    report = run_apply_verify_harness(adapter)
    assert report.calls == ["plan", "apply", "verify"]
    assert report.ok is True


def test_fake_noop_adapter_verify_failure_triggers_rollback_guidance_order() -> None:
    adapter = FakeNoopFirewallHarnessAdapter(fail_verify=True)
    report = run_verify_failure_with_rollback_guidance(adapter)
    assert report.calls == ["plan", "apply", "verify", "rollback"]
    assert report.ok is False


def test_harness_reports_only_and_non_mutating_flags() -> None:
    adapter = FakeNoopFirewallHarnessAdapter()
    report = run_apply_verify_harness(adapter)
    assert report.report_only is True
    assert report.database_write is False
    assert report.lock_acquired is False
    assert report.restore_point_written is False
    assert report.apply is not None
    assert report.apply.safety_flags.host_firewall_mutated is False
    assert report.apply.safety_flags.iptables_save_executed is False
    assert report.apply.safety_flags.iptables_restore_executed is False


def test_adapter_source_does_not_import_subprocess() -> None:
    text = Path("mpf/adapters/firewall_harness.py").read_text(encoding="utf-8")
    assert "import subprocess" not in text
