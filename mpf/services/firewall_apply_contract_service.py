from __future__ import annotations

from mpf.domain.firewall import (
    FirewallApplyContract,
    FirewallApplyReadinessContract,
    FirewallPlanMessage,
    FirewallPlanResult,
)


def build_apply_readiness_contract(
    plan: FirewallPlanResult,
    restore_contract: FirewallApplyContract | None = None,
) -> FirewallApplyReadinessContract:
    contract = FirewallApplyReadinessContract(
        backend=plan.backend,
        apply_mode=plan.apply_mode,
        renderable=bool(restore_contract.renderable) if restore_contract is not None else False,
        source_restore_payload_contract=restore_contract,
    )

    if restore_contract is not None and restore_contract.restore_payload is not None:
        contract.restore_point_contract.desired_payload_hash = restore_contract.restore_payload.payload_sha256

    contract.warnings.extend(plan.warnings)
    contract.errors.extend(plan.errors)

    if restore_contract is not None:
        contract.warnings.extend(restore_contract.warnings)
        contract.errors.extend(restore_contract.errors)

    if plan.planner_customer_source == "config_only":
        contract.warnings.append(
            FirewallPlanMessage(
                code="config_only_source",
                message="explicit config-only source requested; db-readonly remains the default source",
                severity="warning",
            )
        )

    contract.applyable = False
    return contract
