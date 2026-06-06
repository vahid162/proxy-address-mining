from __future__ import annotations

from mpf.services.phase11_controlled_artifact_reapply_core import SCOPE


def build_controlled_artifact_reapply_rollback_plan(exact_added_delta: list[str] | None = None) -> dict[str, object]:
    return {
        "automatic_rollback_execution_available": False,
        "manual_review_required": True,
        "rollback_scope": list(SCOPE),
        "exact_inverse_delta": [
            {"added_artifact": item, "safe_inverse": "operator_review_required", "automatic_execution": False}
            for item in (exact_added_delta or [])
        ],
    }
