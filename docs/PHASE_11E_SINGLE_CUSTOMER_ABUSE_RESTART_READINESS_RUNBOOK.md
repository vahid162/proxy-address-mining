# Phase 11E abuse/restart readiness runbook

After 0.1.218 visibility bundle READY, abuse-1h and restart/container-order evidence gates are still required.

Run on farm5 (read-only):

```bash
bash scripts/phase11e_collect_abuse_restart_readiness_evidence.sh \
  --visibility-bundle-json /path/visibility-bundle-0.1.218.json \
  --visibility-bundle-json-sha256 0cfa19543128954c6774d7ac14646626cd1886ac24895825395fe96612fdc583
```

READY means classifier contract checks passed with explicit evidence. Missing evidence must BLOCK.
This PR does not activate limited-btc-001.
Next step: sync 0.1.219 to farm5, run helper, send outputs for review.
