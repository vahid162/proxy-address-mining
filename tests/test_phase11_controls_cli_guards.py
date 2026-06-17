from types import SimpleNamespace
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from mpf.repositories.customer_write_repo import CustomerMutationResult
from mpf.domain.customer_lifecycle import DomainValidationError


def test_update_blocked_controlled(monkeypatch):
    import mpf.interfaces.cli as cli
    monkeypatch.setattr(cli, "_load", lambda p: SimpleNamespace(database=SimpleNamespace(url="postgresql:///mpf")))
    monkeypatch.setattr(cli.customer_mutation_service, "update_db_only_customer", lambda *a, **k: (_ for _ in ()).throw(DomainValidationError("status must be active/paused/expired/deleted")))
    res=CliRunner().invoke(app,["customer","update","--customer-key","limited-btc-001","--status","blocked"])
    assert res.exit_code == 1
    assert "status must be active/paused/expired/deleted" in res.output
    assert "Traceback" not in res.output


def test_no_yes_dry_run_reaches_service_and_yes_guards(monkeypatch):
    import mpf.interfaces.cli as cli
    cfg=SimpleNamespace(database=SimpleNamespace(url="postgresql:///mpf"))
    monkeypatch.setattr(cli, "_load", lambda p: cfg)
    called=[]
    monkeypatch.setattr(cli.customer_mutation_service, "disable_db_only_customer", lambda cfg, req, dry_run: called.append(("disable",dry_run)) or CustomerMutationResult(ok=True,message="DRY_RUN_OK"))
    monkeypatch.setattr(cli.customer_mutation_service, "update_db_only_customer", lambda cfg, req, dry_run: called.append(("update",dry_run)) or CustomerMutationResult(ok=True,message="DRY_RUN_OK"))
    monkeypatch.setattr(cli, "write_local_peer_root_guard_message", lambda *a, **k: "local peer PostgreSQL write requires mpf OS user")
    r=CliRunner().invoke(app,["customer","disable","--customer-key","limited-btc-001"])
    assert r.exit_code == 0 and ("disable", True) in called
    r=CliRunner().invoke(app,["customer","update","--customer-key","limited-btc-001","--status","expired"])
    assert r.exit_code == 0 and ("update", True) in called
    r=CliRunner().invoke(app,["customer","update","--customer-key","limited-btc-001","--status","expired","--yes"])
    assert r.exit_code == 1
    assert "local peer PostgreSQL write requires mpf OS user" in r.output
