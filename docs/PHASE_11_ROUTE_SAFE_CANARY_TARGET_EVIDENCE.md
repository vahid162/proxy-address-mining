# Phase 11 Route-safe Canary Target Evidence (0.1.163 failure diagnosis)

- In `0.1.163`, single-canary DNAT structurally applied as `--dport 20001 -> 127.0.0.1:60010`.
- External `nc -vz SERVER_PUBLIC_IP 20001` timed out.
- `MPF_NAT_PRE` counters increased during external test (traffic reached rule).
- `route_localnet` remained disabled (`net.ipv4.conf.all.route_localnet=0`, `net.ipv4.conf.ens224.route_localnet=0`).
- Host reachability checks were OK for `127.0.0.1:60010` and `172.18.0.3:60010`.
- Runtime Docker target observed: `mpf-forwarder-btc=172.18.0.3`.
- Failed canary DNAT rule was manually removed; `MPF_NAT_PRE` and PREROUTING hook remained.
- Diagnosis: loopback DNAT target is not route-safe for external PREROUTING DNAT when `route_localnet=0`.
- Phase 11 remains not accepted.
- Limited real customer onboarding remains forbidden.
