# Capital observability legacy-surface retirement acceptance — 2026-09-21

Standing: ACCEPTED_SOURCE_ONLY

## Identity-preserving source update

- previous qualified source: 2772faf183fe6c1ad94eef96cee777285d537eef
- new qualified source: 71bf084cc140a210a5ec0ce736afeb82ed03ae69
- identity-update merge: 897b57354b419e2d5dbef949f43a476db08461d8
- previous source tree: 377aedd5198a4390a74fbe0df6aa7f761c9efcae
- new source/target tree: 10bec5b631f614987c2e385cc683d21b44f5cc3b
- source ref: refs/heads/migration/monorepo-qualified-source-r7-observability-retirement-20260921
- source bundle SHA-256: f9f64d828ee6bdefe725240adaf47349a5b98f432f69b81c4402a6ab327ee158

## Retirement decision

The old Market-Capital Prometheus compatibility surface is retired because no active current consumer exists.

Live census before retirement found:

- prometheus-node-exporter.service inactive/dead;
- prometheus.service inactive/dead;
- active Network v2 Prometheus on 127.0.0.1:29090;
- no Capital scrape target in active Network v2 Prometheus;
- zero current ordivon_market_capital_* series;
- legacy rule/textfile/drop-in/env present only as stale filesystem state.

Current source therefore removes the old renderer, rule file, Capital-specific node-exporter configuration, and renderer-only tests rather than preserving or dual-writing compatibility aliases.

## Live filesystem retirement

The stale host files were archived before deletion:

- /etc/prometheus/rules/market-capital-crypto.yml
- /etc/systemd/system/prometheus-node-exporter.service.d/20-market-capital-textfile.conf
- /etc/conf.d/prometheus-node-exporter-market-capital
- /var/lib/node_exporter/textfile_collector/market-capital-crypto.prom

Archive root:

/root/ordivon-migration-backups/2026-09-21-capital-observability-retirement-r7/live-stale

Archive tar SHA-256:

895efc42e3f6482ad8ac979e7175328376e48ace0281687804c639221a167b15

Archive manifest SHA-256:

efa8bd675c26b91e71a3ba272a48fb23f1a0a14fc215526d66b839959c59d5d4

After deletion:

- generic Prometheus configuration remained valid;
- generic prometheus.service remained inactive;
- generic prometheus-node-exporter.service remained inactive;
- Network v2 Prometheus remained active and ready;
- query for the legacy metric family still returned zero series;
- no generic package or Network v2 service was retired.

## Deterministic source qualification

- Python 3.14.7: PASS
- Rust 1.98.1: PASS
- pytest: 289 tests / 53 test files PASS
- Ruff: PASS
- dependency and lock consistency: PASS
- old metric prefix in current src/scripts/tools/infra: zero
- R0-R5 bounded non-live closure: PASS
- Trading full-effect closure: PASS
- external financial write attempted: false
- real-money effect attempted: false

The source migration does not alter production authorization. Capital remains NON_LIVE and production external financial writes remain blocked.

## Future rule

If Capital later acquires a real TSDB/PromQL/alert-delivery contract, qualify a fresh domain-correct observability surface. Do not restore the retired Market-Capital metric prefix merely for compatibility.
