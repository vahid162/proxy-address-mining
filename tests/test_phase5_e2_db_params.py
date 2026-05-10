from mpf.db import query_database_params


def test_query_database_params_rejects_mutating_sql(monkeypatch):
    class C:
        class D:
            url = "postgresql:///mpf"

        database = D()

    result = query_database_params(C(), "update customers set status='x' where id=%s", (1,))
    assert result.ok is False


def test_query_database_params_local_peer_root_uses_psql_fallback(monkeypatch):
    from mpf import db

    class C:
        class D:
            url = "postgresql:///mpf"

        database = D()

    captured = {}

    def fake_query(dbname, sql):
        captured["dbname"] = dbname
        captured["sql"] = sql
        return type("R", (), {"ok": True, "rows": [], "message": "OK"})()

    monkeypatch.setattr(db.os, "geteuid", lambda: 0)
    monkeypatch.setattr(db, "_query_local_peer_as_mpf", fake_query)
    res = query_database_params(C(), "select * from customers where customer_key=%s and id=%s", ("ab'c", 2))
    assert res.ok is True
    assert "'ab''c'" in captured["sql"]
    assert "2" in captured["sql"]
