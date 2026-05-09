from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_doc(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_control_rules_contract_is_future_only() -> None:
    text = read_doc("docs/CONTROL_RULES.md")

    assert "Runtime impact: none" in text
    assert "Firewall impact: none" in text
    assert "Database migration impact: none in the current phase" in text
    assert "control_rules" in text
    assert "future generic intent model" in text.lower()
    assert "must not apply firewall rules by itself" in text
    assert "Phase 5 — Customer CRUD in DB Only" in text
    assert "worker enforcement" in text
    assert "all active customers in all enabled lanes remain evaluatable" in text


def test_worker_policy_contract_keeps_enforcement_future_only() -> None:
    text = read_doc("docs/WORKER_POLICY.md")

    assert "Runtime impact: none" in text
    assert "Worker names are Stratum-layer identities" in text
    assert "not firewall-layer identities" in text
    assert "worker_routing_rules" in text
    assert "future worker policy and worker routing boundary" in text
    assert "worker enforcement is future-only" in text
    assert "worker block implemented only as IP firewall block" in text
    assert "sustained miner-abuse after about 3600 seconds" in text


def test_phase5_task_requires_control_and_worker_docs_without_runtime() -> None:
    text = read_doc("docs/AI_PHASE_5_TASK.md")

    assert "docs/CONTROL_RULES.md" in text
    assert "docs/WORKER_POLICY.md" in text
    assert "Phase 5 Contract Clarification" in text
    assert "DB-only" in text
    assert "control_rules migration without explicit phase approval" in text
    assert "worker_routing_rules migration without explicit phase approval" in text
    assert "runtime block command" in text
    assert "runtime pause command" in text
    assert "worker scanner" in text
    assert "worker enforcement" in text
    assert "Phase 5 must not introduce any path that silently excludes active customers" in text


def test_index_lists_control_and_worker_contracts_for_phase5() -> None:
    text = read_doc("docs/INDEX.md")

    assert "docs/CONTROL_RULES.md" in text
    assert "docs/WORKER_POLICY.md" in text
    assert "Phase 5 — Customer CRUD in DB Only" in text
    assert "documentation-only contract clarification" in text
    assert "no runtime block/pause command in Phase 5" in text
    assert "no worker scanner or worker enforcement in Phase 5" in text


def test_contract_docs_do_not_introduce_runtime_artifact_paths() -> None:
    # Documentation may mention forbidden runtime words, but this patch must not
    # create runtime source files, migrations, services, or systemd units for the
    # future control/worker contracts.
    forbidden_paths = {
        "mpf/services/control_rule_service.py",
        "mpf/services/worker_policy_service.py",
        "mpf/repositories/control_rule_repo.py",
        "mpf/repositories/worker_routing_repo.py",
        "systemd/mpf-worker-guard.service",
        "systemd/mpf-worker-guard.timer",
        "systemd/mpf-control-expire.service",
        "systemd/mpf-control-expire.timer",
    }

    for relative_path in forbidden_paths:
        assert not (ROOT / relative_path).exists(), relative_path
