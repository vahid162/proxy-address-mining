# Phase 11E abuse/restart evidence collection (0.1.220)

- farm5 verified on 0.1.219: pytest 1396 passed, phase gate passed, helper default BLOCKED (expected missing evidence).
- 0.1.220 adds source-backed read-only evidence builders for abuse 1h and restart/container-order evidence.
- Activation remains forbidden even if precheck becomes READY.

```bash
cd /opt/mpf-py-src
sudo bash scripts/phase11e_collect_abuse_restart_readiness_evidence.sh \
  --collect-abuse-evidence \
  --collect-restart-evidence \
  --run-precheck \
  --visibility-bundle-json /tmp/phase11e-runtime-stratum-0.1.214-20260525T152651Z/visibility-bundle-0.1.218.json \
  --visibility-bundle-json-sha256 0cfa19543128954c6774d7ac14646626cd1886ac24895825395fe96612fdc583
```

```bash
cat manifest.json
cat abuse-1h-evidence.json
cat abuse-1h-readiness.json
cat restart-container-order-evidence.json
cat restart-container-order-readiness.json
cat limited-acceptance-precheck.json
cat sha256-manifest.txt
```
