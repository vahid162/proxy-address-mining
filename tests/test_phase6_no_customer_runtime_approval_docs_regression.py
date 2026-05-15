from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_remaining_plan_runtime_approval_and_versions():
    text = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "No-customer runtime execution approval readiness" in text
    assert "latest recorded farm5 sync evidence is 0.1.94" in text


def test_ai_phase6_task_has_runtime_approval_command_and_abuse_invariant():
    text = _read("docs/AI_PHASE_6_TASK.md")
    assert "repository version after this pr becomes 0.1.99" in text.lower()
    assert "mpf firewall no-customer-runtime-execution-approval" in text
    assert "report-only" in text and "non-executing" in text and "non-authorizing" in text
    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "farms-over alone must not harden" in text
    assert "worker-over alone must not harden" in text
