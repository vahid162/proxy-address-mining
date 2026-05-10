from mpf.repositories.customer_repo import _map_show


def _base_row(bool_value: str):
    return {
        "id": 1,
        "customer_key": "cust_a",
        "lane": "btc",
        "name": "alice",
        "port": 20001,
        "status": "active",
        "activation_mode": "immediate",
        "service_days": 30,
        "activated_at": None,
        "starts_at": None,
        "expires_at": None,
        "first_connected_at": None,
        "expired_at": None,
        "delete_eligible_at": None,
        "deleted_at": None,
        "auto_expire_enabled": bool_value,
        "auto_delete_enabled": bool_value,
        "lifecycle_note": None,
        "miners": 1,
        "farms": 1,
        "maxconn": 1,
        "rate_per_min": 1,
        "burst": 1,
        "ips_mode": "any",
        "abuse_exempt": bool_value,
        "abuse_exempt_reason": None,
        "abuse_exempt_until": None,
        "abuse_exempt_by": None,
    }


def test_map_show_parses_f_as_false():
    rec = _map_show(_base_row("f"))
    assert rec.auto_expire_enabled is False
    assert rec.auto_delete_enabled is False
    assert rec.abuse_exempt is False


def test_map_show_parses_t_as_true():
    rec = _map_show(_base_row("t"))
    assert rec.auto_expire_enabled is True
    assert rec.auto_delete_enabled is True
    assert rec.abuse_exempt is True
