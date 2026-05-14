from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import firewall_apply_gate_readiness_service, firewall_restore_lock_record_execution_gate_service
from mpf.services.firewall_gate_review_service import build_gate_review_report
from mpf.services.firewall_planner_service import build_plan

RUNNER = CliRunner()


class _FakeDB:
    def __init__(self):
        self.restore_points=[]
        self.locks=[]
        self.applies=[]

class _FakeCursor:
    def __init__(self, db):
        self.db=db
        self._result=None
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def execute(self, sql, params=None):
        s=" ".join(sql.lower().split())
        if "select 1 from scheduler_locks" in s:
            self._result=None
        elif "insert into restore_points" in s:
            self.db.restore_points.append(params)
            self._result=(len(self.db.restore_points),)
        elif "insert into scheduler_locks" in s:
            self.db.locks.append(params)
            self._result=(params[2],)
        elif "insert into firewall_applies" in s:
            self.db.applies.append(params)
            self._result=(len(self.db.applies),)
        else:
            raise AssertionError(sql)
    def fetchone(self):
        return self._result

class _FakeConn:
    def __init__(self, db): self.db=db
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def cursor(self): return _FakeCursor(self.db)
    def transaction(self): return self

def _install_fake_psycopg(monkeypatch, db):
    conn=_FakeConn(db)
    class P:
        @staticmethod
        def connect(*args, **kwargs):
            return conn
    monkeypatch.setitem(__import__("sys").modules, "psycopg", P)


def _cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def _base_text() -> str:
    return """## Current State\n```text\ncurrent_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5\ncurrent_working_phase: Phase 6 — Firewall Planner\nserver_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\nproxy_data_plane_allowed: limited_runtime_local_only\nui_allowed: no\ntelegram_allowed: no\nlive_snapshot_read_allowed: iptables_save_read_only\nrestore_lock_record_execution_allowed: controlled_boundary_only\n```\nPhase 6 Read-Only iptables-save Snapshot — Server Evidence\nPhase 6 farm5 Time Synchronization — Server Evidence\nPhase 6 Restore/Lock/DB Apply Record Readiness — Server Sync\nPhase 6 Restore/Lock/DB Apply Record Gate — Proposal Boundary\nPhase 6 Restore/Lock/DB Apply Record Gate Report — Server Sync\nPhase 6 Restore/Lock/DB Apply Record Acceptance Gate — Server Sync\nSystem clock synchronized: yes\nNTPSynchronized=yes\n194.225.150.25\n"""


def test_service_blocked_and_not_authorized() -> None:
    r = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(_cfg())
    assert r["final_decision"] == "BLOCKED"
    assert r["authorization_status"] == "CONTROLLED_BOUNDARY_ACCEPTED_DRY_RUN"
    assert r["execution_allowed"] is False
    assert r["farm5_time_sync_resolved"] is True
    assert r["restore_lock_record_acceptance_gate_evidence_present"] is True
    

def test_blocks_on_changed_current_state(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PHASE_STATUS.md").write_text(_base_text().replace("production_traffic: none", "production_traffic: yes"), encoding="utf-8")
    r = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(_cfg(), repo_root=tmp_path)
    assert "Current State does not match required gate" in r["blockers"]


def test_blocks_missing_time_sync_or_acceptance_sections(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    text = _base_text().replace("Phase 6 farm5 Time Synchronization — Server Evidence", "").replace("Phase 6 Restore/Lock/DB Apply Record Acceptance Gate — Server Sync", "")
    (tmp_path / "docs" / "PHASE_STATUS.md").write_text(text, encoding="utf-8")
    r = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(_cfg(), repo_root=tmp_path)
    assert any("Time Synchronization" in b for b in r["blockers"])
    assert any("Acceptance Gate" in b for b in r["blockers"])


def test_blocks_on_non_plan_and_runtime_true() -> None:
    cfg = _cfg()
    cfg.firewall.apply_mode = "apply"
    cfg.proxy.runtime_activation_allowed = True
    r = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(cfg)
    assert "firewall.apply_mode is not plan_only" in r["blockers"]
    assert "proxy.runtime_activation_allowed is true" in r["blockers"]


def test_cli_human_json_invalid_output() -> None:
    human = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml"])
    assert human.exit_code == 0
    assert "final_decision: BLOCKED" in human.output
    assert "authorization_status: CONTROLLED_BOUNDARY_ACCEPTED_DRY_RUN" in human.output
    js = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml", "--output", "json"])
    assert js.exit_code == 0
    assert '"component": "firewall_restore_lock_record_execution_gate"' in js.output
    bad = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml", "--output", "yaml"])
    assert bad.exit_code != 0


def test_integrations_remain_blocked() -> None:
    cfg = _cfg()
    eg = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(cfg)
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    review = build_gate_review_report(plan=plan, restore_lock_record_execution_gate=eg)
    assert review.restore_lock_record_execution_gate_summary["authorization_status"] == "CONTROLLED_BOUNDARY_ACCEPTED_DRY_RUN"
    assert review.final_decision == "BLOCKED"
    apply = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg)
    assert apply["restore_lock_record_execution_gate_present"] is True
    assert apply["restore_lock_record_execution_gate_authorization_status"] == "CONTROLLED_BOUNDARY_ACCEPTED_DRY_RUN"
    assert apply["restore_lock_record_execution_gate_final_decision"] == "BLOCKED"
    assert apply["restore_lock_record_execution_gate_execution_allowed"] is False
    assert apply["final_decision"] == "BLOCKED"




def test_cli_requires_operator_reason_yes_for_execution() -> None:
    miss_op = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml", "--execute-controlled-boundary", "--reason", "r", "--yes"])
    assert miss_op.exit_code != 0
    miss_reason = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml", "--execute-controlled-boundary", "--operator", "alice", "--yes"])
    assert miss_reason.exit_code != 0
    miss_yes = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml", "--execute-controlled-boundary", "--operator", "alice", "--reason", "r"])
    assert miss_yes.exit_code != 0

def test_controlled_execution_real_db_writer_creates_three_records(monkeypatch) -> None:
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    r = firewall_restore_lock_record_execution_gate_service.run_restore_lock_record_controlled_execution(_cfg(), execute_controlled_boundary=True, operator="alice", reason="test", yes=True)
    assert r["execution_allowed"] is True
    assert r["restore_point_written"] is True
    assert r["lock_acquired"] is True
    assert r["db_apply_record_written"] is True
    assert len(db.restore_points) == 1
    assert len(db.locks) == 1
    assert len(db.applies) == 1
    assert db.applies[0][0] == "prepare"
    assert db.applies[0][1] == "blocked"
    assert r["apply_decision"] == "BLOCKED"
    assert r["iptables_restore_executed"] is False
    assert r["customer_nat_changed"] is False
    assert r["customer_firewall_rules_changed"] is False


def test_cli_execute_missing_args_exit_nonzero() -> None:
    res1 = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml", "--execute-controlled-boundary", "--reason", "r", "--yes"])
    assert res1.exit_code != 0
    res2 = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml", "--execute-controlled-boundary", "--operator", "alice", "--yes"])
    assert res2.exit_code != 0
    res3 = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml", "--execute-controlled-boundary", "--operator", "alice", "--reason", "r"])
    assert res3.exit_code != 0

def test_static_safety_tokens() -> None:
    text = Path("mpf/services/firewall_restore_lock_record_execution_gate_service.py").read_text(encoding="utf-8").lower()
    forbidden = [
        "import subprocess", "subprocess.", "import os", "docker", "systemctl", "conntrack", "iptables-restore", "open(", "write_text(", "mkdir(", "unlink(", "remove(", "rename(", "replace(",
    ]
    for token in forbidden:
        assert token not in text


def test_phase_status_execution_gate_sync_evidence_tokens_present() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "### Phase 6 Restore/Lock/DB Apply Record Execution Gate Scaffold — Server Sync" in text
    required = [
        "pytest with venv during sync: 566 passed in 12.51s",
        "NOT_AUTHORIZED_FOR_EXECUTION",
        "execution_allowed=false",
        "restore_point_write_allowed=false",
        "lock_acquisition_allowed=false",
        "db_apply_record_write_allowed=false",
        "iptables_restore_allowed=false",
        "customer_nat_allowed=false",
        "customer_firewall_rules_allowed=false",
        "production_traffic: none",
        "no usage automation",
        "no abuse automation",
        "no UI",
        "no Telegram",
    ]
    for token in required:
        assert token in text


def test_phase_status_current_state_block_unchanged() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    expected = """current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only"""
    assert expected in text


def test_phase6_controlled_execution_gate_proposal_review_section_present() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "### Phase 6 Controlled Restore/Lock/DB Apply Record Execution Gate — Proposal Review" in text
    required = [
        "proposal/review only",
        "non-authorizing",
        "execution_allowed remains false",
        "restore point writes",
        "lock acquisition",
        "DB apply record writes",
        "iptables-restore",
        "customer NAT/customer firewall rules",
        "production traffic",
        "usage automation",
        "abuse automation",
    ]
    for token in required:
        assert token in text


def test_phase6_controlled_execution_gate_proposal_review_acceptance_criteria_tokens() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    required = [
        "operator approval is explicitly recorded",
        "fresh farm5 evidence is included",
        "python -m pytest -q",
        "current phase safety gate passes",
        "mpf config validate OK",
        "mpf doctor OK",
        "mpf db status OK",
        "mpf proxy doctor final_verdict OK",
        "farm5 time sync remains resolved",
        "System clock synchronized: yes",
        "NTPSynchronized=yes",
        "194.225.150.25",
        "one restore point record/artifact",
        "one scoped firewall/apply lock",
        "one DB apply record in prepared/blocked state",
        "apply_decision=BLOCKED",
    ]
    for token in required:
        assert token in text


def test_phase6_controlled_execution_gate_proposal_review_still_forbidden_tokens() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    forbidden_listed = [
        "iptables-restore",
        "live firewall apply",
        "live rollback",
        "live verify",
        "customer NAT",
        "customer firewall rules",
        "production traffic",
        "usage automation",
        "abuse automation",
        "UI",
        "Telegram",
    ]
    for token in forbidden_listed:
        assert token in text


def test_phase6_controlled_execution_boundary_accepted_section_tokens() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "### Phase 6 Controlled Restore/Lock/DB Apply Record Execution Boundary — Accepted" in text
    required = [
        "accepted boundary only",
        "documentation/test-only",
        "no execution performed by this PR",
        "no runtime behavior enabled by this PR",
        "one restore point record/artifact",
        "one scoped firewall/apply lock",
        "one DB apply record in prepared/blocked state",
        "apply_decision=BLOCKED",
        "firewall_apply_allowed=no",
        "production_traffic=none",
        "restore_lock_record_execution_allowed: controlled_boundary_only",
        "--execute-controlled-boundary",
        "operator identity",
        "reason",
        "dry-run/default mode",
        "operator approval",
        "farm5 time sync evidence",
        "read-only iptables-save snapshot evidence",
    ]
    for token in required:
        assert token in text


def test_phase6_controlled_execution_boundary_accepted_still_forbidden_tokens() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    forbidden_listed = [
        "iptables-restore",
        "live firewall apply",
        "live rollback",
        "live verify",
        "customer NAT",
        "customer firewall rules",
        "production traffic",
        "usage automation",
        "abuse automation",
        "UI",
        "Telegram",
    ]
    for token in forbidden_listed:
        assert token in text


def test_db_failure_sets_execution_failed_status() -> None:
    cfg = _cfg()
    def boom(_payload):
        raise RuntimeError("db down")
    r = firewall_restore_lock_record_execution_gate_service.run_restore_lock_record_controlled_execution(
        cfg, execute_controlled_boundary=True, operator="alice", reason="test", yes=True, record_writer=boom
    )
    assert r["authorization_status"] == "CONTROLLED_BOUNDARY_EXECUTION_FAILED"
    assert r["execution_allowed"] is False
    assert r["restore_point_write_allowed"] is False
    assert r["lock_acquisition_allowed"] is False
    assert r["db_apply_record_write_allowed"] is False
    assert r["restore_point_written"] is False
    assert r["lock_acquired"] is False
    assert r["db_apply_record_written"] is False
    assert r["db_mutation"] is False
    assert r["errors"]


def test_lock_conflict_blocks_without_partial_records() -> None:
    cfg = _cfg()
    class ConflictCursor:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def execute(self, sql, params=None):
            self._sql = sql
        def fetchone(self):
            if "select 1 from scheduler_locks" in " ".join(self._sql.lower().split()):
                return (1,)
            return None

    class ConflictConn:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def cursor(self): return ConflictCursor()
        def transaction(self): return self

    r = firewall_restore_lock_record_execution_gate_service.run_restore_lock_record_controlled_execution(
        cfg, execute_controlled_boundary=True, operator="alice", reason="test", yes=True, connection_factory=lambda: ConflictConn()
    )
    assert r["authorization_status"] == "CONTROLLED_BOUNDARY_EXECUTION_FAILED"
    assert r["restore_point_written"] is False
    assert r["lock_acquired"] is False
    assert r["db_apply_record_written"] is False
    assert r["db_mutation"] is False
    assert any("scoped controlled execution lock already exists" in e for e in r["errors"])


def test_writer_uses_connection_factory_not_direct_cfg_url(monkeypatch) -> None:
    called = {"factory": 0}

    class _C:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def transaction(self): return self
        def cursor(self): return _FakeCursor(_FakeDB())

    def factory():
        called["factory"] += 1
        return _C()

    r = firewall_restore_lock_record_execution_gate_service.run_restore_lock_record_controlled_execution(
        _cfg(), execute_controlled_boundary=True, operator="alice", reason="test", yes=True, connection_factory=factory
    )
    assert called["factory"] == 1
    assert r["restore_point_written"] is True
