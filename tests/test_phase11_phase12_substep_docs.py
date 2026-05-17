from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_phase11_substeps_are_explicit_and_ordered() -> None:
    t = _read("docs/AI_PHASE_11_TASK.md")
    items = [
        "Phase 11A — Production readiness inventory",
        "Phase 11B — CLI canary plan/report only",
        "Phase 11C — Controlled firewall/customer activation harness",
        "Phase 11D — Manual canary customer acceptance",
        "Phase 11E — Limited real customer onboarding",
        "Phase 11F — Phase 11 final acceptance report",
    ]
    assert "Do not implement Phase 11 as one large production-enabling PR." in t
    assert [t.index(item) for item in items] == sorted(t.index(item) for item in items)
    assert "sub-step gate ordering tests" in t


def test_phase12_substeps_are_explicit_and_ordered() -> None:
    t = _read("docs/AI_PHASE_12_TASK.md")
    items = [
        "Phase 12A — Worker evidence and mapping readiness",
        "Phase 12B — Worker policy service in detection_only mode",
        "Phase 12C — Manual operator enforcement action planning",
        "Phase 12D — Adapter capability and failure-mode readiness",
        "Phase 12E — Controlled enforcement canary",
        "Phase 12F — Phase 12 final acceptance report",
    ]
    assert "Do not implement strict worker enforcement as one large PR." in t
    assert [t.index(item) for item in items] == sorted(t.index(item) for item in items)
    assert "sub-step gate ordering tests" in t


def test_phase11_phase12_docs_preserve_service_layer_and_safety() -> None:
    p11 = _read("docs/AI_PHASE_11_TASK.md")
    p12 = _read("docs/AI_PHASE_12_TASK.md")
    assert "Implementation must be Python-first and API-first" in p11
    assert "Implementation must be Python-first and API-first" in p12
    assert "The CLI must stay a thin interface" in p11
    assert "The CLI is only an interface" in p12
    assert "worker policy enforcement in Phase 11" in p11
    assert "firewall-only worker-name blocking" in p12
    assert "safe fallback to detection_only" in p12
