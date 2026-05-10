from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig


@dataclass(frozen=True)
class LaneSyncItem:
    name: str
    enabled: bool
    backend_port: int
    chain_prefix: str
    protocol: str


@dataclass(frozen=True)
class LaneSyncPlan:
    create_items: list[LaneSyncItem]
    update_items: list[LaneSyncItem]
    stale_items: list[LaneSyncItem]


@dataclass(frozen=True)
class LaneSyncResult:
    ok: bool
    message: str
    firewall_change: str = "no"
    nat_change: str = "no"
    runtime_change: str = "no"
    would_create_lanes: int = 0
    would_update_lanes: int = 0
    stale_db_lanes: int = 0
    created_lanes: list[str] | None = None
    updated_lanes: list[str] | None = None
    stale_lanes: list[str] | None = None


def _load_db_lanes(cur) -> dict[str, LaneSyncItem]:
    cur.execute("select name, enabled, backend_port, chain_prefix, protocol from lanes")
    rows = cur.fetchall()
    return {
        str(row[0]).lower(): LaneSyncItem(
            name=str(row[0]),
            enabled=bool(row[1]),
            backend_port=int(row[2]),
            chain_prefix=str(row[3]),
            protocol=str(row[4] or "stratum"),
        )
        for row in rows
    }


def _build_config_items(config: MPFConfig) -> dict[str, LaneSyncItem]:
    return {
        lane_name.lower(): LaneSyncItem(
            name=lane_name,
            enabled=lane.enabled,
            backend_port=lane.backend_port,
            chain_prefix=lane.chain_prefix,
            protocol="stratum",
        )
        for lane_name, lane in config.lanes.items()
    }


def build_lane_sync_plan(config: MPFConfig, db_lanes: dict[str, LaneSyncItem]) -> LaneSyncPlan:
    config_lanes = _build_config_items(config)
    creates: list[LaneSyncItem] = []
    updates: list[LaneSyncItem] = []

    for key, cfg_lane in sorted(config_lanes.items()):
        db_lane = db_lanes.get(key)
        if db_lane is None:
            creates.append(cfg_lane)
            continue
        if (
            db_lane.enabled != cfg_lane.enabled
            or db_lane.backend_port != cfg_lane.backend_port
            or db_lane.chain_prefix != cfg_lane.chain_prefix
            or db_lane.protocol != cfg_lane.protocol
        ):
            updates.append(cfg_lane)

    stale = [item for key, item in sorted(db_lanes.items()) if key not in config_lanes]
    return LaneSyncPlan(create_items=creates, update_items=updates, stale_items=stale)


def sync_lanes_from_config(config: MPFConfig, *, dry_run: bool = True, actor: str | None = "system") -> LaneSyncResult:
    try:
        import psycopg

        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    db_lanes = _load_db_lanes(cur)
                    plan = build_lane_sync_plan(config, db_lanes)
                    if dry_run:
                        return LaneSyncResult(
                            ok=True,
                            message="DRY_RUN_OK",
                            would_create_lanes=len(plan.create_items),
                            would_update_lanes=len(plan.update_items),
                            stale_db_lanes=len(plan.stale_items),
                            created_lanes=[item.name for item in plan.create_items],
                            updated_lanes=[item.name for item in plan.update_items],
                            stale_lanes=[item.name for item in plan.stale_items],
                        )

                    for item in plan.create_items:
                        cur.execute(
                            """
                            insert into lanes (name, enabled, backend_port, chain_prefix, protocol)
                            values (%s, %s, %s, %s, %s)
                            """,
                            (item.name, item.enabled, item.backend_port, item.chain_prefix, item.protocol),
                        )

                    for item in plan.update_items:
                        cur.execute(
                            """
                            update lanes
                            set enabled=%s, backend_port=%s, chain_prefix=%s, protocol=%s, updated_at=now()
                            where lower(name)=lower(%s)
                            """,
                            (item.enabled, item.backend_port, item.chain_prefix, item.protocol, item.name),
                        )

                    cur.execute(
                        """
                        insert into events (event_type, severity, subject_type, subject_id, message, data_json, created_by)
                        values (%s,%s,%s,%s,%s,%s::jsonb,%s)
                        """,
                        (
                            "lane.config_synced",
                            "info",
                            "lane",
                            None,
                            "Lane config sync applied",
                            "{}",
                            actor,
                        ),
                    )
                    cur.execute(
                        """
                        insert into audit_log (actor_type, actor_id, action, resource_type, resource_id, after_json, reason)
                        values (%s,%s,%s,%s,%s,%s::jsonb,%s)
                        """,
                        ("system", actor, "lane.config_sync", "lane", None, "{}", "db-only lane sync from config"),
                    )
    except Exception as exc:  # noqa: BLE001
        return LaneSyncResult(ok=False, message=str(exc))

    return LaneSyncResult(
        ok=True,
        message="OK",
        would_create_lanes=len(plan.create_items),
        would_update_lanes=len(plan.update_items),
        stale_db_lanes=len(plan.stale_items),
        created_lanes=[item.name for item in plan.create_items],
        updated_lanes=[item.name for item in plan.update_items],
        stale_lanes=[item.name for item in plan.stale_items],
    )
