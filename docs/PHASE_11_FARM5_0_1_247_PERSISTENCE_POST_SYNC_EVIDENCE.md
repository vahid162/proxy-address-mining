# Phase 11 Farm5 0.1.247 Persistence Post-Sync Evidence

Status: focused source-backed evidence note for the 0.1.248 integration fix.

Farm5 post-sync evidence for repository version `0.1.247` showed that the sync succeeded and the farm5 test suite passed after synchronization. Runtime container persistence was healthy: `mpf-v2raya`, `mpf-v2raya-socks-bridge`, and `mpf-forwarder-btc` were present, running, and healthy.

The local runtime listeners were correct and local-only: `127.0.0.1:2015` for the v2rayA UI listener and `127.0.0.1:60010` for the BTC backend listener. Backend public exposure was false, `missing_containers` was `[]`, `unhealthy_containers` was `[]`, `unexpected_project_containers` was `[]`, and `unknown_mpf_artifacts` was `[]`.

Known controlled Phase 11 customer firewall artifacts were absent after reboot. That means no Docker runtime repair was required, but controlled customer firewall artifact persistence remains unresolved.

Version `0.1.247` exposed an integration bug: Compose path scope validation compared raw strings and rejected the official absolute installed Compose path, and the package builder generated a plan without live container/socket/config observations. This made the package fabricate missing runtime state even though live diagnosis showed healthy runtime state.

No execute helper was run for this evidence note. No Docker mutation was performed. No firewall mutation was performed. No DB mutation, conntrack flush, systemd action, reboot, worker enforcement, UI, Telegram, buyer panel, public API, or production expansion was performed.

Correct next implementation step:

```text
implement_controlled_artifact_reapply_execute_package
```

Restart/autostart proof remains `missing_or_partial`, Full CLI Production Operations remains not accepted, and Phase 12 remains blocked.
