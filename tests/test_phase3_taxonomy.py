from __future__ import annotations

from mpf.domain.taxonomy import AbuseStatus, ActorType, CustomerStatus, EventSeverity, RequestContext, WorkerEventType


def test_phase3_taxonomy_core_values_are_stable() -> None:
    assert EventSeverity.CRITICAL == "critical"
    assert ActorType.INTERNAL_API == "internal_api"
    assert CustomerStatus.ACTIVE == "active"
    assert AbuseStatus.OVER_TRACKING == "over_tracking"
    assert WorkerEventType.IDENTITY_OBSERVED == "worker.identity.observed"


def test_request_context_has_correlation_id_and_safe_defaults() -> None:
    context = RequestContext()
    assert context.correlation_id
    assert context.actor_type == ActorType.SYSTEM
    assert context.source_interface == "cli"
    assert context.confirmed is False
