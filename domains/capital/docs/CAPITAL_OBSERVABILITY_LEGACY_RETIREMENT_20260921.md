# Capital observability legacy-surface retirement — 2026-09-21

Standing: RETIRED_NO_ACTIVE_CONSUMER

## Finding

The old Market-Capital Prometheus surface was installed on disk but was not part of the active observability chain.

Live census found:

- prometheus-node-exporter.service: inactive/dead;
- prometheus.service: inactive/dead;
- Network v2 Prometheus: active on 127.0.0.1:29090;
- active Network v2 configuration: blackbox-only jobs, no Capital scrape target;
- query for the old Market-Capital metric family: zero series;
- legacy Market-Capital rule file: present on disk but not loaded by the active Network v2 Prometheus;
- legacy Market-Capital textfile: present on disk but its node exporter was inactive.

Therefore the renderer, rules, node-exporter drop-in/env and textfile do not constitute a current consumer contract.

## Decision

Retire the stale compatibility surface rather than rename or dual-write it.

Removed from current source:

- scripts/render-crypto-stream-prometheus
- infra/prometheus/market-capital-crypto.rules.yml
- infra/systemd/prometheus-node-exporter-market-capital.conf
- infra/systemd/prometheus-node-exporter.service.d/20-market-capital-textfile.conf
- the renderer-only test

The current tree emits no old Market-Capital Prometheus metric family.

Prometheus remains a future implementation candidate only. If Capital later needs TSDB retention, PromQL evaluation or alert delivery, it must qualify a fresh domain-correct observability contract instead of restoring the retired names.

## Historical boundary

Dated evidence and historical documentation are not rewritten. The retired filesystem artifacts are archived with hashes before physical deletion.

No Network v2 service, generic Prometheus package, or generic node-exporter package is retired by this decision.
