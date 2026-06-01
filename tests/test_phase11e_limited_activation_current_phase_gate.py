from pathlib import Path

import pytest

from mpf.services.phase11e_limited_activation_common import validate_current_phase_gate


SAFE_CURRENT_STATE = """\
## Current State

```text
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
```
"""


def _validate(tmp_path: Path, content: str) -> list[str]:
    phase_status = tmp_path / "PHASE_STATUS.md"
    phase_status.write_text(content, encoding="utf-8")
    blockers: list[str] = []
    validate_current_phase_gate(blockers, phase_status_path=phase_status)
    return blockers


def test_current_phase_gate_validation_uses_safe_current_state_block(tmp_path: Path) -> None:
    assert _validate(tmp_path, SAFE_CURRENT_STATE) == []


def test_current_phase_gate_rejects_open_current_state_despite_safe_historical_line(tmp_path: Path) -> None:
    content = SAFE_CURRENT_STATE.replace("production_traffic: none", "production_traffic: controlled_cli_limited")
    content += "\n## Historical note\nproduction_traffic: none\n"
    assert "current_phase_gate_open:production_traffic" in _validate(tmp_path, content)


@pytest.mark.parametrize(
    "content",
    [
        "production_traffic: none\n",
        "## Current State\nproduction_traffic: none\n",
        "## Current State\n```text\nproduction_traffic: none\n",
        "## Current State\n```text\n```\n",
        "## Current State\nmissing fence\n## Historical note\n```text\nproduction_traffic: none\n```\n",
    ],
)
def test_current_phase_gate_rejects_missing_or_malformed_current_state_block(tmp_path: Path, content: str) -> None:
    assert "current_phase_gate_malformed" in _validate(tmp_path, content)
