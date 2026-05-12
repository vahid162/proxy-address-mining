from pathlib import Path

from mpf.adapters.firewall_harness import FakeNoopFirewallHarnessAdapter
from mpf.services.firewall_harness_service import run_apply_verify_harness, run_verify_failure_with_rollback_guidance


def test_doc_exists_and_non_authorizing() -> None:
    t = Path('docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md').read_text(encoding='utf-8')
    required = [
        'isolated/non-production only',
        'does not authorize host production firewall mutation',
        'live firewall read/write',
        'iptables-save',
        'iptables-restore',
        'real iptables adapters',
    ]
    for needle in required:
        assert needle in t


def test_doc_preserves_abuse_invariant() -> None:
    t = Path('docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md').read_text(encoding='utf-8')
    for needle in [
        'normal -> over_tracking -> over_grace -> hard',
        '3600 seconds',
        'farms-over alone must not harden',
        'worker-over alone must not harden',
        'all active customers in enabled lanes must be covered',
        'no silent skip is allowed',
    ]:
        assert needle in t


def test_adapter_ordering_and_failures() -> None:
    adapter = FakeNoopFirewallHarnessAdapter(fail_plan=True)
    assert adapter.plan().ok is False
    assert [c.operation for c in adapter.calls] == ['plan']

    adapter = FakeNoopFirewallHarnessAdapter(fail_verify=True)
    report = run_verify_failure_with_rollback_guidance(adapter)
    assert report.calls == ['plan', 'apply', 'verify', 'rollback']
    assert report.rollback is not None


def test_adapter_and_service_no_subprocess_or_iptables_terms() -> None:
    a = Path('mpf/adapters/firewall_harness.py').read_text(encoding='utf-8')
    s = Path('mpf/services/firewall_harness_service.py').read_text(encoding='utf-8')
    assert 'import subprocess' not in a
    assert 'import subprocess' not in s
    assert 'iptables-save' not in a
    assert 'iptables-save' not in s
    assert 'iptables-restore' not in a
    assert 'iptables-restore' not in s


def test_safety_flags_always_false() -> None:
    adapter = FakeNoopFirewallHarnessAdapter()
    result = adapter.apply()
    flags = result.safety_flags
    assert flags.host_firewall_mutated is False
    assert flags.iptables_save_executed is False
    assert flags.iptables_restore_executed is False
    assert flags.database_write is False
    assert flags.lock_acquired is False
    assert flags.restore_point_written is False

    report = run_apply_verify_harness(adapter)
    assert report.report_only is True
    assert report.database_write is False
    assert report.lock_acquired is False
    assert report.restore_point_written is False
