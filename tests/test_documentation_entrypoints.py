from pathlib import Path


def test_docs_index_is_concise_task_routed_entrypoint():
    text = Path("docs/INDEX.md").read_text()
    assert text.startswith("# Documentation Index\n")
    for heading in (
        "## Authority order",
        "## Required reading",
        "## Core contracts",
        "## Task routing",
        "## Historical references",
    ):
        assert heading in text
    for expected in (
        "`AGENTS.md` = AI operating instructions",
        "`docs/PHASE_STATUS.md` = only dynamic project-state authority",
        "`docs/SAFETY.md` = safety restrictions",
        "`docs/ARCHITECTURE.md` = architecture boundaries",
        "`CHANGELOG.md` = release history",
        "`docs/history/` = non-authorizing historical context",
    ):
        assert expected in text


def test_docs_index_does_not_duplicate_dynamic_or_historical_detail():
    text = Path("docs/INDEX.md").read_text()
    for forbidden in (
        "current_accepted_phase:",
        "current_working_phase:",
        "next_required_step",
        "farm5 0.1.",
        "docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md",
        "docs/PHASE_11_FARM5_",
        "production_traffic=",
        "customer_onboarding_allowed=",
    ):
        assert forbidden not in text


def test_legacy_archives_have_required_notice():
    notice = (
        "# Historical Reference\n\n"
        "This file preserves the former active document for historical context.\n\n"
        "It is non-authorizing.\n"
        "Current dynamic project state is defined only by `docs/PHASE_STATUS.md`.\n"
        "Current AI instructions are defined by root `AGENTS.md`.\n\n"
    )
    for path in (
        Path("docs/history/README_LEGACY_0.1.299.md"),
        Path("docs/history/INDEX_LEGACY_0.1.299.md"),
    ):
        assert path.read_text().startswith(notice)


def test_phase8_services_ignore_active_entrypoint_and_history_text(tmp_path):
    from shutil import copytree

    from mpf.config import load_config
    from mpf.services.phase8_abuse_dry_run_evaluator_service import build_phase8_abuse_dry_run_evaluator_report
    from mpf.services.phase8_abuse_evidence_reporting_contract_service import build_phase8_abuse_evidence_reporting_contract_report
    from mpf.services.phase8_abuse_state_machine_contract_service import build_phase8_abuse_state_machine_contract_report
    from mpf.services.phase8_db_transition_execution_service import build_phase8_db_transition_execution_report
    from mpf.services.phase8_db_transition_readiness_service import build_phase8_db_transition_readiness_report
    from mpf.services.phase8_runtime_worker_integration_readiness_service import build_phase8_runtime_worker_integration_readiness_report

    repo = tmp_path / "repo"
    copytree("docs", repo / "docs")
    (repo / "mpf").mkdir()
    (repo / "mpf/models.py").write_text(Path("mpf/models.py").read_text(encoding="utf-8"), encoding="utf-8")
    (repo / "README.md").write_text(Path("README.md").read_text(encoding="utf-8"), encoding="utf-8")

    cfg = load_config(Path("configs/mpf.example.yaml"))
    builders = (
        build_phase8_abuse_state_machine_contract_report,
        build_phase8_abuse_evidence_reporting_contract_report,
        build_phase8_abuse_dry_run_evaluator_report,
        build_phase8_db_transition_readiness_report,
        build_phase8_db_transition_execution_report,
        build_phase8_runtime_worker_integration_readiness_report,
    )

    def summary():
        reports = [builder(cfg, repo) for builder in builders]
        return [
            {
                "component": report["component"],
                "final_decision": report["final_decision"],
                "blockers": report["blockers"],
                "execution_allowed": report["execution_allowed"],
                "db_writes_authorized": report.get("db_writes_authorized"),
                "firewall_apply_authorized": report.get("firewall_apply_authorized"),
                "production_traffic_authorized": report.get("production_traffic_authorized"),
            }
            for report in reports
        ]

    before = summary()
    (repo / "README.md").write_text("# Proxy Address Mining\nchanged active entrypoint only\n", encoding="utf-8")
    (repo / "docs/INDEX.md").write_text("# Documentation Index\nchanged active index only\n", encoding="utf-8")
    (repo / "docs/history/README_LEGACY_0.1.299.md").write_text("historical archive poison pill", encoding="utf-8")
    (repo / "docs/history/INDEX_LEGACY_0.1.299.md").write_text("historical archive poison pill", encoding="utf-8")
    after = summary()

    assert after == before
    for report in after:
        assert report["final_decision"] == "BLOCKED"
        assert report["execution_allowed"] is False
        assert not any("readme" in blocker.lower() or "index" in blocker.lower() for blocker in report["blockers"])


def test_phase8_services_use_phase_status_for_dynamic_state(tmp_path):
    from shutil import copytree

    from mpf.config import load_config
    from mpf.services.phase8_abuse_dry_run_evaluator_service import build_phase8_abuse_dry_run_evaluator_report

    repo = tmp_path / "repo"
    copytree("docs", repo / "docs")
    (repo / "README.md").write_text(Path("README.md").read_text(encoding="utf-8"), encoding="utf-8")
    cfg = load_config(Path("configs/mpf.example.yaml"))

    baseline = build_phase8_abuse_dry_run_evaluator_report(cfg, repo)["blockers"]
    (repo / "docs/PHASE_STATUS.md").write_text("current_accepted_phase: Phase 7\n", encoding="utf-8")
    changed = build_phase8_abuse_dry_run_evaluator_report(cfg, repo)["blockers"]

    assert baseline == []
    assert "current_state_preserved_missing_or_failed" in changed
