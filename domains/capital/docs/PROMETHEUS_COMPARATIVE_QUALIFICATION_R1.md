# Prometheus comparative qualification R1 — 2026-09-21

## Question

Does Market Capital currently have an active Prometheus implementation contract that justifies IMPLEMENTATION_OWNER standing?

## Runtime census

Prometheus 3.14.0 is installed and an active Network v2 Prometheus listens on 127.0.0.1:29090. That service is real, but its exact contract is Network v2 blackbox monitoring.

Market-specific deployment evidence is different:

- prometheus-node-exporter package 1.12.1 is installed, but its service is inactive and 127.0.0.1:29100 is not listening.
- /etc/prometheus/prometheus.yml defines a shared Prometheus target on 127.0.0.1:29091, but no process is listening there.
- /var/lib/node_exporter/textfile_collector/market-capital-crypto.prom exists as a historical/static projection.
- /etc/prometheus/rules/market-capital-crypto.yml contains three valid rules and passes promtool check rules.
- The active Network v2 Prometheus reports zero loaded rule groups.
- Direct queries for three representative ordivon_market_capital_* series return zero series from the active Prometheus.

Therefore configuration existence is not deployment evidence.

## Exact current contract

The currently executable Market-domain contract is only:

frozen evidence -> scripts/render-crypto-stream-prometheus -> Prometheus text exposition

The repo also retains deployable candidate rule definitions. It does not currently own a live scrape, TSDB-retention, PromQL-evaluation, or alert-delivery contract.

## Decision

Prometheus 3.14.0 is not a current Market-domain implementation owner.

It remains the preferred mature candidate if Market Capital later activates a real time-series/PromQL/alerting requirement, because those capabilities are materially broader than the current static renderer. Network v2's independent use of Prometheus is unaffected by this Market-domain decision.
