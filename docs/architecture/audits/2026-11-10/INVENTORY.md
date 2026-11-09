# INVENTORY — Ordivon 当前 SourceCut 完整跟踪文件树与角色台账

**基线** `ef17d6879d12faa61fff3bb762b0d500d73c9113`。Git 原生命令 `git ls-files -z` 枚举 **5,002** 个文件。本清单按真实文件读出大小/行数/短 SHA-256、现有 owner manifest 和路径角色启发式机械归类；**不是完整人工语义审计、动态消费者证明或生产安装盘点**。当前审计新增六文件不在初始 SourceCut 清单中。

## 根目录实际 Git 文件分布

| 顶级路径 | tracked 文件数 |
| --- | ---: |
| `services/` | 1,407 |
| `capabilities/` | 1,054 |
| `domains/` | 786 |
| `platform/` | 663 |
| `catalogs/` | 532 |
| `packages/` | 105 |
| `docs/` | 104 |
| `studies/` | 89 |
| `tools/` | 65 |
| `.agents/` | 63 |
| `extensions/` | 47 |
| `apps/` | 46 |
| `profiles/` | 17 |
| `.github/` | 13 |
| `tests/` | 2 |
| `.gitignore/` | 1 |
| `.gitleaksignore/` | 1 |
| `AGENTS.md/` | 1 |
| `CONTRIBUTING.md/` | 1 |
| `LICENSE/` | 1 |
| `README.md/` | 1 |
| `SECURITY.md/` | 1 |
| `mise.toml/` | 1 |
| `renovate.json/` | 1 |

## 21 个自然 Owner — 文件、主入口、schema 刻度

| Owner / 路径 | 文件 | 主角色分布 | 根可核对入口 | 已有验证 |
| --- | ---: | --- | --- | --- |
| **authority-catalog** `catalogs/authorities/` | 376 | config=359, schemas=7, core=5, evidence=2 | `catalogs/authorities/README.md`; `catalogs/authorities/mise.toml`; `catalogs/authorities/pyproject.toml` | `mise run authority-catalog:verify` |
| **capability-catalog** `catalogs/capabilities/` | 77 | docs=56, core=8, evidence=5, tests=4 | `catalogs/capabilities/AGENTS.md`; `catalogs/capabilities/README.md`; `catalogs/capabilities/artifact/README.md`; `catalogs/capabilities/ele/README.md` | `mise run capability-catalog:verify` |
| **composition** `packages/composition/` | 86 | tests=23, config=20, core=18, schemas=13 | `packages/composition/AGENTS.md`; `packages/composition/README.md`; `packages/composition/formal/README.md`; `packages/composition/mise.toml` | `mise run composition:verify` |
| **control-plugin** `extensions/ordivon-control-plane/` | 2 | config=2 | OWNER manifest | `mise run control-plugin:verify` |
| **runtime** `services/runtime/` | 452 | core=151, research=116, tests=49, config=46 | `services/runtime/AGENTS.md`; `services/runtime/Cargo.toml`; `services/runtime/README.md`; `services/runtime/formal/README.md` | `mise run runtime:verify` |
| **host** `services/host/` | 117 | core=56, tests=38, config=10, docs=8 | `services/host/AGENTS.md`; `services/host/README.md`; `services/host/mise.toml`; `services/host/pyproject.toml` | `mise run host:verify` |
| **harness** `services/harness/` | 731 | tests=203, core=168, evidence=129, research=96 | `services/harness/README.md`; `services/harness/formal/README.md`; `services/harness/mise.toml`; `services/harness/pyproject.toml` | `mise run harness:verify` |
| **gateway** `services/gateway/` | 107 | core=43, tests=31, config=26, evidence=4 | `services/gateway/AGENTS.md`; `services/gateway/README.md`; `services/gateway/pyproject.toml` | `mise run gateway:verify` |
| **skills** `extensions/chatgpt-skills-mcp/` | 45 | tests=19, core=12, config=8, docs=4 | `extensions/chatgpt-skills-mcp/README.md`; `extensions/chatgpt-skills-mcp/mise.toml`; `extensions/chatgpt-skills-mcp/pyproject.toml` | `mise run skills:verify` |
| **security** `platform/security/` | 162 | core=71, tests=24, config=23, docs=18 | `platform/security/README.md`; `platform/security/mise.toml`; `platform/security/pyproject.toml` | `mise run security:verify` |
| **workstation** `platform/workstation/` | 265 | core=79, config=72, tests=40, docs=33 | `platform/workstation/README.md`; `platform/workstation/contracts/README.md`; `platform/workstation/inventory/README.md`; `platform/workstation/mise.toml` | `mise run workstation:ci` |
| **network** `platform/network/` | 236 | config=108, core=59, tests=32, docs=31 | `platform/network/AGENTS.md`; `platform/network/README.md`; `platform/network/acceptance/README.md`; `platform/network/capabilities/README.md` | `mise run network:ci` |
| **artifact** `capabilities/artifact/` | 425 | config=155, core=132, tests=72, docs=30 | `capabilities/artifact/README.md`; `capabilities/artifact/artifact-delivery/mise.toml`; `capabilities/artifact/mise.toml`; `capabilities/artifact/pyproject.toml` | `mise run artifact:verify` |
| **distribution** `capabilities/distribution/` | 30 | evidence=15, core=6, config=5, docs=2 | `capabilities/distribution/README.md`; `capabilities/distribution/mise.toml` | `mise run distribution:verify` |
| **media** `capabilities/media/` | 553 | core=115, research=113, config=85, docs=63 | `capabilities/media/AGENTS.md`; `capabilities/media/README.md`; `capabilities/media/creative-library/README.md`; `capabilities/media/formal/README.md` | `mise run media:verify` |
| **preservation** `capabilities/preservation/` | 46 | config=24, other=13, docs=6, core=2 | `capabilities/preservation/README.md` | `mise run preservation:verify` |
| **game** `domains/game/` | 387 | other=188, core=121, media=34, config=18 | `domains/game/AGENTS.md`; `domains/game/README.md`; `domains/game/formal/README.md`; `domains/game/mise.toml` | `mise run game:verify` |
| **capital** `domains/capital/` | 399 | tests=100, other=84, core=79, config=57 | `domains/capital/README.md`; `domains/capital/contracts/README.md`; `domains/capital/formal/README.md`; `domains/capital/mise.toml` | `mise run capital:verify` |
| **data** `packages/data/` | 19 | core=10, docs=6, tests=2, config=1 | `packages/data/AGENTS.md`; `packages/data/README.md`; `packages/data/mise.toml` | `mise run data:verify` |
| **web** `apps/web/` | 35 | core=22, config=6, evidence=3, schemas=2 | `apps/web/README.md`; `apps/web/mise.toml`; `apps/web/package.json` | `mise run web:verify` |
| **chaoxing-autosign** `apps/chaoxing-autosign/` | 11 | core=9, docs=1, tests=1 | `apps/chaoxing-autosign/README.md` | `mise run chaoxing:verify` |

## 实际源码目录树（Git 当前 SourceCut，忽略 .git/node_modules/.venv 等非跟踪缓存）

以下是真实存在、具有跟踪文件的目录树；按路径前缀聚合文件数。每个文件的精确路径在下面 5,002 行清单中。树形结构与文件记录都来自同一个 Git 原生命令；不把生成缓存当仓库源码。

```text
catalogs/authorities/  [376 tracked files]
  ├── evidence/  (2 files)
    ├── acceptance/  (2 files)
  ├── observations/  (182 files)
    ├── acm-sigsoft-benchmarking/  (1 files)
    ├── acm-sigsoft-data-science/  (1 files)
    ├── acm-sigsoft-general/  (1 files)
    ├── acm-sigsoft-replication/  (1 files)
    ├── agent-skills-spec/  (1 files)
    ├── ansi-niso-z39.104-2022-credit/  (1 files)
    ├── apache-arrow-format-1.5/  (1 files)
    ├── apache-beam-programming-model/  (1 files)
    ├── apache-iceberg-1.11.0/  (1 files)
    ├── apache-iceberg-spec-v3/  (1 files)
    ├── apache-parquet-format-2.13.0/  (1 files)
    ├── apalache-0.58.3/  (1 files)
    ├── archimate-3.2/  (1 files)
    ├── archivematica-1.18.0/  (1 files)
    ├── artefactual-fixity-0.8.0/  (1 files)
    ├── asyncapi-3.1.0/  (1 files)
    ├── bitol-odcs-3.2.0/  (1 files)
    ├── bitol-odps-1.1.0/  (1 files)
    ├── c2pa-2.4/  (1 files)
    ├── cloudevents-1.0.2/  (1 files)
    ├── commons-ip-2.11.3/  (1 files)
    ├── coretrustseal-requirements-2026-2028/  (1 files)
    ├── cpmi-iosco-pfmi-2012/  (1 files)
    ├── crossref-metadata-deposit-schema-5.5.0/  (1 files)
    ├── csl-1.0.2/  (1 files)
    ├── cyclonedx-1.7/  (1 files)
    ├── datacite-metadata-schema-4.7/  (1 files)
    ├── debezium-stable-cdc/  (1 files)
    ├── dpc-ram-3/  (1 files)
    ├── e-ark-csip-2.2.0/  (1 files)
    ├── e-ark-sip-2.2.0/  (1 files)
    ├── eark-csip-2.2.0/  (1 files)
    ├── eark-sip-2.2.0/  (1 files)
    ├── emse-submission-guidelines/  (1 files)
    ├── erpnext-budget-provider/  (1 files)
    ├── erpnext-crm-provider/  (1 files)
    ├── fair-principles/  (1 files)
    ├── fix-4.4-errata-20030618/  (1 files)
    ├── frappe-crm-provider/  (1 files)
    ├── frappe-helpdesk-provider/  (1 files)
    ├── frappe-hr-payroll-provider/  (1 files)
    ├── games-user-research-practice/  (1 files)
    ├── godot-provider/  (1 files)
    ├── google-analytics-traffic-source/  (1 files)
    ├── google-search-essentials/  (1 files)
    ├── gsn-3/  (1 files)
    ├── iab-privacy-standards/  (1 files)
    ├── icc-esomar-code-2025/  (1 files)
    ├── icc-marketing-code-2024/  (1 files)
    ├── in-toto-1.0/  (1 files)
    ├── iptc-photo-metadata-2025.1/  (1 files)
    ├── iso-10002-2018/  (2 files)
    ├── iso-10004-2018/  (2 files)
    ├── iso-10005-2018/  (1 files)
    ├── iso-10006-2017/  (1 files)
    ├── iso-14289-2-2024/  (1 files)
    ├── iso-14721-2025/  (1 files)
    ├── iso-15489-1-2016/  (1 files)
    ├── iso-17442-1-2020/  (1 files)
    ├── iso-19005-4-2020/  (1 files)
    ├── iso-19011-2026/  (1 files)
    ├── iso-20022-1-2026/  (1 files)
    ├── iso-20104-2015/  (1 files)
    ├── iso-20252-2026/  (1 files)
    ├── iso-20400-2017/  (1 files)
    ├── iso-20652-2006/  (1 files)
    ├── iso-20671-1-2021/  (1 files)
    ├── iso-21502-2020/  (1 files)
    ├── iso-22301-2019-amd1-2024/  (1 files)
    ├── iso-28500-2017/  (1 files)
    ├── iso-30401-2018-amd1-2022-amd2-2024/  (1 files)
    ├── iso-30405-2023/  (1 files)
    ├── iso-31000-2018/  (1 files)
    ├── iso-32000-2-2020/  (1 files)
    ├── iso-37301-2021/  (1 files)
    ├── iso-37500-2014/  (1 files)
    ├── iso-56001-2024/  (1 files)
    ├── iso-8000-115-2024/  (1 files)
    ├── iso-9001-2015-amd1-2024/  (2 files)
    ├── iso-9001-2026/  (2 files)
    ├── iso-9004-2018/  (1 files)
    ├── iso-9241-11-2018/  (1 files)
    ├── iso-9241-210-2019/  (1 files)
    ├── iso-iec-11179-3-2023/  (1 files)
    ├── iso-iec-11179-3-amd1-2026/  (1 files)
    ├── iso-iec-12113-2022/  (1 files)
    ├── iso-iec-20000-1-2018-amd1-2024/  (2 files)
    ├── iso-iec-25010-2023/  (1 files)
    ├── iso-iec-27001-2022-amd1-2024/  (1 files)
    ├── iso-iec-29500-1-2016/  (1 files)
    ├── iso-iec-42001-2023/  (1 files)
    ├── iso-iec-5259-2-2024/  (1 files)
    ├── iso-iec-ieee-12207-2026/  (1 files)
    ├── iso-iec-ieee-15288-2023/  (1 files)
    ├── iso-iec-ieee-29148-2018/  (1 files)
    ├── iso-integrated-management-systems-guide-2026/  (1 files)
    ├── json-schema-draft-2020-12/  (1 files)
    ├── lean-startup-principles/  (1 files)
    ├── mcp-spec-2026-07-28/  (1 files)
    ├── mets-2/  (1 files)
    ├── mrc-outcomes-data-quality-2022/  (1 files)
    ├── ndsa-levels-digital-preservation-2.1/  (1 files)
    ├── nist-ai-rmf-1.0/  (1 files)
    ├── nist-csf-2.0/  (1 files)
    ├── nist-oscal-1.1.3/  (1 files)
    ├── nist-privacy-framework-1.0/  (1 files)
    ├── nist-sp-800-218-ssdf-1.1/  (1 files)
    ├── nuxmv-2.2.0/  (1 files)
    ├── oasis-opendocument-1.3/  (1 files)
    ├── oasis-sarif-2.1.0/  (1 files)
    ├── oci-distribution-spec-1.1.1/  (1 files)
    ├── oci-image-spec-1.1.1/  (1 files)
    ├── oci-runtime-spec-1.3.0/  (1 files)
    ├── ocra-1.1.2/  (1 files)
    ├── ocra-2.1.0/  (1 files)
    ├── ogc-geopackage-1.4.0/  (1 files)
    ├── omg-bpmn-2.0.2/  (1 files)
    ├── omg-cmmn-1.1/  (1 files)
    ├── omg-dmn-1.5/  (1 files)
    ├── omg-reqif-1.2/  (1 files)
    ├── omg-sacm-2.3/  (1 files)
    ├── openapi-3.2.0/  (1 files)
    ├── openid-connect-core-1.0-errata2/  (1 files)
    ├── openlineage-spec/  (2 files)
    ├── opentelemetry-genai-semconv/  (1 files)
    ├── opentelemetry-spec-1.60.0/  (1 files)
    ├── orcid-id-structure/  (1 files)
    ├── otlp-1.11.0/  (1 files)
    ├── owasp-asvs-5.0.0/  (1 files)
    ├── pacti-0.3.1/  (1 files)
    ├── premis-3.0/  (1 files)
    ├── prisma-2020/  (1 files)
    ├── pronom-registry/  (1 files)
    ├── qudt-units-3.5.1/  (1 files)
    ├── rfc-1034/  (1 files)
    ├── rfc-1035/  (1 files)
    ├── rfc-6749/  (1 files)
    ├── rfc-7858/  (1 files)
    ├── rfc-8310/  (1 files)
    ├── rfc-8414/  (1 files)
    ├── rfc-8484/  (1 files)
    ├── rfc-8493-bagit-1.0/  (1 files)
    ├── rfc-8707/  (1 files)
    ├── rfc-9000/  (1 files)
    ├── rfc-9110/  (1 files)
    ├── rfc-9113/  (1 files)
    ├── rfc-9114/  (1 files)
    ├── rfc-9700/  (1 files)
    ├── rfc-9728/  (1 files)
    ├── rfc-9846/  (1 files)
    ├── ro-crate-1.3/  (1 files)
    ├── roger-martin-strategy-choice-cascade/  (1 files)
    ├── ror-schema-2.1/  (1 files)
    ├── samr-registration-materials-2026/  (1 files)
    ├── sdmx-3.1/  (1 files)
    ├── sdmx-cl-obs-status-2.3/  (1 files)
    ├── slsa-1.2/  (1 files)
    ├── spdx-3.0/  (1 files)
    ├── springer-research-data-policy/  (1 files)
    ├── strategyzer-business-model-canvas/  (1 files)
    ├── strategyzer-value-proposition-canvas/  (1 files)
    ├── stripe-saas-pricing-packaging/  (1 files)
    ├── swhid-scheme-v1/  (1 files)
    ├── tla-tools-1.7.4/  (1 files)
    ├── togaf-standard-10th-edition/  (1 files)
    ├── ucum-spec/  (1 files)
    ├── w3c-dcat-3-2024/  (1 files)
    ├── w3c-odrl-2.2-2018/  (1 files)
    ├── w3c-png-3-2025/  (1 files)
    ├── w3c-prov-o-2013/  (1 files)
    ├── wcag-2.2/  (1 files)
    ├── worldcc-contract-management-standard-4e/  (1 files)
    ├── xbox-accessibility-guidelines-3.2/  (1 files)
    ├── xbrl-2.1/  (1 files)
    ├── yc-essential-startup-advice/  (1 files)
    ├── yc-how-to-sell-2018/  (1 files)
  ├── planning/  (1 files)
  ├── records/  (176 files)
    ├── acm-sigsoft/  (4 files)
    ├── agent-skills/  (1 files)
    ├── apache-arrow/  (1 files)
    ├── apache-beam/  (1 files)
    ├── apache-iceberg/  (2 files)
    ├── apache-parquet/  (1 files)
    ├── apalache-mc/  (1 files)
    ├── artefactual/  (2 files)
    ├── asyncapi/  (1 files)
    ├── bitol/  (2 files)
    ├── c2pa/  (1 files)
    ├── citation-style-language/  (1 files)
    ├── cncf-cloudevents/  (1 files)
    ├── commons-ip/  (1 files)
    ├── coretrustseal/  (1 files)
    ├── cpmi-iosco/  (1 files)
    ├── crossref/  (1 files)
    ├── datacite/  (1 files)
    ├── debezium/  (1 files)
    ├── digital-preservation-coalition/  (1 files)
    ├── dilcis-board/  (2 files)
    ├── dilcis/  (2 files)
    ├── fbk/  (3 files)
    ├── fix-trading/  (1 files)
    ├── frappe/  (5 files)
    ├── games-user-research/  (1 files)
    ├── go-fair/  (1 files)
    ├── godot-engine/  (1 files)
    ├── google/  (2 files)
    ├── iab/  (1 files)
    ├── icc/  (2 files)
    ├── ietf/  (16 files)
    ├── in-toto/  (1 files)
    ├── iptc/  (1 files)
    ├── iso-iec-ieee/  (3 files)
    ├── iso-iec/  (9 files)
    ├── iso/  (33 files)
    ├── json-schema/  (1 files)
    ├── lean-startup/  (1 files)
    ├── linux-foundation/  (1 files)
    ├── loc-premis/  (1 files)
    ├── mets-editorial-board/  (1 files)
    ├── microsoft-xbox/  (1 files)
    ├── model-context-protocol/  (1 files)
    ├── mrc/  (1 files)
    ├── ndsa/  (1 files)
    ├── niso/  (1 files)
    ├── nist/  (5 files)
    ├── oasis/  (2 files)
    ├── oci/  (3 files)
    ├── ogc/  (1 files)
    ├── omg/  (5 files)
    ├── openapi-initiative/  (1 files)
    ├── openid-foundation/  (1 files)
    ├── openlineage/  (1 files)
    ├── opentelemetry/  (3 files)
    ├── orcid/  (1 files)
    ├── owasp-ecma/  (1 files)
    ├── owasp/  (1 files)
    ├── pacti/  (1 files)
    ├── prisma/  (1 files)
    ├── qudt/  (1 files)
    ├── research-object/  (1 files)
    ├── roger-l-martin/  (1 files)
    ├── ror/  (1 files)
    ├── samr/  (1 files)
    ├── scsc/  (1 files)
    ├── sdmx/  (2 files)
    ├── slsa/  (1 files)
    ├── software-heritage/  (1 files)
    ├── springer-nature/  (2 files)
    ├── strategyzer/  (2 files)
    ├── stripe/  (1 files)
    ├── the-open-group/  (2 files)
    ├── tlaplus/  (1 files)
    ├── ucum/  (1 files)
    ├── uk-national-archives/  (1 files)
    ├── w3c/  (5 files)
    ├── worldcc/  (1 files)
    ├── xbrl-international/  (1 files)
    ├── y-combinator/  (2 files)
  ├── schemas/  (3 files)
  ├── scripts/  (5 files)
  ├── tests/  (1 files)
  ├── venues/  (1 files)
catalogs/capabilities/  [77 tracked files]
  ├── artifact/  (1 files)
  ├── docs/  (2 files)
  ├── ele/  (4 files)
  ├── evidence/  (5 files)
    ├── github-radar/  (1 files)
  ├── packages/  (13 files)
  ├── profiles/  (1 files)
  ├── providers/  (36 files)
  ├── routing/  (2 files)
  ├── schemas/  (1 files)
  ├── scripts/  (4 files)
  ├── tests/  (4 files)
packages/composition/  [86 tracked files]
  ├── docs/  (7 files)
  ├── formal/  (16 files)
  ├── planning/  (1 files)
  ├── policies/  (4 files)
    ├── research-adopted-r1/  (4 files)
  ├── profiles/  (2 files)
    ├── admission/  (2 files)
  ├── scripts/  (4 files)
  ├── src/  (24 files)
    ├── ordivon_composition/  (24 files)
      ├── evidence/  (1 files)
      ├── schemas/  (13 files)
  ├── tests/  (23 files)
    ├── fixtures/  (4 files)
      ├── pacti/  (2 files)
extensions/ordivon-control-plane/  [2 tracked files]
services/runtime/  [452 tracked files]
  ├── .config/  (1 files)
  ├── .github/  (7 files)
    ├── ISSUE_TEMPLATE/  (3 files)
    ├── workflows/  (1 files)
  ├── .ordivon/  (3 files)
  ├── crates/  (139 files)
    ├── ordivon-runtime-core/  (115 files)
      ├── migrations/  (6 files)
      ├── sql/  (1 files)
      ├── src/  (104 files)
      ├── tests/  (3 files)
    ├── ordivon-runtime-mcp/  (24 files)
      ├── src/  (22 files)
      ├── tests/  (1 files)
  ├── docs/  (23 files)
    ├── audits/  (2 files)
    ├── evidence/  (1 files)
    ├── guides/  (3 files)
    ├── reference/  (1 files)
  ├── evidence/  (1 files)
  ├── examples/  (4 files)
    ├── runtime-demo/  (4 files)
  ├── formal/  (18 files)
  ├── packaging/  (11 files)
    ├── systemd/  (9 files)
      ├── tmpfiles.d/  (1 files)
    ├── windows/  (2 files)
  ├── planning/  (10 files)
  ├── platform/  (3 files)
    ├── windows/  (3 files)
  ├── research/  (132 files)
    ├── authority/  (7 files)
      ├── publications/  (6 files)
    ├── core/  (10 files)
    ├── engineering/  (4 files)
    ├── foundations/  (71 files)
    ├── programme/  (39 files)
      ├── consumption/  (10 files)
      ├── evidence/  (10 files)
      ├── tools/  (10 files)
  ├── scripts/  (67 files)
    ├── tests/  (34 files)
  ├── sql/  (1 files)
  ├── standards/  (3 files)
  ├── tests/  (7 files)
services/host/  [117 tracked files]
  ├── docs/  (6 files)
  ├── formal/  (3 files)
  ├── migrations/  (15 files)
    ├── versions/  (13 files)
  ├── packaging/  (4 files)
    ├── systemd/  (2 files)
  ├── planning/  (4 files)
  ├── src/  (37 files)
    ├── ordivon_host_v2/  (37 files)
  ├── tests/  (38 files)
  ├── tools/  (1 files)
services/harness/  [731 tracked files]
  ├── .github/  (6 files)
    ├── ISSUE_TEMPLATE/  (3 files)
    ├── workflows/  (1 files)
  ├── .ordivon/  (3 files)
  ├── config/  (11 files)
  ├── containers/  (1 files)
  ├── docs/  (42 files)
    ├── superpowers/  (1 files)
      ├── plans/  (1 files)
  ├── evals/  (48 files)
    ├── fixtures/  (1 files)
    ├── fresh_agent_ab/  (14 files)
    ├── harness-document-retirement-004/  (8 files)
      ├── fixture/  (5 files)
    ├── harness-edit-addressing-002/  (7 files)
      ├── evidence/  (1 files)
      ├── known-invalid/  (1 files)
      ├── oracle/  (1 files)
      ├── verifier/  (1 files)
    ├── harness-edit-multiregion-003/  (9 files)
      ├── evidence/  (1 files)
      ├── known-invalid/  (3 files)
      ├── oracle/  (1 files)
      ├── verifier/  (1 files)
    ├── harness-repository-repair-001/  (8 files)
      ├── evidence/  (1 files)
      ├── known-invalid/  (2 files)
      ├── oracle/  (1 files)
      ├── verifier/  (1 files)
  ├── evidence/  (139 files)
    ├── browser-security/  (26 files)
    ├── system1-decision/  (18 files)
      ├── mind2web-census-r1/  (15 files)
  ├── fixtures/  (10 files)
    ├── harness-edit-addressing-repeated-v1/  (3 files)
    ├── harness-edit-multiregion-v1/  (3 files)
    ├── harness-replacement-repository-repair-v1/  (4 files)
      ├── artifacts/  (1 files)
  ├── formal/  (13 files)
  ├── planning/  (4 files)
  ├── research/  (97 files)
    ├── authority/  (2 files)
      ├── publications/  (1 files)
    ├── experiments/  (17 files)
      ├── browser-security-r3/  (1 files)
      ├── browser-security-r4/  (1 files)
      ├── browser-security-r5/  (1 files)
      ├── browser-security-r7/  (1 files)
      ├── browser-security-r8/  (1 files)
      ├── browser-security-r9/  (1 files)
    ├── fixtures/  (3 files)
  ├── schemas/  (1 files)
    ├── agent-automation/  (1 files)
  ├── scripts/  (87 files)
  ├── src/  (62 files)
    ├── anc_canonical/  (2 files)
    ├── ordivon_harness/  (60 files)
      ├── ordivon/  (24 files)
  ├── systemd/  (14 files)
  ├── tests/  (182 files)
    ├── fixtures/  (2 files)
services/gateway/  [107 tracked files]
  ├── formal/  (18 files)
    ├── evidence/  (4 files)
  ├── packaging/  (12 files)
    ├── windows/  (7 files)
  ├── planning/  (7 files)
  ├── src/  (26 files)
    ├── ordivon_gateway/  (26 files)
  ├── systemd/  (6 files)
    ├── ordivon-gateway.service.d/  (5 files)
  ├── tests/  (31 files)
extensions/chatgpt-skills-mcp/  [45 tracked files]
  ├── config/  (2 files)
  ├── docs/  (3 files)
  ├── planning/  (1 files)
  ├── plugins/  (2 files)
    ├── ordivon-skills-bridge/  (2 files)
  ├── scripts/  (3 files)
  ├── src/  (9 files)
    ├── ordivon_skills/  (9 files)
  ├── systemd/  (1 files)
  ├── tests/  (19 files)
    ├── fixtures/  (3 files)
      ├── agent-plugins-1.0.0/  (3 files)
platform/security/  [162 tracked files]
  ├── .clusterfuzzlite/  (3 files)
  ├── artifacts/  (1 files)
  ├── contracts/  (13 files)
    ├── agent-admission-v1/  (2 files)
    ├── agent-request-verifier-v1/  (11 files)
      ├── evidence/  (1 files)
      ├── patches/  (1 files)
      ├── src/  (1 files)
      ├── test/  (1 files)
  ├── docs/  (15 files)
  ├── fixtures/  (13 files)
    ├── agent-admission/  (1 files)
    ├── browser-security/  (9 files)
    ├── clean/  (2 files)
  ├── formal/  (3 files)
  ├── fuzz/  (1 files)
  ├── labs/  (29 files)
    ├── agent-admission-rs/  (29 files)
      ├── evidence/  (2 files)
      ├── keycloak/  (1 files)
      ├── patches/  (1 files)
      ├── src/  (13 files)
      ├── test/  (3 files)
  ├── planning/  (1 files)
  ├── policies/  (9 files)
  ├── profiles/  (2 files)
    ├── product/  (1 files)
    ├── zap/  (1 files)
  ├── providers/  (2 files)
    ├── packer/  (2 files)
  ├── schemas/  (2 files)
  ├── scripts/  (23 files)
  ├── src/  (14 files)
    ├── ordivon_security_v2/  (14 files)
  ├── tests/  (24 files)
    ├── fixtures/  (5 files)
      ├── signed-vsa-r2/  (5 files)
  ├── threat-models/  (1 files)
platform/workstation/  [265 tracked files]
  ├── ansible/  (20 files)
  ├── contracts/  (6 files)
    ├── asyncapi/  (3 files)
    ├── cloudevents/  (1 files)
    ├── outbox/  (1 files)
  ├── docs/  (16 files)
  ├── evidence/  (2 files)
  ├── grafana/  (2 files)
  ├── host/  (3 files)
  ├── inventory/  (12 files)
    ├── queries/  (6 files)
    ├── snapshots/  (1 files)
  ├── manifests/  (1 files)
  ├── n8n/  (6 files)
    ├── workflows/  (2 files)
  ├── observability/  (12 files)
    ├── gatus/  (2 files)
  ├── policy/  (1 files)
  ├── postgresql/  (4 files)
  ├── providers/  (58 files)
    ├── cloudflare/  (58 files)
      ├── config/  (1 files)
      ├── deploy/  (2 files)
      ├── docs/  (4 files)
      ├── scripts/  (13 files)
      ├── src/  (19 files)
      ├── test/  (9 files)
  ├── scripts/  (13 files)
  ├── systemd/  (6 files)
    ├── service-profiles/  (3 files)
      ├── loki.service.d/  (1 files)
      ├── netdata.service.d/  (1 files)
      ├── vector.service.d/  (1 files)
  ├── tempo/  (1 files)
  ├── temporal/  (2 files)
  ├── tests/  (40 files)
  ├── tofu/  (9 files)
    ├── agent-birth-handoff/  (8 files)
  ├── tools/  (1 files)
  ├── windows/  (4 files)
  ├── workstation/  (40 files)
    ├── nix/  (7 files)
      ├── codex-cli/  (4 files)
      ├── nix/  (1 files)
    ├── providers/  (18 files)
      ├── acceptance/  (3 files)
      ├── authority_validation/  (2 files)
      ├── d_drive_compact/  (5 files)
      ├── windows_wsl/  (2 files)
      ├── windows_wsl_service/  (2 files)
    ├── windows/  (7 files)
platform/network/  [236 tracked files]
  ├── .github/  (1 files)
  ├── acceptance/  (16 files)
    ├── connectivity/  (2 files)
    ├── dns/  (1 files)
    ├── egress/  (3 files)
    ├── fault/  (1 files)
    ├── full-ip/  (1 files)
    ├── lifecycle/  (2 files)
    ├── observability/  (3 files)
    ├── protocol/  (1 files)
    ├── topology/  (1 files)
  ├── capabilities/  (6 files)
    ├── failover/  (2 files)
      ├── acceptance/  (1 files)
    ├── wireguard/  (3 files)
      ├── acceptance/  (1 files)
      ├── external/  (1 files)
  ├── config/  (10 files)
    ├── blackbox/  (1 files)
    ├── prometheus/  (7 files)
      ├── consumers/  (5 files)
    ├── sing-box/  (1 files)
    ├── sysctl/  (1 files)
  ├── consumers/  (105 files)
    ├── browserless/  (11 files)
      ├── acceptance/  (2 files)
      ├── config/  (1 files)
      ├── systemd/  (4 files)
    ├── chat-ingress/  (7 files)
      ├── config/  (2 files)
      ├── systemd/  (3 files)
    ├── claude/  (11 files)
      ├── config/  (2 files)
      ├── systemd/  (6 files)
    ├── codex/  (14 files)
      ├── config/  (1 files)
      ├── systemd/  (3 files)
    ├── developer-egress/  (3 files)
    ├── discord/  (7 files)
      ├── config/  (2 files)
      ├── systemd/  (2 files)
    ├── finance/  (15 files)
      ├── config/  (10 files)
      ├── systemd/  (2 files)
    ├── mobile-tailnet-exit/  (5 files)
      ├── systemd/  (1 files)
    ├── model-provider/  (7 files)
      ├── config/  (2 files)
      ├── systemd/  (2 files)
    ├── supply-chain/  (9 files)
      ├── acceptance/  (1 files)
      ├── config/  (2 files)
      ├── systemd/  (3 files)
    ├── windows-real-chrome/  (8 files)
      ├── config/  (2 files)
      ├── systemd/  (3 files)
    ├── x-reality/  (7 files)
      ├── config/  (2 files)
      ├── systemd/  (2 files)
  ├── docs/  (5 files)
  ├── evidence/  (3 files)
  ├── formal/  (6 files)
    ├── fixtures/  (1 files)
  ├── planning/  (2 files)
  ├── providers/  (20 files)
    ├── gluetun/  (11 files)
      ├── config/  (1 files)
      ├── quadlet/  (2 files)
      ├── systemd/  (4 files)
    ├── surfshark/  (5 files)
      ├── acceptance/  (1 files)
      ├── config/  (1 files)
      ├── external/  (1 files)
    ├── zte-u30pro/  (3 files)
  ├── reference/  (9 files)
    ├── linux/  (9 files)
      ├── containerlab/  (1 files)
      ├── workflows/  (1 files)
  ├── scripts/  (2 files)
  ├── substrates/  (8 files)
    ├── shared-egress/  (8 files)
      ├── systemd/  (3 files)
  ├── systemd/  (5 files)
  ├── tests/  (32 files)
capabilities/artifact/  [425 tracked files]
  ├── artifact-delivery/  (180 files)
    ├── consumer-acceptance/  (9 files)
    ├── examples/  (14 files)
    ├── golden/  (14 files)
      ├── pdu-sdu-34x10-r1/  (12 files)
    ├── node/  (6 files)
    ├── openxml-nix/  (2 files)
    ├── openxml-validator/  (2 files)
    ├── policy/  (1 files)
    ├── python-uv/  (3 files)
    ├── shadow-bindings/  (20 files)
    ├── shadow-contracts/  (36 files)
      ├── game-station-zero-ogg-vorbis-r1/  (3 files)
    ├── shadow-profiles/  (20 files)
    ├── shadow-v2/  (29 files)
      ├── examples/  (28 files)
    ├── verification/  (1 files)
  ├── artifact_capabilities/  (22 files)
    ├── presentation/  (7 files)
    ├── publication/  (11 files)
  ├── artifact_core/  (11 files)
  ├── artifact_evidence/  (3 files)
  ├── artifact_operations/  (8 files)
    ├── providers/  (4 files)
  ├── artifact_trust/  (7 files)
  ├── artifact_verification/  (9 files)
    ├── formal/  (3 files)
  ├── artifact_verifiers/  (21 files)
    ├── document/  (4 files)
    ├── openxml/  (3 files)
    ├── pdf/  (4 files)
    ├── presentation/  (4 files)
    ├── web/  (5 files)
      ├── node/  (1 files)
  ├── config/  (2 files)
    ├── zot/  (1 files)
  ├── docs/  (28 files)
  ├── planning/  (10 files)
    ├── prototypes/  (4 files)
  ├── scripts/  (43 files)
  ├── systemd/  (2 files)
  ├── tests/  (72 files)
    ├── fixtures/  (2 files)
      ├── cad/  (2 files)
capabilities/distribution/  [30 tracked files]
  ├── adapters/  (3 files)
  ├── docs/  (1 files)
  ├── evidence/  (15 files)
  ├── scripts/  (6 files)
  ├── tests/  (1 files)
    ├── fixtures/  (1 files)
capabilities/media/  [553 tracked files]
  ├── apps/  (19 files)
    ├── motion-remotion/  (13 files)
      ├── src/  (10 files)
    ├── preview/  (6 files)
      ├── src/  (3 files)
  ├── artifacts/  (16 files)
    ├── creative-archive/  (1 files)
    ├── creative-library/  (15 files)
      ├── derived/  (10 files)
      ├── evidence/  (4 files)
  ├── creative-library/  (5 files)
    ├── web/  (3 files)
  ├── docs/  (16 files)
    ├── resolve-compatibility/  (3 files)
  ├── formal/  (6 files)
  ├── packages/  (6 files)
    ├── identity/  (3 files)
      ├── scripts/  (1 files)
      ├── tokens/  (1 files)
    ├── visuals/  (3 files)
      ├── src/  (2 files)
  ├── planning/  (1 files)
  ├── play/  (6 files)
    ├── media-ecology-20260830/  (6 files)
  ├── processing/  (16 files)
    ├── bin/  (6 files)
    ├── profiles/  (4 files)
    ├── tests/  (5 files)
  ├── productions/  (213 files)
    ├── archive-archipelago-001/  (57 files)
      ├── evidence/  (30 files)
      ├── interactive/  (12 files)
      ├── render/  (7 files)
      ├── source/  (2 files)
    ├── browser-perception-note/  (5 files)
      ├── evidence/  (1 files)
    ├── convergence-object-001/  (15 files)
      ├── render/  (2 files)
      ├── source/  (2 files)
    ├── convergence-sonic-ident/  (13 files)
      ├── render/  (5 files)
    ├── fishing-fable-lego-study-r1/  (6 files)
    ├── friction-loop-field-zine/  (9 files)
      ├── inspect/  (1 files)
      ├── render/  (1 files)
    ├── live-relay-001/  (30 files)
      ├── artifact-evidence/  (5 files)
      ├── evidence/  (5 files)
      ├── program/  (4 files)
      ├── render/  (3 files)
      ├── source/  (6 files)
    ├── mhs-hardware-boundary/  (9 files)
      ├── evidence/  (5 files)
    ├── ordivon-book-v0/  (18 files)
      ├── portable/  (2 files)
    ├── ordivon-system-constellation-atlas/  (12 files)
      ├── render/  (3 files)
      ├── source/  (2 files)
    ├── runtime-introduction/  (25 files)
      ├── evidence/  (6 files)
      ├── history/  (1 files)
      ├── script/  (2 files)
      ├── timed-text/  (5 files)
      ├── timeline/  (4 files)
    ├── site-social-card/  (7 files)
      ├── output/  (1 files)
      ├── source/  (1 files)
    ├── studio-expression-card/  (7 files)
      ├── output/  (1 files)
      ├── source/  (1 files)
  ├── research/  (110 files)
    ├── equipment/  (13 files)
      ├── evidence/  (4 files)
      ├── experiments/  (5 files)
    ├── expression/  (69 files)
      ├── evidence/  (6 files)
      ├── experiments/  (10 files)
      ├── foundations/  (33 files)
      ├── profiles/  (7 files)
    ├── media/  (28 files)
      ├── authority/  (3 files)
      ├── bridges/  (1 files)
      ├── core/  (2 files)
      ├── coverage/  (1 files)
      ├── derived/  (4 files)
      ├── engineering-consumption/  (12 files)
      ├── evidence/  (1 files)
      ├── history/  (1 files)
      ├── negative/  (1 files)
  ├── schemas/  (6 files)
  ├── scripts/  (21 files)
  ├── src/  (70 files)
    ├── ordivon_studio/  (70 files)
      ├── cli_handlers/  (4 files)
      ├── ecology/  (5 files)
      ├── research/  (16 files)
  ├── tests/  (26 files)
capabilities/preservation/  [46 tracked files]
  ├── artifacts/  (32 files)
    ├── creative-preservation/  (32 files)
      ├── archivematica-r6/  (1 files)
      ├── closeout-r10/  (1 files)
      ├── forward-r1/  (1 files)
      ├── forward-r2/  (3 files)
      ├── operations-r7/  (1 files)
      ├── pilot-r1/  (23 files)
      ├── retirement-r9/  (1 files)
      ├── standards-r8/  (1 files)
  ├── config/  (1 files)
  ├── docs/  (5 files)
  ├── planning/  (1 files)
  ├── scripts/  (3 files)
  ├── systemd/  (2 files)
domains/game/  [387 tracked files]
  ├── .ordivon/  (1 files)
  ├── docs/  (6 files)
  ├── examples/  (333 files)
    ├── beacon-relay/  (59 files)
      ├── art/  (24 files)
      ├── fonts/  (4 files)
      ├── screenshots/  (2 files)
    ├── kenney-visual-composition/  (11 files)
      ├── assets/  (4 files)
    ├── native-composition/  (19 files)
      ├── assets/  (5 files)
      ├── configs/  (2 files)
    ├── orbit-collector/  (6 files)
      ├── src/  (3 files)
    ├── room-encounter/  (238 files)
      ├── addons/  (190 files)
      ├── assets/  (6 files)
      ├── configs/  (3 files)
      ├── narrative/  (9 files)
  ├── formal/  (3 files)
  ├── knowledge/  (7 files)
  ├── planning/  (1 files)
  ├── research/  (7 files)
    ├── autonomous-interest-r7/  (7 files)
  ├── scripts/  (8 files)
  ├── src/  (4 files)
  ├── test/  (9 files)
domains/capital/  [399 tracked files]
  ├── artifacts/  (1 files)
  ├── config/  (28 files)
  ├── contracts/  (12 files)
    ├── legacy_protocol_v1/  (4 files)
  ├── data-products/  (4 files)
    ├── crypto-public-shadow-r2/  (4 files)
  ├── destroyer/  (1 files)
  ├── docs/  (19 files)
  ├── evidence/  (26 files)
    ├── acceptance/  (7 files)
    ├── data-products/  (3 files)
      ├── crypto-public-shadow-consumption-r1/  (3 files)
    ├── finance-research/  (5 files)
      ├── spy-shy-forward-20261108/  (5 files)
  ├── examples/  (5 files)
  ├── fixtures/  (4 files)
    ├── r5_legacy_bounded/  (4 files)
  ├── formal/  (17 files)
  ├── infra/  (2 files)
    ├── systemd/  (1 files)
  ├── planning/  (1 files)
  ├── schema/  (3 files)
    ├── legacy_protocol_v1/  (1 files)
  ├── scripts/  (50 files)
  ├── src/  (65 files)
    ├── ordivon_capital/  (65 files)
      ├── accounting/  (6 files)
      ├── governance/  (2 files)
      ├── markets/  (12 files)
      ├── portfolio/  (10 files)
      ├── research/  (13 files)
      ├── risk/  (9 files)
      ├── trading/  (12 files)
  ├── tests/  (100 files)
  ├── tools/  (53 files)
    ├── jsonschema_4_26_0/  (4 files)
    ├── legacy_replay/  (13 files)
      ├── lean_wave_b/  (12 files)
    ├── nautilus_rc4/  (16 files)
      ├── config/  (3 files)
    ├── okx_official_cli/  (3 files)
    ├── opa_1_20_2/  (2 files)
    ├── qualification/  (2 files)
    ├── quickfixn_1_14_1/  (4 files)
      ├── fix44-projector/  (3 files)
    ├── tigerbeetle_0_17_9/  (8 files)
      ├── ordivon_capital/  (4 files)
      ├── replay/  (3 files)
  ├── wave_b/  (1 files)
    ├── fixtures/  (1 files)
packages/data/  [19 tracked files]
  ├── docs/  (4 files)
  ├── formal/  (3 files)
  ├── scripts/  (2 files)
  ├── src/  (5 files)
    ├── ordivon_data/  (5 files)
  ├── tests/  (2 files)
apps/web/  [35 tracked files]
  ├── evidence/  (3 files)
  ├── planning/  (1 files)
  ├── src/  (15 files)
  ├── test/  (7 files)
apps/chaoxing-autosign/  [11 tracked files]
  ├── chaoxing_mvp/  (9 files)
  ├── tests/  (1 files)
Non-owner source regions:
├── docs/ (104 tracked files)
├── tools/ (65 tracked files)
├── studies/ (89 tracked files)
├── profiles/ (17 tracked files)
├── .github/ (13 tracked files)
├── .agents/ (63 tracked files)
├── tests/ (2 tracked files)
├── apps/ (46 tracked files)
├── packages/ (105 tracked files)
```

## 自然 Owner 的 README schema/lifecycle 声明与现有验证入口

这是直接解析根 README YAML frontmatter 的元数据，无 frontmatter 标成 `—`，**不是不符合**。Host PG `journalSchema=13` 属于独立线上观测，不在本表混入文件 `schema_version`。

| Owner | root README | frontmatter schema_version | lifecycle | source_role | verify task |
| --- | --- | --- | --- | --- | --- |
| authority-catalog | `catalogs/authorities/README.md` present | — | — | — | `authority-catalog:verify` |
| capability-catalog | `catalogs/capabilities/README.md` present | — | — | — | `capability-catalog:verify` |
| composition | `packages/composition/README.md` present | — | — | — | `composition:verify` |
| control-plugin | `extensions/ordivon-control-plane/README.md` absent | — | — | — | `control-plugin:verify` |
| runtime | `services/runtime/README.md` present | 1 | active | canonical | `runtime:verify` |
| host | `services/host/README.md` present | — | — | — | `host:verify` |
| harness | `services/harness/README.md` present | 1 | active | canonical | `harness:verify` |
| gateway | `services/gateway/README.md` present | — | — | — | `gateway:verify` |
| skills | `extensions/chatgpt-skills-mcp/README.md` present | — | — | — | `skills:verify` |
| security | `platform/security/README.md` present | — | — | — | `security:verify` |
| workstation | `platform/workstation/README.md` present | — | — | — | `workstation:ci` |
| network | `platform/network/README.md` present | — | — | — | `network:ci` |
| artifact | `capabilities/artifact/README.md` present | — | — | — | `artifact:verify` |
| distribution | `capabilities/distribution/README.md` present | — | — | — | `distribution:verify` |
| media | `capabilities/media/README.md` present | — | — | — | `media:verify` |
| preservation | `capabilities/preservation/README.md` present | — | — | — | `preservation:verify` |
| game | `domains/game/README.md` present | 1 | active | canonical | `game:verify` |
| capital | `domains/capital/README.md` present | — | — | — | `capital:verify` |
| data | `packages/data/README.md` present | — | — | — | `data:verify` |
| web | `apps/web/README.md` present | — | — | — | `web:verify` |
| chaoxing-autosign | `apps/chaoxing-autosign/README.md` present | — | — | — | `chaoxing:verify` |

## schema_version/lifecycle 语义说明

README/frontmatter 的 schema_version 是文件/文档结构合同，不是数据库 schema。JSON 文件的 schemaVersion 是**各对象自属**的版本；没有统一的 repo-global schemaVersion。各 Owner 的当前状态必须从其 README、manifest、相应 schema 和已部署实例分别核实。没有找到 frontmatter 的 README 不是自动不合格。

## 精确文件逐项清单（机械检测）

字段解释：`role` 为路径+文件类型启发式；`lines` 仅文本类型；`sha12` 为文件内容 SHA-256 前 12 位，不是来源证明；`schema` 仅一级 JSON/schema 文档声明。此表**不**提供删文件许可；实际入边/动态消费者需要 Phase2 求证。

### authority-catalog — catalogs/authorities/（376 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `catalogs/authorities/.gitignore` | other | 114 | — | `37e0da5f5fec` |  |
| `catalogs/authorities/README.md` | docs | 5928 | 106 | `614130d9081a` |  |
| `catalogs/authorities/evidence/acceptance/authority-catalog-seed-closure-20260914.json` | evidence | 4361 | 93 | `12c38de010b3` | 1 |
| `catalogs/authorities/evidence/acceptance/enterprise-operating-model-r1-dogfood-20260914.json` | evidence | 6657 | 187 | `5b5165267418` | 1 |
| `catalogs/authorities/mise.toml` | config | 599 | 18 | `e5f61ab836f3` |  |
| `catalogs/authorities/observations/acm-sigsoft-benchmarking/2026-09-14.json` | config | 351 | 11 | `a6d21758471b` | 1 |
| `catalogs/authorities/observations/acm-sigsoft-data-science/2026-09-14.json` | config | 351 | 11 | `96dcdb85ffe2` | 1 |
| `catalogs/authorities/observations/acm-sigsoft-general/2026-09-14.json` | config | 346 | 11 | `9a667380d3c7` | 1 |
| `catalogs/authorities/observations/acm-sigsoft-replication/2026-09-14.json` | config | 350 | 11 | `2c91ea4b3ed7` | 1 |
| `catalogs/authorities/observations/agent-skills-spec/2026-09-14.json` | config | 419 | 11 | `540c97dff9e3` | 1 |
| `catalogs/authorities/observations/ansi-niso-z39.104-2022-credit/2026-09-14.json` | config | 431 | 11 | `5605f878a726` | 1 |
| `catalogs/authorities/observations/apache-arrow-format-1.5/2026-09-14.json` | config | 335 | 11 | `5dcf51c1b675` | 1 |
| `catalogs/authorities/observations/apache-beam-programming-model/2026-09-20.json` | config | 551 | 11 | `fa83bf59ee7d` | 1 |
| `catalogs/authorities/observations/apache-iceberg-1.11.0/2026-09-20.json` | config | 395 | 11 | `ea65966068cc` | 1 |
| `catalogs/authorities/observations/apache-iceberg-spec-v3/2026-09-20.json` | config | 447 | 11 | `df6bec0b97a5` | 1 |
| `catalogs/authorities/observations/apache-parquet-format-2.13.0/2026-09-14.json` | config | 340 | 11 | `1509724a8e89` | 1 |
| `catalogs/authorities/observations/apalache-0.58.3/2026-09-22.json` | config | 488 | 11 | `fdc9dfe7dbb9` | 1 |
| `catalogs/authorities/observations/archimate-3.2/2026-09-14.json` | config | 427 | 11 | `e0e8c92ad65f` | 1 |
| `catalogs/authorities/observations/archivematica-1.18.0/2026-09-20.json` | config | 501 | 11 | `4faf0c67851f` | 1 |
| `catalogs/authorities/observations/artefactual-fixity-0.8.0/2026-09-20.json` | config | 474 | 11 | `aaaba5302a60` | 1 |
| `catalogs/authorities/observations/asyncapi-3.1.0/2026-09-14.json` | config | 435 | 11 | `400bb66397ee` | 1 |
| `catalogs/authorities/observations/bitol-odcs-3.2.0/2026-09-20.json` | config | 481 | 11 | `505e1f686fb6` | 1 |
| `catalogs/authorities/observations/bitol-odps-1.1.0/2026-09-20.json` | config | 481 | 11 | `1333545023bb` | 1 |
| `catalogs/authorities/observations/c2pa-2.4/2026-09-14.json` | config | 423 | 11 | `607eceb50a16` | 1 |
| `catalogs/authorities/observations/cloudevents-1.0.2/2026-09-14.json` | config | 348 | 11 | `a3ecc08abb1a` | 1 |
| `catalogs/authorities/observations/commons-ip-2.11.3/2026-09-20.json` | config | 432 | 11 | `8f475ee813d6` | 1 |
| `catalogs/authorities/observations/coretrustseal-requirements-2026-2028/2026-09-14.json` | config | 442 | 11 | `0e739f5b48f0` | 1 |
| `catalogs/authorities/observations/cpmi-iosco-pfmi-2012/2026-09-14.json` | config | 500 | 11 | `a30a91db2097` | 1 |
| `catalogs/authorities/observations/crossref-metadata-deposit-schema-5.5.0/2026-09-14.json` | config | 493 | 11 | `c8a40e094215` | 1 |
| `catalogs/authorities/observations/csl-1.0.2/2026-09-14.json` | config | 484 | 11 | `746a7f8778c3` | 1 |
| `catalogs/authorities/observations/cyclonedx-1.7/2026-09-14.json` | config | 472 | 11 | `40bbce4fe1ff` | 1 |
| `catalogs/authorities/observations/datacite-metadata-schema-4.7/2026-09-14.json` | config | 420 | 11 | `ec9c24afc475` | 1 |
| `catalogs/authorities/observations/debezium-stable-cdc/2026-09-20.json` | config | 621 | 11 | `8684e3aebb1f` | 1 |
| `catalogs/authorities/observations/dpc-ram-3/2026-09-14.json` | config | 426 | 11 | `6fc135dc313b` | 1 |
| `catalogs/authorities/observations/e-ark-csip-2.2.0/2026-09-14.json` | config | 377 | 11 | `aa84dfed7bae` | 1 |
| `catalogs/authorities/observations/e-ark-sip-2.2.0/2026-09-14.json` | config | 374 | 11 | `599e1686435b` | 1 |
| `catalogs/authorities/observations/eark-csip-2.2.0/2026-09-20.json` | config | 417 | 11 | `4081c3bd65ec` | 1 |
| `catalogs/authorities/observations/eark-sip-2.2.0/2026-09-20.json` | config | 436 | 11 | `4e304482fc00` | 1 |
| `catalogs/authorities/observations/emse-submission-guidelines/2026-09-14.json` | config | 356 | 11 | `f7f9da3e2634` | 1 |
| `catalogs/authorities/observations/erpnext-budget-provider/2026-09-19.json` | config | 470 | 11 | `3fe95a5d6534` | 1 |
| `catalogs/authorities/observations/erpnext-crm-provider/2026-09-19.json` | config | 525 | 11 | `7745fd6f2177` | 1 |
| `catalogs/authorities/observations/fair-principles/2026-09-14.json` | config | 324 | 11 | `1bd081df12c8` | 1 |
| `catalogs/authorities/observations/fix-4.4-errata-20030618/2026-09-14.json` | config | 541 | 11 | `46e9c6de404e` | 1 |
| `catalogs/authorities/observations/frappe-crm-provider/2026-09-19.json` | config | 408 | 11 | `6bc83684138a` | 1 |
| `catalogs/authorities/observations/frappe-helpdesk-provider/2026-09-19.json` | config | 480 | 11 | `ad58ebd8ff17` | 1 |
| `catalogs/authorities/observations/frappe-hr-payroll-provider/2026-09-19.json` | config | 510 | 11 | `2d375ed8ce76` | 1 |
| `catalogs/authorities/observations/games-user-research-practice/2026-09-14.json` | config | 360 | 11 | `abc2f4b60b24` | 1 |
| `catalogs/authorities/observations/godot-provider/2026-09-14.json` | config | 447 | 11 | `c7dbb589a1c5` | 1 |
| `catalogs/authorities/observations/google-analytics-traffic-source/2026-09-19.json` | config | 552 | 11 | `aaeab8dc9c75` | 1 |
| `catalogs/authorities/observations/google-search-essentials/2026-09-19.json` | config | 574 | 11 | `9ca0d28385e1` | 1 |
| `catalogs/authorities/observations/gsn-3/2026-09-22.json` | config | 388 | 11 | `271fe9482a2e` | 1 |
| `catalogs/authorities/observations/iab-privacy-standards/2026-09-19.json` | config | 611 | 11 | `855ce03ea45f` | 1 |
| `catalogs/authorities/observations/icc-esomar-code-2025/2026-09-19.json` | config | 614 | 11 | `365d6c13ce17` | 1 |
| `catalogs/authorities/observations/icc-marketing-code-2024/2026-09-19.json` | config | 593 | 11 | `6497374a067f` | 1 |
| `catalogs/authorities/observations/in-toto-1.0/2026-09-14.json` | config | 393 | 11 | `8f0ffc164037` | 1 |
| `catalogs/authorities/observations/iptc-photo-metadata-2025.1/2026-09-14.json` | config | 374 | 11 | `21a4de4906f5` | 1 |
| `catalogs/authorities/observations/iso-10002-2018/2026-09-14.json` | config | 326 | 11 | `496d58654979` | 1 |
| `catalogs/authorities/observations/iso-10002-2018/2026-09-19.json` | config | 421 | 11 | `e9f7929d9908` | 1 |
| `catalogs/authorities/observations/iso-10004-2018/2026-09-14.json` | config | 326 | 11 | `fc9376e0ff59` | 1 |
| `catalogs/authorities/observations/iso-10004-2018/2026-09-19.json` | config | 421 | 11 | `f445f2a01b7b` | 1 |
| `catalogs/authorities/observations/iso-10005-2018/2026-09-14.json` | config | 326 | 11 | `86b86b82e0cd` | 1 |
| `catalogs/authorities/observations/iso-10006-2017/2026-09-14.json` | config | 326 | 11 | `fa447482c16c` | 1 |
| `catalogs/authorities/observations/iso-14289-2-2024/2026-09-14.json` | config | 318 | 11 | `24dd7409573c` | 1 |
| `catalogs/authorities/observations/iso-14721-2025/2026-09-14.json` | config | 346 | 11 | `73aef357ad2a` | 1 |
| `catalogs/authorities/observations/iso-15489-1-2016/2026-09-20.json` | config | 547 | 11 | `334fe296ebde` | 1 |
| `catalogs/authorities/observations/iso-17442-1-2020/2026-09-14.json` | config | 379 | 11 | `91c27061e9c2` | 1 |
| `catalogs/authorities/observations/iso-19005-4-2020/2026-09-14.json` | config | 418 | 11 | `265dfa15c815` | 1 |
| `catalogs/authorities/observations/iso-19011-2026/2026-09-14.json` | config | 321 | 11 | `00dd824369a7` | 1 |
| `catalogs/authorities/observations/iso-20022-1-2026/2026-09-14.json` | config | 448 | 11 | `4f202b4d63a0` | 1 |
| `catalogs/authorities/observations/iso-20104-2015/2026-09-14.json` | config | 379 | 11 | `f61c1cd5c498` | 1 |
| `catalogs/authorities/observations/iso-20252-2026/2026-09-19.json` | config | 538 | 11 | `124de744ee47` | 1 |
| `catalogs/authorities/observations/iso-20400-2017/2026-09-19.json` | config | 421 | 11 | `1e65a04d3f8f` | 1 |
| `catalogs/authorities/observations/iso-20652-2006/2026-09-14.json` | config | 377 | 11 | `4195badb683d` | 1 |
| `catalogs/authorities/observations/iso-20671-1-2021/2026-09-19.json` | config | 447 | 11 | `1c3c7dcecd97` | 1 |
| `catalogs/authorities/observations/iso-21502-2020/2026-09-14.json` | config | 326 | 11 | `de02a82f6ca0` | 1 |
| `catalogs/authorities/observations/iso-22301-2019-amd1-2024/2026-09-14.json` | config | 459 | 11 | `8f1a0e781db5` | 1 |
| `catalogs/authorities/observations/iso-28500-2017/2026-09-14.json` | config | 392 | 11 | `d4f139dde0b5` | 1 |
| `catalogs/authorities/observations/iso-30401-2018-amd1-2022-amd2-2024/2026-09-14.json` | config | 545 | 11 | `d6dbe2b5d422` | 1 |
| `catalogs/authorities/observations/iso-30405-2023/2026-09-19.json` | config | 411 | 11 | `c0c991496109` | 1 |
| `catalogs/authorities/observations/iso-31000-2018/2026-09-14.json` | config | 326 | 11 | `5f7ede93d5ee` | 1 |
| `catalogs/authorities/observations/iso-32000-2-2020/2026-09-14.json` | config | 380 | 11 | `b9fcc91a003e` | 1 |
| `catalogs/authorities/observations/iso-37301-2021/2026-09-14.json` | config | 326 | 11 | `d2ca1ff7e4b9` | 1 |
| `catalogs/authorities/observations/iso-37500-2014/2026-09-19.json` | config | 395 | 11 | `f4401dff1249` | 1 |
| `catalogs/authorities/observations/iso-56001-2024/2026-09-14.json` | config | 352 | 11 | `e2cb8e679cfb` | 1 |
| `catalogs/authorities/observations/iso-8000-115-2024/2026-09-20.json` | config | 473 | 11 | `879bc850c8b4` | 1 |
| `catalogs/authorities/observations/iso-9001-2015-amd1-2024/2026-09-14.json` | config | 463 | 11 | `d58bd2470d03` | 1 |
| `catalogs/authorities/observations/iso-9001-2015-amd1-2024/2026-09-19.json` | config | 448 | 11 | `637f2b1c54e1` | 1 |
| `catalogs/authorities/observations/iso-9001-2026/2026-09-14.json` | config | 430 | 11 | `92f4d2c0928a` | 1 |
| `catalogs/authorities/observations/iso-9001-2026/2026-09-19.json` | config | 388 | 11 | `412d8a49af5e` | 1 |
| `catalogs/authorities/observations/iso-9004-2018/2026-09-14.json` | config | 325 | 11 | `1e7d4250739b` | 1 |
| `catalogs/authorities/observations/iso-9241-11-2018/2026-09-14.json` | config | 328 | 11 | `caede7c2e673` | 1 |
| `catalogs/authorities/observations/iso-9241-210-2019/2026-09-14.json` | config | 329 | 11 | `cc2c0e28ef73` | 1 |
| `catalogs/authorities/observations/iso-iec-11179-3-2023/2026-09-20.json` | config | 449 | 11 | `b645169123bf` | 1 |
| `catalogs/authorities/observations/iso-iec-11179-3-amd1-2026/2026-09-20.json` | config | 386 | 11 | `f079d1b62f3b` | 1 |
| `catalogs/authorities/observations/iso-iec-12113-2022/2026-09-14.json` | config | 320 | 11 | `593e8a088440` | 1 |
| `catalogs/authorities/observations/iso-iec-20000-1-2018-amd1-2024/2026-09-14.json` | config | 413 | 11 | `8afe623afa0a` | 1 |
| `catalogs/authorities/observations/iso-iec-20000-1-2018-amd1-2024/2026-09-19.json` | config | 513 | 11 | `04746ef9626b` | 1 |
| `catalogs/authorities/observations/iso-iec-25010-2023/2026-09-14.json` | config | 330 | 11 | `74e07fba0f2e` | 1 |
| `catalogs/authorities/observations/iso-iec-27001-2022-amd1-2024/2026-09-14.json` | config | 402 | 11 | `73e1336e0fe4` | 1 |
| `catalogs/authorities/observations/iso-iec-29500-1-2016/2026-09-14.json` | config | 439 | 11 | `6f33aeeb4d58` | 1 |
| `catalogs/authorities/observations/iso-iec-42001-2023/2026-09-14.json` | config | 355 | 11 | `00213bb370f1` | 1 |
| `catalogs/authorities/observations/iso-iec-5259-2-2024/2026-09-20.json` | config | 443 | 11 | `894dbd632962` | 1 |
| `catalogs/authorities/observations/iso-iec-ieee-12207-2026/2026-09-14.json` | config | 335 | 11 | `82003094c710` | 1 |
| `catalogs/authorities/observations/iso-iec-ieee-15288-2023/2026-09-14.json` | config | 325 | 11 | `1b503c2fae95` | 1 |
| `catalogs/authorities/observations/iso-iec-ieee-29148-2018/2026-09-14.json` | config | 426 | 11 | `62cd4bdc7905` | 1 |
| `catalogs/authorities/observations/iso-integrated-management-systems-guide-2026/2026-09-14.json` | config | 363 | 11 | `76091242bcd1` | 1 |
| `catalogs/authorities/observations/json-schema-draft-2020-12/2026-09-14.json` | config | 411 | 11 | `e8fc56fce727` | 1 |
| `catalogs/authorities/observations/lean-startup-principles/2026-09-19.json` | config | 483 | 11 | `d341ffbf495d` | 1 |
| `catalogs/authorities/observations/mcp-spec-2026-07-28/2026-09-14.json` | config | 415 | 11 | `4c104be27cf8` | 1 |
| `catalogs/authorities/observations/mets-2/2026-09-14.json` | config | 464 | 11 | `6f1c411bed44` | 1 |
| `catalogs/authorities/observations/mrc-outcomes-data-quality-2022/2026-09-19.json` | config | 547 | 11 | `f99573221430` | 1 |
| `catalogs/authorities/observations/ndsa-levels-digital-preservation-2.1/2026-09-14.json` | config | 453 | 11 | `06ff61bd2ace` | 1 |
| `catalogs/authorities/observations/nist-ai-rmf-1.0/2026-09-14.json` | config | 476 | 11 | `f904c04914d1` | 1 |
| `catalogs/authorities/observations/nist-csf-2.0/2026-09-14.json` | config | 354 | 11 | `fd0ecd9b3222` | 1 |
| `catalogs/authorities/observations/nist-oscal-1.1.3/2026-09-14.json` | config | 333 | 11 | `d9edc89efcd5` | 1 |
| `catalogs/authorities/observations/nist-privacy-framework-1.0/2026-09-20.json` | config | 597 | 11 | `0f40544e431a` | 1 |
| `catalogs/authorities/observations/nist-sp-800-218-ssdf-1.1/2026-09-14.json` | config | 339 | 11 | `3c4a8025505b` | 1 |
| `catalogs/authorities/observations/nuxmv-2.2.0/2026-09-22.json` | config | 445 | 11 | `3c082a6f931c` | 1 |
| `catalogs/authorities/observations/oasis-opendocument-1.3/2026-09-14.json` | config | 392 | 11 | `1f373c22c24b` | 1 |
| `catalogs/authorities/observations/oasis-sarif-2.1.0/2026-09-14.json` | config | 330 | 11 | `d9fb2d2dab09` | 1 |
| `catalogs/authorities/observations/oci-distribution-spec-1.1.1/2026-09-14.json` | config | 362 | 11 | `bc4a50d30012` | 1 |
| `catalogs/authorities/observations/oci-image-spec-1.1.1/2026-09-14.json` | config | 348 | 11 | `ae5544f2061d` | 1 |
| `catalogs/authorities/observations/oci-runtime-spec-1.3.0/2026-09-14.json` | config | 352 | 11 | `587d5ca1dbd6` | 1 |
| `catalogs/authorities/observations/ocra-1.1.2/2026-09-22.json` | config | 536 | 11 | `3cf4aad791b5` | 1 |
| `catalogs/authorities/observations/ocra-2.1.0/2026-09-22.json` | config | 528 | 11 | `9fb7b8c432f7` | 1 |
| `catalogs/authorities/observations/ogc-geopackage-1.4.0/2026-09-14.json` | config | 424 | 11 | `0392130ac244` | 1 |
| `catalogs/authorities/observations/omg-bpmn-2.0.2/2026-09-14.json` | config | 323 | 11 | `b253100ff0be` | 1 |
| `catalogs/authorities/observations/omg-cmmn-1.1/2026-09-14.json` | config | 317 | 11 | `c250339f38f9` | 1 |
| `catalogs/authorities/observations/omg-dmn-1.5/2026-09-14.json` | config | 315 | 11 | `ed366c665e1f` | 1 |
| `catalogs/authorities/observations/omg-reqif-1.2/2026-09-14.json` | config | 319 | 11 | `b3c4961fad3b` | 1 |
| `catalogs/authorities/observations/omg-sacm-2.3/2026-09-22.json` | config | 474 | 11 | `9a10916566cd` | 1 |
| `catalogs/authorities/observations/openapi-3.2.0/2026-09-14.json` | config | 398 | 11 | `0341539e141c` | 1 |
| `catalogs/authorities/observations/openid-connect-core-1.0-errata2/2026-09-14.json` | config | 447 | 11 | `cc5e368d709d` | 1 |
| `catalogs/authorities/observations/openlineage-spec/2026-09-14.json` | config | 480 | 11 | `3fa16b9c4491` | 1 |
| `catalogs/authorities/observations/openlineage-spec/2026-11-06.json` | config | 764 | 11 | `37f085395a5c` | 1 |
| `catalogs/authorities/observations/opentelemetry-genai-semconv/2026-09-14.json` | config | 547 | 11 | `a5873b27b793` | 1 |
| `catalogs/authorities/observations/opentelemetry-spec-1.60.0/2026-09-14.json` | config | 331 | 11 | `f00156ba5ebf` | 1 |
| `catalogs/authorities/observations/orcid-id-structure/2026-09-14.json` | config | 599 | 11 | `d4ab6a5a51d9` | 1 |
| `catalogs/authorities/observations/otlp-1.11.0/2026-09-14.json` | config | 312 | 11 | `1d3d49020ae9` | 1 |
| `catalogs/authorities/observations/owasp-asvs-5.0.0/2026-09-14.json` | config | 353 | 11 | `18a922f7ff5f` | 1 |
| `catalogs/authorities/observations/pacti-0.3.1/2026-09-22.json` | config | 463 | 11 | `0f8347e0acc1` | 1 |
| `catalogs/authorities/observations/premis-3.0/2026-09-14.json` | config | 434 | 11 | `d49c9786f6c1` | 1 |
| `catalogs/authorities/observations/prisma-2020/2026-09-14.json` | config | 338 | 11 | `c0857d601d9b` | 1 |
| `catalogs/authorities/observations/pronom-registry/2026-09-14.json` | config | 419 | 11 | `c9ee29619a9a` | 1 |
| `catalogs/authorities/observations/qudt-units-3.5.1/2026-09-20.json` | config | 405 | 11 | `8906621f782f` | 1 |
| `catalogs/authorities/observations/rfc-1034/2026-09-14.json` | config | 369 | 11 | `e8e1e1a29284` | 1 |
| `catalogs/authorities/observations/rfc-1035/2026-09-14.json` | config | 369 | 11 | `0a49936f054b` | 1 |
| `catalogs/authorities/observations/rfc-6749/2026-09-14.json` | config | 399 | 11 | `0981242ab318` | 1 |
| `catalogs/authorities/observations/rfc-7858/2026-09-14.json` | config | 374 | 11 | `6fc2441d09b7` | 1 |
| `catalogs/authorities/observations/rfc-8310/2026-09-14.json` | config | 352 | 11 | `c65d3e12d893` | 1 |
| `catalogs/authorities/observations/rfc-8414/2026-09-20.json` | config | 444 | 11 | `f9fe078c2577` | 1 |
| `catalogs/authorities/observations/rfc-8484/2026-09-14.json` | config | 366 | 11 | `eb631fffd849` | 1 |
| `catalogs/authorities/observations/rfc-8493-bagit-1.0/2026-09-20.json` | config | 483 | 11 | `59cf23fb5406` | 1 |
| `catalogs/authorities/observations/rfc-8707/2026-09-14.json` | config | 377 | 11 | `002c9600833b` | 1 |
| `catalogs/authorities/observations/rfc-9000/2026-09-14.json` | config | 365 | 11 | `8c09d7ea9631` | 1 |
| `catalogs/authorities/observations/rfc-9110/2026-09-14.json` | config | 343 | 11 | `cc29a738064c` | 1 |
| `catalogs/authorities/observations/rfc-9113/2026-09-14.json` | config | 399 | 11 | `31d2247a442f` | 1 |
| `catalogs/authorities/observations/rfc-9114/2026-09-14.json` | config | 366 | 11 | `90b1fe4a986c` | 1 |
| `catalogs/authorities/observations/rfc-9700/2026-09-14.json` | config | 383 | 11 | `e8f6319fcbb7` | 1 |
| `catalogs/authorities/observations/rfc-9728/2026-09-20.json` | config | 443 | 11 | `963a34239ccd` | 1 |
| `catalogs/authorities/observations/rfc-9846/2026-09-14.json` | config | 437 | 11 | `1d5d39f341c0` | 1 |
| `catalogs/authorities/observations/ro-crate-1.3/2026-09-14.json` | config | 337 | 11 | `d8b749cf86ab` | 1 |
| `catalogs/authorities/observations/roger-martin-strategy-choice-cascade/2026-09-19.json` | config | 496 | 11 | `09d8eef0989c` | 1 |
| `catalogs/authorities/observations/ror-schema-2.1/2026-09-14.json` | config | 474 | 11 | `63ac0dfaeeb7` | 1 |
| `catalogs/authorities/observations/samr-registration-materials-2026/2026-09-19.json` | config | 540 | 11 | `dbe0c48f8df2` | 1 |
| `catalogs/authorities/observations/sdmx-3.1/2026-09-20.json` | config | 440 | 11 | `da86e4f6db71` | 1 |
| `catalogs/authorities/observations/sdmx-cl-obs-status-2.3/2026-09-20.json` | config | 454 | 11 | `2c0bbfc486bb` | 1 |
| `catalogs/authorities/observations/slsa-1.2/2026-09-14.json` | config | 307 | 11 | `3e143cc5c081` | 1 |
| `catalogs/authorities/observations/spdx-3.0/2026-09-14.json` | config | 418 | 11 | `b8cc40b82d5e` | 1 |
| `catalogs/authorities/observations/springer-research-data-policy/2026-09-14.json` | config | 360 | 11 | `2bde7b31331e` | 1 |
| `catalogs/authorities/observations/strategyzer-business-model-canvas/2026-09-19.json` | config | 487 | 11 | `776ab27c04c9` | 1 |
| `catalogs/authorities/observations/strategyzer-value-proposition-canvas/2026-09-19.json` | config | 500 | 11 | `10b2518e9380` | 1 |
| `catalogs/authorities/observations/stripe-saas-pricing-packaging/2026-09-19.json` | config | 523 | 11 | `84be6369b5fb` | 1 |
| `catalogs/authorities/observations/swhid-scheme-v1/2026-09-14.json` | config | 443 | 11 | `595b954b21e2` | 1 |
| `catalogs/authorities/observations/tla-tools-1.7.4/2026-09-22.json` | config | 498 | 11 | `e77660662275` | 1 |
| `catalogs/authorities/observations/togaf-standard-10th-edition/2026-09-14.json` | config | 567 | 11 | `17d83108c90f` | 1 |
| `catalogs/authorities/observations/ucum-spec/2026-09-20.json` | config | 430 | 11 | `59b552251bf1` | 1 |
| `catalogs/authorities/observations/w3c-dcat-3-2024/2026-09-20.json` | config | 475 | 11 | `c2cfe5a1caf2` | 1 |
| `catalogs/authorities/observations/w3c-odrl-2.2-2018/2026-09-20.json` | config | 470 | 11 | `be5ac6e40d46` | 1 |
| `catalogs/authorities/observations/w3c-png-3-2025/2026-09-14.json` | config | 381 | 11 | `a09d95658893` | 1 |
| `catalogs/authorities/observations/w3c-prov-o-2013/2026-09-14.json` | config | 313 | 11 | `f2f73f4aa1eb` | 1 |
| `catalogs/authorities/observations/wcag-2.2/2026-09-14.json` | config | 309 | 11 | `2dd0edac0d27` | 1 |
| `catalogs/authorities/observations/worldcc-contract-management-standard-4e/2026-09-19.json` | config | 539 | 11 | `433b6e728559` | 1 |
| `catalogs/authorities/observations/xbox-accessibility-guidelines-3.2/2026-09-14.json` | config | 384 | 11 | `634eea1e3bc0` | 1 |
| `catalogs/authorities/observations/xbrl-2.1/2026-09-14.json` | config | 474 | 11 | `4b4b0d87f92f` | 1 |
| `catalogs/authorities/observations/yc-essential-startup-advice/2026-09-19.json` | config | 484 | 11 | `bb565704c4b9` | 1 |
| `catalogs/authorities/observations/yc-how-to-sell-2018/2026-09-19.json` | config | 499 | 11 | `83425d0778ea` | 1 |
| `catalogs/authorities/planning/lego-plan-r1.json` | config | 4122 | 96 | `7a9d9d33f98a` | 1 |
| `catalogs/authorities/pyproject.toml` | config | 738 | 30 | `c24d6e495a53` |  |
| `catalogs/authorities/records/acm-sigsoft/acm-sigsoft-benchmarking.json` | config | 1107 | 47 | `ffb8904f6fca` | 1 |
| `catalogs/authorities/records/acm-sigsoft/acm-sigsoft-data-science.json` | config | 1101 | 47 | `c71c0f0392ad` | 1 |
| `catalogs/authorities/records/acm-sigsoft/acm-sigsoft-general.json` | config | 1133 | 48 | `b5909ee688a4` | 1 |
| `catalogs/authorities/records/acm-sigsoft/acm-sigsoft-replication.json` | config | 1093 | 47 | `99e9479660f4` | 1 |
| `catalogs/authorities/records/agent-skills/agent-skills-spec.json` | config | 1164 | 54 | `6d06d06af9f0` | 1 |
| `catalogs/authorities/records/apache-arrow/apache-arrow-format-1.5.json` | config | 1156 | 53 | `59ade79a21e5` | 1 |
| `catalogs/authorities/records/apache-beam/apache-beam-programming-model.json` | config | 1328 | 56 | `b284f2063879` | 1 |
| `catalogs/authorities/records/apache-iceberg/apache-iceberg-1.11.0.json` | config | 1164 | 52 | `4c492343fbc2` | 1 |
| `catalogs/authorities/records/apache-iceberg/apache-iceberg-spec-v3.json` | config | 1250 | 55 | `899b3a81a537` | 1 |
| `catalogs/authorities/records/apache-parquet/apache-parquet-format-2.13.0.json` | config | 1166 | 53 | `b275d6fb5d74` | 1 |
| `catalogs/authorities/records/apalache-mc/apalache-0.58.3.json` | config | 1238 | 52 | `28ef746c6f3e` | 1 |
| `catalogs/authorities/records/artefactual/archivematica-1.18.0.json` | config | 1253 | 56 | `5df15e9bcbc1` | 1 |
| `catalogs/authorities/records/artefactual/artefactual-fixity-0.8.0.json` | config | 1321 | 55 | `50d1b59f850b` | 1 |
| `catalogs/authorities/records/asyncapi/asyncapi-3.1.0.json` | config | 1187 | 53 | `267f6fc1ac86` | 1 |
| `catalogs/authorities/records/bitol/bitol-odcs-3.2.0.json` | config | 1335 | 58 | `66775525a255` | 1 |
| `catalogs/authorities/records/bitol/bitol-odps-1.1.0.json` | config | 1316 | 58 | `7625ded8071c` | 1 |
| `catalogs/authorities/records/c2pa/c2pa-2.4.json` | config | 1164 | 52 | `e93e6048eace` | 1 |
| `catalogs/authorities/records/citation-style-language/csl-1.0.2.json` | config | 1285 | 55 | `808eee723f12` | 1 |
| `catalogs/authorities/records/cncf-cloudevents/cloudevents-1.0.2.json` | config | 1165 | 52 | `325fce6077eb` | 1 |
| `catalogs/authorities/records/commons-ip/commons-ip-2.11.3.json` | config | 1280 | 55 | `d14ef172a3a5` | 1 |
| `catalogs/authorities/records/coretrustseal/coretrustseal-requirements-2026-2028.json` | config | 1353 | 51 | `a8d2763e0731` | 1 |
| `catalogs/authorities/records/cpmi-iosco/cpmi-iosco-pfmi-2012.json` | config | 1260 | 53 | `81e0ca7fa19c` | 1 |
| `catalogs/authorities/records/crossref/crossref-metadata-deposit-schema-5.5.0.json` | schemas | 1324 | 55 | `d46f7c38a738` | 1 |
| `catalogs/authorities/records/datacite/datacite-metadata-schema-4.7.json` | schemas | 1255 | 55 | `f60c2bca3a45` | 1 |
| `catalogs/authorities/records/debezium/debezium-stable-cdc.json` | config | 1245 | 53 | `43c657d6200e` | 1 |
| `catalogs/authorities/records/digital-preservation-coalition/dpc-ram-3.json` | config | 1347 | 51 | `b3c9586f5ceb` | 1 |
| `catalogs/authorities/records/dilcis-board/e-ark-csip-2.2.0.json` | config | 1247 | 51 | `3dccd89c1839` | 1 |
| `catalogs/authorities/records/dilcis-board/e-ark-sip-2.2.0.json` | config | 1348 | 56 | `b2e994cd81b2` | 1 |
| `catalogs/authorities/records/dilcis/eark-csip-2.2.0.json` | config | 1257 | 55 | `8f1a0034aa70` | 1 |
| `catalogs/authorities/records/dilcis/eark-sip-2.2.0.json` | config | 1311 | 55 | `07961fda3a4d` | 1 |
| `catalogs/authorities/records/fbk/nuxmv-2.2.0.json` | config | 1225 | 52 | `5579b8b0a947` | 1 |
| `catalogs/authorities/records/fbk/ocra-1.1.2.json` | config | 1351 | 55 | `3c7ce53314c0` | 1 |
| `catalogs/authorities/records/fbk/ocra-2.1.0.json` | config | 1332 | 57 | `c2db8b9ecad6` | 1 |
| `catalogs/authorities/records/fix-trading/fix-4.4-errata-20030618.json` | config | 1315 | 54 | `ba7b128a3c03` | 1 |
| `catalogs/authorities/records/frappe/erpnext-budget-provider.json` | config | 1266 | 53 | `30463851d9e5` | 1 |
| `catalogs/authorities/records/frappe/erpnext-crm-provider.json` | config | 1266 | 52 | `cf6901d8d69d` | 1 |
| `catalogs/authorities/records/frappe/frappe-crm-provider.json` | config | 1039 | 51 | `c8ca0bc30d39` | 1 |
| `catalogs/authorities/records/frappe/frappe-helpdesk-provider.json` | config | 1158 | 54 | `7da5bc64e46f` | 1 |
| `catalogs/authorities/records/frappe/frappe-hr-payroll-provider.json` | config | 1233 | 53 | `4a61db4d7a71` | 1 |
| `catalogs/authorities/records/games-user-research/games-user-research-practice.json` | config | 1141 | 49 | `1a6852a7eb62` | 1 |
| `catalogs/authorities/records/go-fair/fair-principles.json` | config | 1047 | 50 | `ec6e15a5f39f` | 1 |
| `catalogs/authorities/records/godot-engine/godot-provider.json` | config | 1075 | 48 | `9b1fc04649a9` | 1 |
| `catalogs/authorities/records/google/google-analytics-traffic-source.json` | config | 1341 | 54 | `2b6d360e35ed` | 1 |
| `catalogs/authorities/records/google/google-search-essentials.json` | config | 1200 | 51 | `75fd83238f13` | 1 |
| `catalogs/authorities/records/iab/iab-privacy-standards.json` | config | 1254 | 52 | `65b1c7e673b1` | 1 |
| `catalogs/authorities/records/icc/icc-esomar-code-2025.json` | config | 1405 | 53 | `e2cc94a4468f` | 1 |
| `catalogs/authorities/records/icc/icc-marketing-code-2024.json` | config | 1434 | 54 | `b4a13cc25e0a` | 1 |
| `catalogs/authorities/records/ietf/rfc-1034.json` | config | 1080 | 52 | `bb4f67b1d77e` | 1 |
| `catalogs/authorities/records/ietf/rfc-1035.json` | config | 1116 | 53 | `ed77cde815de` | 1 |
| `catalogs/authorities/records/ietf/rfc-6749.json` | config | 1177 | 57 | `870ecd122399` | 1 |
| `catalogs/authorities/records/ietf/rfc-7858.json` | config | 1107 | 55 | `95e0bee26f2b` | 1 |
| `catalogs/authorities/records/ietf/rfc-8310.json` | config | 1111 | 54 | `4b18bbc6bf8e` | 1 |
| `catalogs/authorities/records/ietf/rfc-8414.json` | config | 1207 | 57 | `e31a09564c13` | 1 |
| `catalogs/authorities/records/ietf/rfc-8484.json` | config | 1082 | 55 | `e28821df3b39` | 1 |
| `catalogs/authorities/records/ietf/rfc-8493-bagit-1.0.json` | config | 1271 | 55 | `6c98ebf9ca40` | 1 |
| `catalogs/authorities/records/ietf/rfc-8707.json` | config | 1168 | 56 | `9409df58b785` | 1 |
| `catalogs/authorities/records/ietf/rfc-9000.json` | config | 1096 | 54 | `cb5e365ad909` | 1 |
| `catalogs/authorities/records/ietf/rfc-9110.json` | config | 1053 | 52 | `a2e77cc747ee` | 1 |
| `catalogs/authorities/records/ietf/rfc-9113.json` | config | 1052 | 54 | `8c69cd95065c` | 1 |
| `catalogs/authorities/records/ietf/rfc-9114.json` | config | 1062 | 55 | `e1b26ff468f6` | 1 |
| `catalogs/authorities/records/ietf/rfc-9700.json` | config | 1158 | 55 | `c389a56e9483` | 1 |
| `catalogs/authorities/records/ietf/rfc-9728.json` | config | 1241 | 59 | `c518c7539c03` | 1 |
| `catalogs/authorities/records/ietf/rfc-9846.json` | config | 1111 | 52 | `887957e7b9b2` | 1 |
| `catalogs/authorities/records/in-toto/in-toto-1.0.json` | config | 1150 | 54 | `12568d327bb6` | 1 |
| `catalogs/authorities/records/iptc/iptc-photo-metadata-2025.1.json` | config | 1205 | 52 | `f2f769f1e752` | 1 |
| `catalogs/authorities/records/iso-iec-ieee/iso-iec-ieee-12207-2026.json` | config | 1099 | 48 | `c08428865c91` | 1 |
| `catalogs/authorities/records/iso-iec-ieee/iso-iec-ieee-15288-2023.json` | config | 1145 | 49 | `e5f0d3c85410` | 1 |
| `catalogs/authorities/records/iso-iec-ieee/iso-iec-ieee-29148-2018.json` | config | 1331 | 56 | `374f54f5ad50` | 1 |
| `catalogs/authorities/records/iso-iec/iso-iec-11179-3-2023.json` | config | 1361 | 55 | `e79200110631` | 1 |
| `catalogs/authorities/records/iso-iec/iso-iec-11179-3-amd1-2026.json` | config | 1313 | 54 | `0d5bb1cf7332` | 1 |
| `catalogs/authorities/records/iso-iec/iso-iec-12113-2022.json` | config | 1136 | 53 | `4e8da390a839` | 1 |
| `catalogs/authorities/records/iso-iec/iso-iec-20000-1-2018-amd1-2024.json` | config | 1296 | 54 | `91617ebaf927` | 1 |
| `catalogs/authorities/records/iso-iec/iso-iec-25010-2023.json` | config | 1053 | 48 | `8c668faddc39` | 1 |
| `catalogs/authorities/records/iso-iec/iso-iec-27001-2022-amd1-2024.json` | config | 1288 | 54 | `321c11855dd7` | 1 |
| `catalogs/authorities/records/iso-iec/iso-iec-29500-1-2016.json` | config | 1196 | 53 | `82924a41c022` | 1 |
| `catalogs/authorities/records/iso-iec/iso-iec-42001-2023.json` | config | 1203 | 54 | `a24531a1f43d` | 1 |
| `catalogs/authorities/records/iso-iec/iso-iec-5259-2-2024.json` | config | 1339 | 55 | `e30804694f2d` | 1 |
| `catalogs/authorities/records/iso/iso-10002-2018.json` | config | 1185 | 52 | `3c194e819302` | 1 |
| `catalogs/authorities/records/iso/iso-10004-2018.json` | config | 1187 | 52 | `0b80876a4173` | 1 |
| `catalogs/authorities/records/iso/iso-10005-2018.json` | config | 1120 | 50 | `707c8d7b42d7` | 1 |
| `catalogs/authorities/records/iso/iso-10006-2017.json` | config | 1127 | 49 | `33571aa9b859` | 1 |
| `catalogs/authorities/records/iso/iso-14289-2-2024.json` | config | 1192 | 54 | `4afc2c412d9a` | 1 |
| `catalogs/authorities/records/iso/iso-14721-2025.json` | config | 1290 | 51 | `a85e790e52fa` | 1 |
| `catalogs/authorities/records/iso/iso-15489-1-2016.json` | config | 1306 | 55 | `f049d181a8f2` | 1 |
| `catalogs/authorities/records/iso/iso-17442-1-2020.json` | config | 1210 | 52 | `8247cd25b455` | 1 |
| `catalogs/authorities/records/iso/iso-19005-4-2020.json` | config | 1187 | 54 | `6b5c795e448d` | 1 |
| `catalogs/authorities/records/iso/iso-19011-2026.json` | config | 1080 | 49 | `c7effa3dac18` | 1 |
| `catalogs/authorities/records/iso/iso-20022-1-2026.json` | config | 1257 | 53 | `4086838bb52e` | 1 |
| `catalogs/authorities/records/iso/iso-20104-2015.json` | config | 1335 | 54 | `77a8b5db38e0` | 1 |
| `catalogs/authorities/records/iso/iso-20252-2026.json` | config | 1224 | 53 | `1714a80bd502` | 1 |
| `catalogs/authorities/records/iso/iso-20400-2017.json` | config | 1186 | 51 | `7977a41c9713` | 1 |
| `catalogs/authorities/records/iso/iso-20652-2006.json` | config | 1328 | 53 | `0de8cef2a62f` | 1 |
| `catalogs/authorities/records/iso/iso-20671-1-2021.json` | config | 1141 | 49 | `dad360c37771` | 1 |
| `catalogs/authorities/records/iso/iso-21502-2020.json` | config | 1168 | 50 | `4ccb887d2616` | 1 |
| `catalogs/authorities/records/iso/iso-22301-2019-amd1-2024.json` | config | 1265 | 53 | `54df18c51a2d` | 1 |
| `catalogs/authorities/records/iso/iso-28500-2017.json` | config | 1118 | 52 | `70b726319039` | 1 |
| `catalogs/authorities/records/iso/iso-30401-2018-amd1-2022-amd2-2024.json` | config | 1275 | 52 | `eb4f3392b768` | 1 |
| `catalogs/authorities/records/iso/iso-30405-2023.json` | config | 1087 | 50 | `e15e1bc49f0f` | 1 |
| `catalogs/authorities/records/iso/iso-31000-2018.json` | config | 1121 | 51 | `4c2f0092a4c6` | 1 |
| `catalogs/authorities/records/iso/iso-32000-2-2020.json` | config | 1131 | 51 | `d84d556c8ad8` | 1 |
| `catalogs/authorities/records/iso/iso-37301-2021.json` | config | 1039 | 48 | `b827449c6912` | 1 |
| `catalogs/authorities/records/iso/iso-37500-2014.json` | config | 1042 | 49 | `0c189afdf630` | 1 |
| `catalogs/authorities/records/iso/iso-56001-2024.json` | config | 1149 | 51 | `0e569f6e281b` | 1 |
| `catalogs/authorities/records/iso/iso-8000-115-2024.json` | config | 1324 | 55 | `ae44ace63bb1` | 1 |
| `catalogs/authorities/records/iso/iso-9001-2015-amd1-2024.json` | config | 1185 | 52 | `1f5727005e86` | 1 |
| `catalogs/authorities/records/iso/iso-9001-2026.json` | config | 1127 | 51 | `f377fb16c6c8` | 1 |
| `catalogs/authorities/records/iso/iso-9004-2018.json` | config | 1065 | 48 | `a7eb09b3d87c` | 1 |
| `catalogs/authorities/records/iso/iso-9241-11-2018.json` | config | 1087 | 50 | `c3587ff6c9fd` | 1 |
| `catalogs/authorities/records/iso/iso-9241-210-2019.json` | config | 1085 | 49 | `bc8167d5a254` | 1 |
| `catalogs/authorities/records/iso/iso-integrated-management-systems-guide-2026.json` | config | 1184 | 49 | `cb7650849eb1` | 1 |
| `catalogs/authorities/records/json-schema/json-schema-draft-2020-12.json` | schemas | 1187 | 54 | `56a01323d5a0` | 1 |
| `catalogs/authorities/records/lean-startup/lean-startup-principles.json` | config | 1099 | 50 | `93189857f995` | 1 |
| `catalogs/authorities/records/linux-foundation/spdx-3.0.json` | config | 1142 | 54 | `4799dac1f82e` | 1 |
| `catalogs/authorities/records/loc-premis/premis-3.0.json` | config | 1255 | 54 | `54e2207bdfe0` | 1 |
| `catalogs/authorities/records/mets-editorial-board/mets-2.json` | config | 1277 | 53 | `e2f4ddb67738` | 1 |
| `catalogs/authorities/records/microsoft-xbox/xbox-accessibility-guidelines-3.2.json` | config | 1130 | 49 | `f4aac5d1942f` | 1 |
| `catalogs/authorities/records/model-context-protocol/mcp-spec-2026-07-28.json` | config | 1247 | 55 | `2b4daa66870b` | 1 |
| `catalogs/authorities/records/mrc/mrc-outcomes-data-quality-2022.json` | config | 1302 | 53 | `3a157ddf1a51` | 1 |
| `catalogs/authorities/records/ndsa/ndsa-levels-digital-preservation-2.1.json` | config | 1347 | 54 | `51b4eee6c84a` | 1 |
| `catalogs/authorities/records/niso/ansi-niso-z39.104-2022-credit.json` | config | 1327 | 54 | `41647989ee7b` | 1 |
| `catalogs/authorities/records/nist/nist-ai-rmf-1.0.json` | config | 1237 | 53 | `85c3e8ddb3b8` | 1 |
| `catalogs/authorities/records/nist/nist-csf-2.0.json` | config | 1110 | 51 | `c0651c18f0cd` | 1 |
| `catalogs/authorities/records/nist/nist-oscal-1.1.3.json` | config | 1198 | 52 | `2aa1095234ed` | 1 |
| `catalogs/authorities/records/nist/nist-privacy-framework-1.0.json` | config | 1397 | 56 | `d0fb5f4d6277` | 1 |
| `catalogs/authorities/records/nist/nist-sp-800-218-ssdf-1.1.json` | config | 1137 | 51 | `0c3f3e491af9` | 1 |
| `catalogs/authorities/records/oasis/oasis-opendocument-1.3.json` | config | 1220 | 53 | `362a1ba19ab3` | 1 |
| `catalogs/authorities/records/oasis/oasis-sarif-2.1.0.json` | config | 1170 | 52 | `9cd01546fc83` | 1 |
| `catalogs/authorities/records/oci/oci-distribution-spec-1.1.1.json` | config | 1160 | 51 | `f6d582f40791` | 1 |
| `catalogs/authorities/records/oci/oci-image-spec-1.1.1.json` | config | 1135 | 51 | `1a56ff6f7dbc` | 1 |
| `catalogs/authorities/records/oci/oci-runtime-spec-1.3.0.json` | config | 1138 | 50 | `abb2aecf4d21` | 1 |
| `catalogs/authorities/records/ogc/ogc-geopackage-1.4.0.json` | config | 1102 | 53 | `31e9e6c4842d` | 1 |
| `catalogs/authorities/records/omg/omg-bpmn-2.0.2.json` | config | 1092 | 50 | `400339472a16` | 1 |
| `catalogs/authorities/records/omg/omg-cmmn-1.1.json` | config | 1082 | 50 | `e54c3e61ab60` | 1 |
| `catalogs/authorities/records/omg/omg-dmn-1.5.json` | config | 1075 | 50 | `7bb26b037de6` | 1 |
| `catalogs/authorities/records/omg/omg-reqif-1.2.json` | config | 1083 | 50 | `8d607a500d55` | 1 |
| `catalogs/authorities/records/omg/omg-sacm-2.3.json` | config | 1233 | 55 | `f972ba293e9e` | 1 |
| `catalogs/authorities/records/openapi-initiative/openapi-3.2.0.json` | config | 1144 | 53 | `1058d044daf8` | 1 |
| `catalogs/authorities/records/openid-foundation/openid-connect-core-1.0-errata2.json` | config | 1248 | 56 | `809062110e6f` | 1 |
| `catalogs/authorities/records/openlineage/openlineage-spec.json` | config | 1149 | 52 | `49a5559cc8a9` | 1 |
| `catalogs/authorities/records/opentelemetry/opentelemetry-genai-semconv.json` | config | 1326 | 56 | `42a263a4e2ab` | 1 |
| `catalogs/authorities/records/opentelemetry/opentelemetry-spec-1.60.0.json` | config | 1204 | 54 | `601c5efdb7c0` | 1 |
| `catalogs/authorities/records/opentelemetry/otlp-1.11.0.json` | config | 1192 | 54 | `8bc190ad9312` | 1 |
| `catalogs/authorities/records/orcid/orcid-id-structure.json` | config | 1270 | 54 | `293688756dea` | 1 |
| `catalogs/authorities/records/owasp-ecma/cyclonedx-1.7.json` | config | 1287 | 56 | `eca102a258be` | 1 |
| `catalogs/authorities/records/owasp/owasp-asvs-5.0.0.json` | config | 1164 | 51 | `662e3999f543` | 1 |
| `catalogs/authorities/records/pacti/pacti-0.3.1.json` | config | 1147 | 53 | `89c2bfd1291b` | 1 |
| `catalogs/authorities/records/prisma/prisma-2020.json` | config | 1037 | 47 | `d834c983e570` | 1 |
| `catalogs/authorities/records/qudt/qudt-units-3.5.1.json` | config | 1246 | 56 | `fa14321a6865` | 1 |
| `catalogs/authorities/records/research-object/ro-crate-1.3.json` | config | 1092 | 50 | `1e11074bdc01` | 1 |
| `catalogs/authorities/records/roger-l-martin/roger-martin-strategy-choice-cascade.json` | config | 1349 | 58 | `143ad00fa839` | 1 |
| `catalogs/authorities/records/ror/ror-schema-2.1.json` | schemas | 1234 | 54 | `7777e278ee06` | 1 |
| `catalogs/authorities/records/samr/samr-registration-materials-2026.json` | config | 1262 | 49 | `636c22ad0d17` | 1 |
| `catalogs/authorities/records/scsc/gsn-3.json` | config | 1276 | 57 | `5053b74fe031` | 1 |
| `catalogs/authorities/records/sdmx/sdmx-3.1.json` | config | 1353 | 58 | `e357e1f6cb64` | 1 |
| `catalogs/authorities/records/sdmx/sdmx-cl-obs-status-2.3.json` | config | 1349 | 55 | `e39b1d3544b9` | 1 |
| `catalogs/authorities/records/slsa/slsa-1.2.json` | config | 1061 | 50 | `de7ffebfdd1e` | 1 |
| `catalogs/authorities/records/software-heritage/swhid-scheme-v1.json` | config | 1328 | 54 | `1b8854b93b17` | 1 |
| `catalogs/authorities/records/springer-nature/emse-submission-guidelines.json` | config | 1102 | 47 | `37676f6d47ee` | 1 |
| `catalogs/authorities/records/springer-nature/springer-research-data-policy.json` | config | 1088 | 47 | `6883bbed1eed` | 1 |
| `catalogs/authorities/records/strategyzer/strategyzer-business-model-canvas.json` | config | 1196 | 52 | `be19a17d3f3d` | 1 |
| `catalogs/authorities/records/strategyzer/strategyzer-value-proposition-canvas.json` | config | 1216 | 52 | `9cd18423bb70` | 1 |
| `catalogs/authorities/records/stripe/stripe-saas-pricing-packaging.json` | config | 1182 | 50 | `9acf728eccf3` | 1 |
| `catalogs/authorities/records/the-open-group/archimate-3.2.json` | config | 1258 | 53 | `a41da4fc9dc2` | 1 |
| `catalogs/authorities/records/the-open-group/togaf-standard-10th-edition.json` | config | 1241 | 52 | `91737f9eb559` | 1 |
| `catalogs/authorities/records/tlaplus/tla-tools-1.7.4.json` | config | 1260 | 54 | `2d01da6328c4` | 1 |
| `catalogs/authorities/records/ucum/ucum-spec.json` | config | 1238 | 55 | `8391eee5bbba` | 1 |
| `catalogs/authorities/records/uk-national-archives/pronom-registry.json` | config | 1199 | 53 | `e1e39b48320e` | 1 |
| `catalogs/authorities/records/w3c/w3c-dcat-3-2024.json` | config | 1248 | 60 | `60f855880d4c` | 1 |
| `catalogs/authorities/records/w3c/w3c-odrl-2.2-2018.json` | config | 1322 | 57 | `3b25e7062263` | 1 |
| `catalogs/authorities/records/w3c/w3c-png-3-2025.json` | config | 1096 | 52 | `35b798e88157` | 1 |
| `catalogs/authorities/records/w3c/w3c-prov-o-2013.json` | config | 1097 | 52 | `36d8f241653f` | 1 |
| `catalogs/authorities/records/w3c/wcag-2.2.json` | config | 1013 | 49 | `268ae5a4fb27` | 1 |
| `catalogs/authorities/records/worldcc/worldcc-contract-management-standard-4e.json` | config | 1485 | 53 | `169ecf14e797` | 1 |
| `catalogs/authorities/records/xbrl-international/xbrl-2.1.json` | config | 1176 | 52 | `832e642c078a` | 1 |
| `catalogs/authorities/records/y-combinator/yc-essential-startup-advice.json` | config | 1149 | 50 | `d2ac924564cc` | 1 |
| `catalogs/authorities/records/y-combinator/yc-how-to-sell-2018.json` | config | 1137 | 52 | `95580ca3156e` | 1 |
| `catalogs/authorities/schemas/external-authority-index-v1.schema.json` | schemas | 1779 | 38 | `0a47f455aa04` |  |
| `catalogs/authorities/schemas/external-authority-observation-v1.schema.json` | schemas | 1251 | 32 | `bd5b98e4ecc0` |  |
| `catalogs/authorities/schemas/external-authority-record-v1.schema.json` | schemas | 3197 | 74 | `c79061bf840d` |  |
| `catalogs/authorities/scripts/authority_catalog.py` | core | 8554 | 280 | `30c82bed668e` |  |
| `catalogs/authorities/scripts/authority_catalog_search.py` | core | 3388 | 109 | `842803e15c9f` |  |
| `catalogs/authorities/scripts/authority_catalog_sources.py` | core | 5840 | 150 | `40da61b4df5e` |  |
| `catalogs/authorities/scripts/check_authority_catalog_r1.py` | core | 5674 | 159 | `d0b247591621` |  |
| `catalogs/authorities/scripts/check_historical_registration.py` | core | 2951 | 83 | `d344b48d38b4` |  |
| `catalogs/authorities/tests/test_authority_catalog.py` | tests | 13613 | 290 | `8dfd2f366bbe` |  |
| `catalogs/authorities/uv.lock` | config | 60517 | — | `1e739a44ffbf` |  |
| `catalogs/authorities/venues/fse-2027-research-r1.json` | config | 2154 | 82 | `aae4178a0d53` | 1 |

### capability-catalog — catalogs/capabilities/（77 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `catalogs/capabilities/AGENTS.md` | docs | 2770 | 19 | `9f96fe684c59` |  |
| `catalogs/capabilities/README.md` | docs | 5342 | 74 | `ee2755faabb8` |  |
| `catalogs/capabilities/RESEARCH_CAPABILITY_PACKAGE_R1.md` | docs | 5964 | 85 | `2d8cb3bb499e` |  |
| `catalogs/capabilities/artifact/README.md` | docs | 960 | 23 | `26de46c35f55` |  |
| `catalogs/capabilities/authority-map-r1.md` | docs | 21246 | 429 | `e9df82528db9` |  |
| `catalogs/capabilities/docs/EXTERNAL_CAPABILITY_EVALUATION_R1.md` | docs | 7661 | 76 | `73a8bc899b32` |  |
| `catalogs/capabilities/docs/HUMAN_EXTERNAL_LEGO_REVIEW_R1.md` | docs | 3565 | 38 | `2e39746c8121` |  |
| `catalogs/capabilities/ele/README.md` | docs | 7439 | 122 | `6f9440058724` |  |
| `catalogs/capabilities/ele/relations.py` | core | 5308 | 155 | `a1ac0faf0dfb` |  |
| `catalogs/capabilities/ele/schema.sql` | schemas | 2711 | 64 | `75e07b4ab39f` |  |
| `catalogs/capabilities/ele/studies.py` | core | 25499 | 688 | `5f263cf426b7` |  |
| `catalogs/capabilities/evidence/capability-packages-r1-20260913.md` | evidence | 13948 | 151 | `49b02b868ea2` |  |
| `catalogs/capabilities/evidence/cross-owner-source-observations-20261106.json` | evidence | 4100 | 89 | `bc1cec885614` |  |
| `catalogs/capabilities/evidence/github-radar/2026-11-06.json` | evidence | 7794 | 220 | `8a2c746ba9c3` |  |
| `catalogs/capabilities/evidence/worktrunk-candidate-20261106.json` | evidence | 3028 | 53 | `699b643035a0` | r1 |
| `catalogs/capabilities/evidence/worktrunk-repo-owner-consumer-shadow-20261106.json` | evidence | 2199 | 61 | `61f14ae1c871` |  |
| `catalogs/capabilities/packages/INDEX.md` | docs | 2879 | 33 | `4669fd5a90dd` |  |
| `catalogs/capabilities/packages/README.md` | docs | 2589 | 44 | `27c8ad05cf20` |  |
| `catalogs/capabilities/packages/artifact.md` | docs | 3129 | 62 | `6119ec4c0060` |  |
| `catalogs/capabilities/packages/data-analytics.md` | docs | 7769 | 191 | `aa6543c029c3` |  |
| `catalogs/capabilities/packages/distribution.md` | docs | 2351 | 54 | `5edb1f98d72e` |  |
| `catalogs/capabilities/packages/engineering.md` | docs | 4165 | 63 | `6e92d3787cdf` |  |
| `catalogs/capabilities/packages/game.md` | docs | 4792 | 78 | `a0b5d9ecd3d6` |  |
| `catalogs/capabilities/packages/media.md` | docs | 4090 | 73 | `5b2b90faf0f5` |  |
| `catalogs/capabilities/packages/network.md` | docs | 2474 | 50 | `424e98156b41` |  |
| `catalogs/capabilities/packages/operations.md` | docs | 5649 | 75 | `18a8d8bb6390` |  |
| `catalogs/capabilities/packages/preservation.md` | docs | 5174 | 96 | `794344059340` |  |
| `catalogs/capabilities/packages/research.md` | docs | 6068 | 82 | `152adb8c9929` |  |
| `catalogs/capabilities/packages/security.md` | docs | 4166 | 93 | `3ea7b77cefb8` |  |
| `catalogs/capabilities/profiles/web-interaction-r1.json` | config | 3990 | 93 | `57672424a00a` | 1 |
| `catalogs/capabilities/providers/artifact-v2.md` | docs | 928 | 20 | `2a8e3a4679ba` |  |
| `catalogs/capabilities/providers/browser-use.md` | docs | 8235 | 177 | `49e09e59ab92` |  |
| `catalogs/capabilities/providers/check-jsonschema.md` | schemas | 1484 | 27 | `08eb337d5abc` |  |
| `catalogs/capabilities/providers/codex.md` | docs | 5640 | 114 | `7eb4039bbbb1` |  |
| `catalogs/capabilities/providers/comfyui.md` | docs | 9905 | 262 | `1f0181e7a5a3` |  |
| `catalogs/capabilities/providers/commons-ip.md` | docs | 1712 | 35 | `a84d3745bd8e` |  |
| `catalogs/capabilities/providers/dagster.md` | docs | 11571 | 368 | `cc768a0d931d` |  |
| `catalogs/capabilities/providers/dify.md` | docs | 14160 | 403 | `27d7023588da` |  |
| `catalogs/capabilities/providers/distribution-v2.md` | docs | 1240 | 23 | `620452b9fdec` |  |
| `catalogs/capabilities/providers/enduro.md` | docs | 2007 | 33 | `cb8a28dc4926` |  |
| `catalogs/capabilities/providers/firecrawl.md` | docs | 8856 | 207 | `e3896bd259b9` |  |
| `catalogs/capabilities/providers/flowable.md` | docs | 2568 | 51 | `6bee4ea19c3e` |  |
| `catalogs/capabilities/providers/graphify.md` | docs | 6433 | 184 | `5fdbda141175` |  |
| `catalogs/capabilities/providers/haystack.md` | docs | 6224 | 206 | `7b6e6127bbd7` |  |
| `catalogs/capabilities/providers/langfuse.md` | docs | 7943 | 217 | `b08db7a08c17` |  |
| `catalogs/capabilities/providers/langgraph.md` | docs | 11957 | 348 | `dd3af515a07c` |  |
| `catalogs/capabilities/providers/litellm.md` | docs | 12600 | 315 | `2b990bfe0374` |  |
| `catalogs/capabilities/providers/llamaindex.md` | docs | 7114 | 201 | `e1ff18682804` |  |
| `catalogs/capabilities/providers/markitdown.md` | docs | 7763 | 189 | `762e565e0b63` |  |
| `catalogs/capabilities/providers/mcp.md` | docs | 11243 | 300 | `75c8aec53df0` |  |
| `catalogs/capabilities/providers/microsoft-agent-framework.md` | docs | 1694 | 28 | `4fa5bae75018` |  |
| `catalogs/capabilities/providers/n8n.md` | docs | 4682 | 117 | `72e9095fd950` |  |
| `catalogs/capabilities/providers/network-v2.md` | docs | 1066 | 21 | `b3377b3a9e90` |  |
| `catalogs/capabilities/providers/openinference.md` | docs | 5599 | 133 | `c6895d09f587` |  |
| `catalogs/capabilities/providers/opentelemetry.md` | docs | 8161 | 228 | `f86e1ffd715d` |  |
| `catalogs/capabilities/providers/phoenix.md` | docs | 7435 | 197 | `b665345a4f82` |  |
| `catalogs/capabilities/providers/plane.md` | docs | 949 | 25 | `ed0d2abcc317` |  |
| `catalogs/capabilities/providers/playwright-cli.md` | docs | 2424 | 37 | `594ee0a42f80` |  |
| `catalogs/capabilities/providers/qdrant.md` | docs | 11234 | 321 | `fafa9b9da198` |  |
| `catalogs/capabilities/providers/reasoning-waist.md` | docs | 3134 | 61 | `a2cd7272bf1a` |  |
| `catalogs/capabilities/providers/runtime.md` | docs | 2455 | 30 | `51d9bd0b4d94` |  |
| `catalogs/capabilities/providers/security-v2.md` | docs | 1080 | 20 | `bc7779384ba2` |  |
| `catalogs/capabilities/providers/strictdoc.md` | docs | 1402 | 37 | `1faa995b480f` |  |
| `catalogs/capabilities/providers/temporal.md` | docs | 12450 | 290 | `c049e130e287` |  |
| `catalogs/capabilities/providers/workstation-v2.md` | docs | 2050 | 40 | `9afd068413bc` |  |
| `catalogs/capabilities/providers/worktrunk.md` | docs | 2091 | 17 | `44c608256359` |  |
| `catalogs/capabilities/routing/web_interaction_route.py` | core | 7233 | 193 | `bcb239d9a358` |  |
| `catalogs/capabilities/routing/web_provider_census.py` | core | 6341 | 170 | `d26dbfa805fd` |  |
| `catalogs/capabilities/schemas/external-capability-candidate-r1.schema.json` | schemas | 4739 | 205 | `29427ac53682` |  |
| `catalogs/capabilities/scripts/check_external_candidate_references.py` | core | 3118 | 68 | `1db1a84d2bac` |  |
| `catalogs/capabilities/scripts/compare_worktrunk_owner_consumer.py` | core | 9751 | 186 | `d791a7d7f6a1` |  |
| `catalogs/capabilities/scripts/github_radar_incremental.py` | core | 10082 | 207 | `2955a58ab496` |  |
| `catalogs/capabilities/scripts/verify_reasoning_providers.py` | core | 7936 | 225 | `61a285aa9f22` |  |
| `catalogs/capabilities/tests/test_ele_pg_studies.py` | tests | 6637 | 185 | `870573677d29` |  |
| `catalogs/capabilities/tests/test_external_capability_evaluation.py` | tests | 8189 | 153 | `44925e4d9604` |  |
| `catalogs/capabilities/tests/test_web_interaction_route.py` | tests | 5291 | 124 | `cb0f82d6fe27` |  |
| `catalogs/capabilities/tests/test_web_provider_routing_skill.py` | tests | 626 | 16 | `0210ffda8a7d` |  |

### composition — packages/composition/（86 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `packages/composition/AGENTS.md` | docs | 1479 | 25 | `d8f548bf4573` |  |
| `packages/composition/README.md` | docs | 2203 | 46 | `575a323c98ad` |  |
| `packages/composition/docs/COGNITIVE_CIRCUIT_R1.md` | docs | 9436 | 287 | `bdf3d7639645` |  |
| `packages/composition/docs/FINANCE_CONTRACTUAL_EXECUTION_SPEC_R1.md` | docs | 40431 | 479 | `dbfb936f2265` |  |
| `packages/composition/docs/IDENTITY_TOKEN_GRAMMAR_20261031.md` | docs | 2913 | 52 | `3dea74f36f8f` |  |
| `packages/composition/docs/INTERFACE_CONTRACT_EVOLUTION_R2.md` | docs | 5809 | 198 | `abe08b536317` |  |
| `packages/composition/docs/META_IMPROVEMENT_MEASUREMENT_R1.md` | docs | 5256 | 177 | `9c3c0437628b` |  |
| `packages/composition/docs/SUCCESSOR_CONTRACT_R1.md` | docs | 5894 | 218 | `58abc9daa6af` |  |
| `packages/composition/docs/VERIFICATION_OBLIGATION_R1.md` | docs | 5341 | 179 | `116b568f6708` |  |
| `packages/composition/formal/EffectReplayFence.ReconciliationIsUnreachable.cfg` | config | 78 | 3 | `e1211635f1b7` |  |
| `packages/composition/formal/EffectReplayFence.TerminalCommittedWithoutEffectIsUnreachable.cfg` | config | 94 | 3 | `e93fd8fd6d96` |  |
| `packages/composition/formal/EffectReplayFence.UnindexedUncertaintyIsUnreachable.cfg` | config | 84 | 3 | `697cb6c55cb5` |  |
| `packages/composition/formal/EffectReplayFence.cfg` | config | 275 | 12 | `63f4beb1b563` |  |
| `packages/composition/formal/EffectReplayFence.tla` | core | 4468 | 127 | `96b2ee6b25ca` |  |
| `packages/composition/formal/Lego21OwnerBoundary.cfg` | config | 492 | 19 | `453513b585a2` |  |
| `packages/composition/formal/Lego21OwnerBoundary.direct-egress.cfg` | config | 493 | 19 | `ab12836dba65` |  |
| `packages/composition/formal/Lego21OwnerBoundary.direct-local.cfg` | config | 494 | 19 | `6c3269dbb34f` |  |
| `packages/composition/formal/Lego21OwnerBoundary.foreign-evidence-probe.cfg` | config | 148 | 9 | `fa8b921e36f0` |  |
| `packages/composition/formal/Lego21OwnerBoundary.foreign-receipt-probe.cfg` | config | 155 | 9 | `884a5d0c0bac` |  |
| `packages/composition/formal/Lego21OwnerBoundary.harness-local.cfg` | config | 493 | 19 | `a5970177ffdd` |  |
| `packages/composition/formal/Lego21OwnerBoundary.readiness-probe.cfg` | config | 153 | 9 | `1a17016e7986` |  |
| `packages/composition/formal/Lego21OwnerBoundary.receipt-probe.cfg` | config | 162 | 9 | `e181f66ad8c6` |  |
| `packages/composition/formal/Lego21OwnerBoundary.sourcecut-probe.cfg` | config | 152 | 9 | `96bfd4f35f21` |  |
| `packages/composition/formal/Lego21OwnerBoundary.tla` | core | 10861 | 253 | `582bdaa756ce` |  |
| `packages/composition/formal/README.md` | docs | 24457 | 216 | `0fbacefa742f` |  |
| `packages/composition/mise.toml` | config | 10476 | 217 | `c606cf60ebe2` |  |
| `packages/composition/planning/lego-plan-r1.json` | config | 30579 | 620 | `b0bb89efcf6c` | 1 |
| `packages/composition/policies/research-adopted-r1/README.md` | docs | 2344 | 46 | `8fc11a23ad46` |  |
| `packages/composition/policies/research-adopted-r1/data.json` | config | 928 | 31 | `2bb6ea1d8c03` |  |
| `packages/composition/policies/research-adopted-r1/policy.rego` | core | 925 | 28 | `507b17934f42` |  |
| `packages/composition/policies/research-adopted-r1/policy_test.rego` | core | 1807 | 67 | `3aacea7abc3d` |  |
| `packages/composition/profiles/admission/admission-interactive-circuit-r1.json` | config | 8271 | 253 | `5f64a309d716` | 1 |
| `packages/composition/profiles/admission/admission-workload-circuit-r1.json` | config | 6281 | 187 | `12b21ec58528` | 1 |
| `packages/composition/pyproject.toml` | config | 1203 | 46 | `df8b932c805f` |  |
| `packages/composition/scripts/check_standard_native_enterprise_r2.py` | core | 3551 | 97 | `e5874ac8ee90` |  |
| `packages/composition/scripts/pacti_timeout_model.py` | core | 6697 | 166 | `878a17759b77` |  |
| `packages/composition/scripts/pacti_timeout_obligation_r1.py` | core | 10804 | 286 | `4f83f9d30168` |  |
| `packages/composition/scripts/verify_effect_replay_formal.sh` | core | 3115 | 57 | `3cdaab972640` |  |
| `packages/composition/src/ordivon_composition/__init__.py` | core | 1187 | 45 | `987109b58ade` |  |
| `packages/composition/src/ordivon_composition/cognitive_circuit_r1.py` | core | 18281 | 449 | `26ece4dc4993` |  |
| `packages/composition/src/ordivon_composition/cross_domain_binding_r3.py` | core | 1973 | 62 | `13eba954ebcc` |  |
| `packages/composition/src/ordivon_composition/effect_reconciliation_r1.py` | core | 5773 | 129 | `09ca8db5cef3` |  |
| `packages/composition/src/ordivon_composition/evidence/standard-native-enterprise-r2-dogfood-20260914.json` | evidence | 19437 | 447 | `3ce88cf3a786` | 1 |
| `packages/composition/src/ordivon_composition/interface_contract_r2.py` | core | 6884 | 182 | `b4d4a2906690` |  |
| `packages/composition/src/ordivon_composition/research_artifact_gate_r3.py` | core | 5895 | 160 | `1d166249ae97` |  |
| `packages/composition/src/ordivon_composition/schemas/cognitive-circuit-manifest-v1.schema.json` | schemas | 6122 | 209 | `0d029cf5cf76` |  |
| `packages/composition/src/ordivon_composition/schemas/composition-gate-result-v1.schema.json` | schemas | 1756 | 58 | `77ade4b7f99b` |  |
| `packages/composition/src/ordivon_composition/schemas/cross-domain-verification-r3-binding.schema.json` | schemas | 4516 | 131 | `cadf55501ad3` |  |
| `packages/composition/src/ordivon_composition/schemas/experimental-episode-binding-r1.schema.json` | schemas | 7155 | 341 | `53f0e5a6ecb5` |  |
| `packages/composition/src/ordivon_composition/schemas/interface-compatibility-result-v1.schema.json` | schemas | 3262 | 110 | `3ec33aca328a` |  |
| `packages/composition/src/ordivon_composition/schemas/interface-contract-expectation-v1.schema.json` | schemas | 2215 | 49 | `5ab9793ca4cb` |  |
| `packages/composition/src/ordivon_composition/schemas/interface-contract-observation-v1.schema.json` | schemas | 2743 | 97 | `4cdb57988e1a` |  |
| `packages/composition/src/ordivon_composition/schemas/standard-native-profile-projection-v1.schema.json` | schemas | 3817 | 113 | `c81122817282` |  |
| `packages/composition/src/ordivon_composition/schemas/successor-contract-v1.schema.json` | schemas | 4360 | 150 | `56fdd2917ab7` |  |
| `packages/composition/src/ordivon_composition/schemas/successor-gate-result-v1.schema.json` | schemas | 2070 | 76 | `369aa3130ef4` |  |
| `packages/composition/src/ordivon_composition/schemas/verification-obligation-set-v1.schema.json` | schemas | 3252 | 103 | `520d1b8a57a5` |  |
| `packages/composition/src/ordivon_composition/schemas/verifier-binding-set-v1.schema.json` | schemas | 2542 | 86 | `ff70a1e9368c` |  |
| `packages/composition/src/ordivon_composition/schemas/verifier-resolution-v1.schema.json` | schemas | 3266 | 104 | `1cd24ca64857` |  |
| `packages/composition/src/ordivon_composition/successor_contract_r1.py` | core | 11430 | 279 | `dfb2f315a11d` |  |
| `packages/composition/src/ordivon_composition/verification_impact.py` | core | 30790 | 662 | `a07ab628c8b6` |  |
| `packages/composition/src/ordivon_composition/verification_obligation_r1.py` | core | 33557 | 770 | `a357afa852c5` |  |
| `packages/composition/src/ordivon_composition/web_security_gate_r3.py` | core | 9283 | 259 | `ff3d72d81bf2` |  |
| `packages/composition/tests/fixtures/cross-domain-verification-r3-bindings.json` | tests | 2408 | 65 | `8a45e79a68a0` | 1 |
| `packages/composition/tests/fixtures/gateway-client-interface-contract-r2-dogfood.json` | tests | 2250 | 71 | `976b41d41269` | 1 |
| `packages/composition/tests/fixtures/pacti/pacti-timeout-obligation-r2.json` | tests | 10892 | 233 | `5c97ae291a71` | 1 |
| `packages/composition/tests/fixtures/pacti/pacti-timeout-obligation-spec-r2.json` | tests | 758 | 21 | `aa6d30452ad3` | 1 |
| `packages/composition/tests/test_admission_fabric_r1.py` | tests | 2569 | 71 | `6d2830a5fb7e` |  |
| `packages/composition/tests/test_cognitive_circuit_r1.py` | tests | 18101 | 458 | `5fee12ed6614` |  |
| `packages/composition/tests/test_cross_domain_verification_r3.py` | tests | 19624 | 583 | `9a949ae9d68a` |  |
| `packages/composition/tests/test_effect_reconciliation_r1.py` | tests | 11283 | 311 | `0583187fa61e` |  |
| `packages/composition/tests/test_finance_contractual_execution_consumer.py` | tests | 13360 | 324 | `b96c7cbf373c` |  |
| `packages/composition/tests/test_finance_research_frozen_consumer.py` | tests | 16737 | 406 | `2e7735c5d557` |  |
| `packages/composition/tests/test_gate_evidence_reference_law.py` | tests | 1832 | 53 | `c5205337546f` |  |
| `packages/composition/tests/test_graph_operator_properties.py` | tests | 8201 | 219 | `ee0442af78e0` |  |
| `packages/composition/tests/test_identity_token_grammar.py` | tests | 1735 | 48 | `9a8a03bcd74b` |  |
| `packages/composition/tests/test_interface_contract_core.py` | tests | 3328 | 95 | `ca136975593d` |  |
| `packages/composition/tests/test_interface_contract_r2.py` | tests | 18286 | 489 | `a4d15898cab8` |  |
| `packages/composition/tests/test_native_formal_model_gate.py` | tests | 6405 | 134 | `4b090b2b2be8` |  |
| `packages/composition/tests/test_nonfinite_source_numeric_r21.py` | tests | 9475 | 255 | `a9d4fc2736a2` |  |
| `packages/composition/tests/test_owner_python_binding.py` | tests | 1228 | 36 | `50842bdf7735` |  |
| `packages/composition/tests/test_pacti_timeout_obligation_r1.py` | tests | 12842 | 352 | `42da30261ac0` |  |
| `packages/composition/tests/test_research_adopted_policy.py` | tests | 1841 | 51 | `b67546bd78d8` |  |
| `packages/composition/tests/test_source_json_uniqueness.py` | tests | 2103 | 58 | `19c75d194325` |  |
| `packages/composition/tests/test_successor_contract_r1.py` | tests | 13143 | 337 | `70a71d881d27` |  |
| `packages/composition/tests/test_verification_obligation_r1.py` | tests | 135984 | 3388 | `00ec682541b7` |  |
| `packages/composition/uv.lock` | config | 58619 | — | `78940e05a0ba` |  |

### control-plugin — extensions/ordivon-control-plane/（2 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `extensions/ordivon-control-plane/mcp.json` | config | 213 | 9 | `7a2c11d0ff6a` |  |
| `extensions/ordivon-control-plane/plugin.json` | config | 363 | 7 | `3d265f7e842e` |  |

### runtime — services/runtime/（452 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `services/runtime/.config/nextest.toml` | config | 170 | 4 | `8166f61917e5` |  |
| `services/runtime/.editorconfig` | other | 259 | — | `8d1a04524e09` |  |
| `services/runtime/.gitattributes` | other | 814 | — | `0ebc7e7bdb7d` |  |
| `services/runtime/.github/CODEOWNERS` | other | 171 | — | `8fcad3261f37` |  |
| `services/runtime/.github/ISSUE_TEMPLATE/bug_report.yml` | config | 2040 | 68 | `d178c7169e64` |  |
| `services/runtime/.github/ISSUE_TEMPLATE/config.yml` | config | 222 | 5 | `a4ccfb874afd` |  |
| `services/runtime/.github/ISSUE_TEMPLATE/feature_request.yml` | config | 1291 | 40 | `b0085e938686` |  |
| `services/runtime/.github/actionlint.yaml` | config | 76 | 5 | `6d062429a44d` |  |
| `services/runtime/.github/pull_request_template.md` | docs | 253 | 11 | `9069fbaca6cd` |  |
| `services/runtime/.github/workflows/release-acceptance.yml` | config | 1149 | 32 | `6a1cd7ae09b2` |  |
| `services/runtime/.gitignore` | other | 221 | — | `64d3caafb314` |  |
| `services/runtime/.gitleaks.toml` | config | 453 | 13 | `2938b8d54c31` |  |
| `services/runtime/.gitleaksignore` | other | 411 | — | `33fd29a2976f` |  |
| `services/runtime/.ordivon/project.yaml` | config | 723 | 32 | `446c322ea481` |  |
| `services/runtime/.ordivon/publication.yaml` | config | 937 | 26 | `ba4786ab030e` |  |
| `services/runtime/.ordivon/rights.yaml` | config | 610 | 16 | `e1a8bab6c381` |  |
| `services/runtime/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `services/runtime/AGENTS.md` | docs | 6485 | 56 | `4dddd76efa90` |  |
| `services/runtime/CHANGELOG.md` | docs | 38144 | 172 | `147b139195d9` |  |
| `services/runtime/CONTRIBUTING.md` | docs | 3747 | 77 | `c6c8f2bd32a5` |  |
| `services/runtime/Cargo.lock` | config | 75320 | — | `c9751328e432` |  |
| `services/runtime/Cargo.toml` | config | 1213 | 35 | `e29d5444cc88` |  |
| `services/runtime/LICENSE` | other | 11357 | — | `c71d239df917` |  |
| `services/runtime/README.md` | docs | 13734 | 216 | `c8c16d4bcb63` | 1 |
| `services/runtime/SECURITY.md` | docs | 4977 | 65 | `5dad0e88efc8` |  |
| `services/runtime/crates/ordivon-runtime-core/Cargo.toml` | config | 2265 | 78 | `31fc279a4963` |  |
| `services/runtime/crates/ordivon-runtime-core/migrations/runtime/0001_runtime.sql` | schemas | 5862 | 142 | `9c5e0ccf94b0` |  |
| `services/runtime/crates/ordivon-runtime-core/migrations/runtime/0002_orphan_recovery.sql` | schemas | 834 | 27 | `08361881c9f5` |  |
| `services/runtime/crates/ordivon-runtime-core/migrations/runtime/0003_terminal_repair.sql` | schemas | 854 | 27 | `464c9b769dac` |  |
| `services/runtime/crates/ordivon-runtime-core/migrations/runtime/0004_orphan_reclaim.sql` | schemas | 1118 | 39 | `b76afbfaf706` |  |
| `services/runtime/crates/ordivon-runtime-core/migrations/runtime/0005_condition_retirement.sql` | schemas | 3520 | 79 | `ae8e45dde797` |  |
| `services/runtime/crates/ordivon-runtime-core/migrations/runtime/0006_workspace_patch_retirement.sql` | schemas | 49 | 1 | `90288d85d61b` |  |
| `services/runtime/crates/ordivon-runtime-core/sql/pg_fresh_epoch.sql` | schemas | 4594 | 86 | `124bb8b23ad5` |  |
| `services/runtime/crates/ordivon-runtime-core/src/bin/ordivon-runtime-doctor.rs` | core | 2404 | 69 | `9093790f94ec` |  |
| `services/runtime/crates/ordivon-runtime-core/src/bin/ordivon-runtime-inspect.rs` | core | 14744 | 345 | `f46dd626d53e` |  |
| `services/runtime/crates/ordivon-runtime-core/src/bin/ordivon-runtime-job-fixture.rs` | core | 8457 | 273 | `78cf7fe03d30` |  |
| `services/runtime/crates/ordivon-runtime-core/src/bin/ordivon-runtime-repair.rs` | core | 6015 | 145 | `17cdd1176072` |  |
| `services/runtime/crates/ordivon-runtime-core/src/bin/ordivon-runtime-runner.rs` | core | 916 | 30 | `f003c83f6ccd` |  |
| `services/runtime/crates/ordivon-runtime-core/src/bin/ordivon-runtime-windows-deploy.rs` | core | 77213 | 2089 | `fca1abdf21cd` |  |
| `services/runtime/crates/ordivon-runtime-core/src/lib.rs` | core | 7254 | 120 | `f4e598a09a85` |  |
| `services/runtime/crates/ordivon-runtime-core/src/pg_admission.rs` | core | 129633 | 3026 | `0bb75cffec22` |  |
| `services/runtime/crates/ordivon-runtime-core/src/pg_dispatch.rs` | core | 10352 | 312 | `e85e03c8c7d6` |  |
| `services/runtime/crates/ordivon-runtime-core/src/pg_readback.rs` | core | 14601 | 364 | `26ed9693a1fb` |  |
| `services/runtime/crates/ordivon-runtime-core/src/resource_fit.rs` | core | 1168 | 36 | `a638d9d82bfb` |  |
| `services/runtime/crates/ordivon-runtime-core/src/resource_scheduling.rs` | core | 12758 | 351 | `c6f18a323370` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/artifact_release_state.rs` | core | 29209 | 750 | `eac2bbcbeeaa` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/attempt_supervisor_owner_storage.sql` | schemas | 211 | 5 | `bbce86a7204d` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/authority_contract.rs` | core | 30941 | 746 | `1fbc0b51207b` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/control_primitives.rs` | core | 3524 | 110 | `2b9d06cfb065` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/doctor.rs` | core | 23077 | 606 | `dc41873ffb01` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine.rs` | core | 71738 | 1860 | `cc25e4468209` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/admission.rs` | core | 24650 | 590 | `c2ef0903f0c9` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/admission_validation.rs` | core | 13393 | 348 | `d0bb9d6242af` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/artifact_projection.rs` | core | 18223 | 447 | `07d4eea5710a` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/construction.rs` | core | 11201 | 284 | `97503ad01511` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/execution.rs` | core | 36307 | 832 | `e188bc948424` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/execution_environment.rs` | core | 3429 | 101 | `1c8b94c41875` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/execution_preparation.rs` | core | 22904 | 512 | `9997c12d3a37` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/input_bindings.rs` | core | 14943 | 392 | `1db49d64a4e8` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/job_activity_evidence.rs` | core | 4508 | 127 | `e33c21eb038a` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/job_control.rs` | core | 12761 | 311 | `ce7468070883` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/launch_identity.rs` | core | 32639 | 676 | `162092b42827` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/observation_projection.rs` | core | 9763 | 242 | `9f98a3ddba42` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/orphan_recovery.rs` | core | 11100 | 236 | `452d17d1724f` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/output.rs` | core | 6521 | 211 | `4ae24165c459` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/prepared_binding_recovery.rs` | core | 13061 | 295 | `2348f5738ea0` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/provider_commitments.rs` | core | 8570 | 196 | `80bcb6ff9f88` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/reconciliation.rs` | core | 29303 | 707 | `dab8d1c42e7e` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/release.rs` | core | 9098 | 219 | `9625996c2ad7` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/terminal_commit.rs` | core | 5213 | 119 | `53ad6523920d` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/terminal_evidence.rs` | core | 12025 | 295 | `e6ea72ea8c8f` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/workspace.rs` | core | 12697 | 300 | `62f511b60baf` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/workspace_evidence.rs` | core | 2809 | 77 | `8847191b00ae` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/error.rs` | core | 7794 | 217 | `4ff4f0d648ce` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/error/sqlite.rs` | core | 893 | 21 | `c796707e1d4b` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/error/universal.rs` | core | 1955 | 31 | `67aa9ffa4a45` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/evidence.rs` | core | 20461 | 534 | `b93c91d96051` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/execution_provider.rs` | core | 22244 | 576 | `7a5c6894f6ad` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/execution_provider_storage.sql` | schemas | 203 | 5 | `782ac9947be0` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/host_dependency.rs` | core | 5257 | 132 | `b67709c049d9` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/host_dependency_storage.sql` | schemas | 192 | 5 | `686eab278a5c` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/inspection.rs` | core | 4905 | 144 | `5092443a9f81` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/inspection/job.rs` | core | 20471 | 499 | `3942eab79010` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/inspection/operator.rs` | core | 75660 | 1813 | `3837c20def3b` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/inspection/operator/archive.rs` | core | 13615 | 345 | `9f29f43cd90c` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/inspection/summary_query_tests.rs` | core | 9140 | 225 | `d86da9bb6523` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/integration_tests.rs` | core | 146371 | 3840 | `36a1ad655d83` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/job_attempt_state.rs` | core | 30016 | 802 | `310295e9f7b2` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/lifecycle_locks.rs` | core | 4794 | 151 | `4c28c1b02392` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/mod.rs` | core | 7243 | 137 | `5c7b3ccc9118` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/operation_circuit.rs` | core | 28056 | 679 | `82cb7f23d25a` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime.rs` | core | 11486 | 278 | `6d611b83ac8e` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/artifact.rs` | core | 5071 | 119 | `e8d6068aea85` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/job.rs` | core | 29252 | 678 | `16a0c7f1fdab` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/native_stop.rs` | core | 3075 | 81 | `56e7a77e0acc` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/node_query.rs` | core | 8278 | 136 | `e598dc2f6b18` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/reconciliation.rs` | core | 37468 | 739 | `e9a5652ce00b` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/release.rs` | core | 6550 | 148 | `425c02956a30` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/scheduling.rs` | core | 14225 | 343 | `ed0ed40cf14c` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/workspace.rs` | core | 11851 | 255 | `3d1924c8e0c5` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/platform/linux.rs` | core | 41815 | 1112 | `b4fc4aa08cbb` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/platform/mod.rs` | core | 497 | 10 | `0b7110774fa1` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/registry.rs` | core | 58397 | 1556 | `acc15af1bda0` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/registry/admission.rs` | core | 25420 | 588 | `61f3c4021a00` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/registry/lifecycle.rs` | core | 38527 | 875 | `173b4066f6b1` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/registry/query.rs` | core | 50867 | 1087 | `123e4bac5ec2` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/registry/reconciliation.rs` | core | 4969 | 119 | `9991b31ea0da` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/registry/recovery.rs` | core | 18931 | 418 | `9dc840b18a00` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/registry/storage.rs` | core | 22303 | 543 | `a4589159afc5` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/registry_storage.rs` | core | 9753 | 274 | `70553c7020d3` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/repair.rs` | core | 50427 | 1348 | `dffdb20eb4b9` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/reservation_state.rs` | core | 11599 | 330 | `9d64bc0cf7e0` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/runtime_release_storage.sql` | schemas | 602 | 14 | `cc41694fd3d5` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/supervisor.rs` | core | 19116 | 550 | `cb7e94de2c4f` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs` | core | 401775 | 10788 | `31372e533592` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/types.rs` | core | 80024 | 2097 | `04f79b92d26b` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/windows.rs` | core | 109555 | 2875 | `90a484b67698` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/windows_broker.rs` | core | 15506 | 475 | `254b474a9ff2` |  |
| `services/runtime/crates/ordivon-runtime-core/src/runtime/workspace_state.rs` | core | 4975 | 140 | `7a95df211198` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/config.rs` | core | 8490 | 244 | `b90831d67cf4` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/error.rs` | core | 3267 | 95 | `06cc48b409c3` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/fsutil.rs` | core | 17450 | 556 | `42471dc478af` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/mod.rs` | core | 3926 | 90 | `6b5ca5ca2886` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/mutation.rs` | core | 11983 | 296 | `aba15f4afe2e` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/projection.rs` | core | 2157 | 58 | `95a0005873a6` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/resource_receipt.rs` | core | 10699 | 300 | `5f3bc76cade6` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/runner.rs` | core | 66905 | 1811 | `f8f955eb5256` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/tests.rs` | core | 160946 | 4382 | `78424c3e31eb` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/types.rs` | core | 32287 | 881 | `c6dd5f03463c` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/workspace.rs` | core | 4340 | 124 | `5171b48f23a1` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/workspace/changes.rs` | core | 25567 | 734 | `5fbf76933f55` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/workspace/close_recovery.rs` | core | 53932 | 1322 | `6036b22e9c83` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/workspace/file_io.rs` | core | 13807 | 393 | `fb983e5d9ad9` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/workspace/paths_git.rs` | core | 14621 | 410 | `d13d2bcfee86` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/workspace/records.rs` | core | 13650 | 380 | `ad4a1856cdbf` |  |
| `services/runtime/crates/ordivon-runtime-core/src/universal/workspace/source_state.rs` | core | 28666 | 701 | `23c230b39725` |  |
| `services/runtime/crates/ordivon-runtime-core/src/windows_security.rs` | core | 10457 | 321 | `902cba125567` |  |
| `services/runtime/crates/ordivon-runtime-core/tests/platform_owner_boundary.rs` | tests | 2030 | 58 | `77da5a2e12ff` |  |
| `services/runtime/crates/ordivon-runtime-core/tests/sqlite_unsigned_contract.rs` | tests | 1227 | 35 | `d92f0e0baf40` |  |
| `services/runtime/crates/ordivon-runtime-core/tests/systemd_supervisor.rs` | tests | 8991 | 279 | `d82275124052` |  |
| `services/runtime/crates/ordivon-runtime-mcp/Cargo.toml` | config | 1376 | 47 | `9f01cfb16db9` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/access_auth.rs` | core | 11338 | 298 | `a8d7cd41e305` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/lib.rs` | core | 363 | 9 | `a95307b60ec3` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/main.rs` | core | 54738 | 1475 | `0e21da663f36` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/pg_auth.rs` | core | 6733 | 173 | `20748527544b` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/pg_main.rs` | core | 4773 | 112 | `cb705190ffea` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/contract.rs` | core | 26562 | 665 | `5e1bd1104fb8` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/execution_binding.rs` | core | 10329 | 240 | `5c57719b34b9` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/handler.rs` | core | 7672 | 203 | `0c1dafa13886` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/input_ingress.rs` | core | 7044 | 207 | `de6861d8c96c` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/mod.rs` | core | 5547 | 142 | `0d9ad3bcbd64` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/pg_output_contract.rs` | core | 7882 | 198 | `c83f07181374` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/pg_server.rs` | core | 17863 | 234 | `33375cfd9a6f` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/server_state.rs` | core | 27498 | 658 | `0208fd393161` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/tests.rs` | core | 93875 | 2602 | `95550a198c51` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/tests/projection_contract.rs` | tests | 3369 | 100 | `61766ac6bc6b` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/tests/stage_trace.rs` | tests | 4236 | 113 | `727223d575dc` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/tests/tool_catalog.rs` | tests | 13671 | 361 | `b58f2915d470` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/tool_error.rs` | core | 17464 | 472 | `f3b06bdf275c` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/tools.rs` | core | 55172 | 1021 | `37ab22a10b78` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/server/tracing.rs` | core | 3998 | 118 | `90652812b951` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/trace.rs` | core | 4193 | 123 | `f257c29d33f3` |  |
| `services/runtime/crates/ordivon-runtime-mcp/src/windows_service.rs` | core | 5317 | 171 | `730de0f81b0e` |  |
| `services/runtime/crates/ordivon-runtime-mcp/tests/pg_vertical.rs` | tests | 103841 | 2740 | `ed26cef04041` |  |
| `services/runtime/deny.toml` | config | 904 | 33 | `ac7cb33e87bc` |  |
| `services/runtime/docs/NATIVE_RUNTIME_NODES_R1.md` | docs | 17965 | 285 | `e110b7cebafc` |  |
| `services/runtime/docs/RUNTIME_WINDOWS_R6C_ACCEPTANCE_R1.md` | docs | 13520 | 333 | `c8cc8ebe9c98` |  |
| `services/runtime/docs/STANDARDS_FIRST_W2_BOUNDARY_R1.md` | docs | 2799 | 73 | `1a429bb3e442` |  |
| `services/runtime/docs/agent-ux.md` | docs | 38542 | 184 | `c47ff6c94186` |  |
| `services/runtime/docs/audits/2026-11-07-runtime-owner-audit.md` | docs | 34226 | 214 | `8258c0e362e1` | 1 |
| `services/runtime/docs/audits/2026-11-08-runtime-modernization-brainstorm.md` | docs | 32713 | 294 | `3aa7c93f00e9` | 1 |
| `services/runtime/docs/authority.md` | docs | 3304 | 68 | `1250d2491749` | 1 |
| `services/runtime/docs/compatibility.md` | docs | 12250 | 79 | `5f24f5f4f20c` |  |
| `services/runtime/docs/data-and-privacy.md` | docs | 13813 | 184 | `9deab122010c` | 1 |
| `services/runtime/docs/effect-comparison.md` | docs | 4051 | 72 | `6b7ce4d010d0` |  |
| `services/runtime/docs/effect-kernel.md` | docs | 23803 | 288 | `77b30f4c733c` | 1 |
| `services/runtime/docs/evidence/windows-r6c-c3-pass-20260920.json` | evidence | 1662 | 52 | `a804bc043bf8` | 1 |
| `services/runtime/docs/guides/agent-runtime.md` | docs | 12121 | 118 | `c2c038e34fa4` | 1 |
| `services/runtime/docs/guides/operator-runtime.md` | docs | 14105 | 125 | `0e80baecf8a2` | 1 |
| `services/runtime/docs/guides/runtime-legos.md` | docs | 12651 | 119 | `841e2fe92680` | 1 |
| `services/runtime/docs/operations.md` | docs | 75630 | 763 | `827b3fa36434` | 1 |
| `services/runtime/docs/quickstart.md` | docs | 8006 | 189 | `fbab6c48e858` | 1 |
| `services/runtime/docs/recovery.md` | docs | 13219 | 94 | `aac620a1c361` |  |
| `services/runtime/docs/reference/tools.md` | docs | 18505 | 83 | `bb35ea26fb35` | 1 |
| `services/runtime/docs/releases.md` | docs | 11924 | 187 | `ceaf2a672774` | 1 |
| `services/runtime/docs/runtime-decomposition-history.md` | docs | 15431 | 174 | `744d1de8329d` |  |
| `services/runtime/docs/runtime.md` | docs | 78259 | 353 | `81c1d92fb2d7` | 1 |
| `services/runtime/docs/status.md` | docs | 14009 | 151 | `8cb08fd4bc51` | 1 |
| `services/runtime/evidence/harness-h2-runtime-r2-live-d50f609-20260731.json` | evidence | 9097 | 221 | `51ac196a80c9` | 1 |
| `services/runtime/examples/runtime-demo/inspect_policy.py` | core | 159 | 9 | `64db6bea6507` |  |
| `services/runtime/examples/runtime-demo/policy.py` | core | 144 | 7 | `2d436a857fe8` |  |
| `services/runtime/examples/runtime-demo/report.py` | core | 482 | 25 | `cc8c25f61b05` |  |
| `services/runtime/examples/runtime-demo/test_policy.py` | tests | 362 | 16 | `c0852dce272d` |  |
| `services/runtime/formal/README.md` | docs | 35921 | 543 | `5583e5014b5e` |  |
| `services/runtime/formal/RuntimeDispatchR1.cfg` | config | 565 | 25 | `09c48ff95113` |  |
| `services/runtime/formal/RuntimeDispatchR1.foreign-result-probe.cfg` | config | 143 | 9 | `440e6c8e7f3c` |  |
| `services/runtime/formal/RuntimeDispatchR1.tla` | core | 11926 | 285 | `fae5d12db3dd` |  |
| `services/runtime/formal/RuntimeDispatchR1.trace-r1.acceptance.json` | config | 2876 | 55 | `4626029d7d08` | 1 |
| `services/runtime/formal/RuntimeDispatchR1.trace-r1.json` | config | 11450 | 202 | `1ef330835491` | 2 |
| `services/runtime/formal/RuntimePgCutoverR1.cfg` | config | 416 | 15 | `d83e57404647` |  |
| `services/runtime/formal/RuntimePgCutoverR1.tla` | core | 10412 | 263 | `d367538dd66c` |  |
| `services/runtime/formal/RuntimeResourceQueueR1.cfg` | config | 213 | 8 | `b07a44b68e93` |  |
| `services/runtime/formal/RuntimeResourceQueueR1.tla` | core | 2467 | 29 | `027b69d005c4` |  |
| `services/runtime/formal/RuntimeWindowsFirstPgR1.cfg` | config | 151 | 7 | `9ceb94ac44d4` |  |
| `services/runtime/formal/RuntimeWindowsFirstPgR1.tla` | core | 3623 | 114 | `72720ab3d06c` |  |
| `services/runtime/formal/WorkspaceConsumerCloseR1.cfg` | config | 206 | 7 | `c95464c370e3` |  |
| `services/runtime/formal/WorkspaceConsumerCloseR1.liveness.cfg` | config | 255 | 8 | `b5198eabd5b9` |  |
| `services/runtime/formal/WorkspaceConsumerCloseR1.r2-candidate.cfg` | config | 230 | 7 | `9347959fdcf1` |  |
| `services/runtime/formal/WorkspaceConsumerCloseR1.reachability.cfg` | config | 68 | 3 | `03965a70213f` |  |
| `services/runtime/formal/WorkspaceConsumerCloseR1.tla` | core | 4829 | 162 | `5d4a8a78d7a5` |  |
| `services/runtime/formal/toolchain.lock.json` | config | 587 | 13 | `38644c24273f` | 1 |
| `services/runtime/mise.toml` | config | 7120 | 144 | `0a8da5bac70f` |  |
| `services/runtime/packaging/systemd/ordivon-runtime-lifecycle.service` | config | 722 | 18 | `a3df3c32c926` |  |
| `services/runtime/packaging/systemd/ordivon-runtime-lifecycle.timer` | config | 206 | — | `063640ef4406` |  |
| `services/runtime/packaging/systemd/ordivon-runtime-storage-pressure.service` | config | 884 | 12 | `b4b022da287f` |  |
| `services/runtime/packaging/systemd/ordivon-runtime-storage-pressure.timer` | config | 282 | — | `b4cd71446c9b` |  |
| `services/runtime/packaging/systemd/ordivon-runtime.env.example` | other | 4412 | — | `45ab4e70ea06` |  |
| `services/runtime/packaging/systemd/ordivon-runtime.service` | config | 430 | 21 | `6b0722ca32ea` |  |
| `services/runtime/packaging/systemd/ordivon-storage-pressure-control.json` | config | 371 | 13 | `9020de96ae50` | 1 |
| `services/runtime/packaging/systemd/ordivon-workspace-retention.json` | config | 935 | 33 | `a169b38b5f93` | 1 |
| `services/runtime/packaging/systemd/tmpfiles.d/ordivon.conf` | config | 415 | 8 | `350258ddfd7f` |  |
| `services/runtime/packaging/windows/materialize-ordivon-runtime-service.ps1` | core | 16533 | 405 | `6dad2d89b52c` |  |
| `services/runtime/packaging/windows/ordivon-runtime.env.example` | other | 3461 | — | `aaf7ded906df` |  |
| `services/runtime/planning/EXECUTION_FABRIC_R1_ROADMAP.md` | docs | 674 | 17 | `e135cb5c66da` |  |
| `services/runtime/planning/WINDOWS_AUTHORITY_FACTORIZATION_EXECUTION_PLAN_R1.md` | docs | 9861 | 204 | `ff2188e7a659` |  |
| `services/runtime/planning/WINDOWS_AUTHORITY_FACTORIZATION_LEGO_R1.json` | config | 15789 | 495 | `3ffe80fa5ea2` | 1 |
| `services/runtime/planning/WORKSPACE_CONSUMER_LIFECYCLE_R21_EXECUTION_PLAN.md` | docs | 18244 | 228 | `314efbd85153` |  |
| `services/runtime/planning/WORKSPACE_CONSUMER_LIFECYCLE_R21_SPEC.md` | docs | 21717 | 190 | `2fde9c4c23bf` |  |
| `services/runtime/planning/invariants-r1.json` | config | 14681 | 249 | `d4068a69d310` | 1 |
| `services/runtime/planning/lego-plan-r1.json` | config | 83087 | 1269 | `570cf700b92a` | 1 |
| `services/runtime/planning/state-responsibility-census-r1.json` | config | 10394 | 289 | `94ff043b1093` | 1 |
| `services/runtime/planning/test-taxonomy-r1.json` | config | 8618 | 213 | `f8af79914945` | 1 |
| `services/runtime/planning/tool-necessity-audit-r1.json` | config | 9338 | 290 | `fb74fba0b1eb` | 1 |
| `services/runtime/platform/windows/Ordivon.WindowsJobFixture.cs` | core | 10865 | 286 | `55229611224b` |  |
| `services/runtime/platform/windows/Ordivon.WindowsJobLauncher.cs` | core | 122201 | 2966 | `76f4e54da2b0` |  |
| `services/runtime/platform/windows/Ordivon.WindowsPrivilegedBroker.cs` | core | 44339 | 1018 | `b067f9198d5d` |  |
| `services/runtime/pyproject.toml` | config | 156 | 11 | `ffb3e64889e3` |  |
| `services/runtime/requirements-runtime-pg-operator.in` | other | 15 | — | `6e63821a5f9c` |  |
| `services/runtime/requirements-runtime-pg-operator.lock.txt` | other | 416 | 6 | `3122a08a9d3b` |  |
| `services/runtime/requirements-tooling.lock.txt` | other | 1766 | 22 | `beb9ccb72cf3` |  |
| `services/runtime/requirements-tooling.txt` | other | 13 | 1 | `2946681ff837` |  |
| `services/runtime/research/README.md` | research | 2407 | 35 | `7d97a7f70f93` |  |
| `services/runtime/research/authority/CURRENT.json` | research | 507 | 9 | `77c0f8982c72` | 1 |
| `services/runtime/research/authority/publications/227cc7e253de5fa10be7cbecdfd2e7d84724b507c4a0504836fc63996ac53497.json` | evidence | 12850 | 343 | `227cc7e253de` | 1 |
| `services/runtime/research/authority/publications/350d042df3c01399cf9314c6954f0c3f4c45bdeb660aa275556e098a77ec62eb.json` | evidence | 7570 | 181 | `350d042df3c0` | 1 |
| `services/runtime/research/authority/publications/9c67d1b4094ce85a2465579430bb1a941f1923457087fb74cde0642d7b9a51b3.json` | evidence | 18979 | 482 | `9c67d1b4094c` | 1 |
| `services/runtime/research/authority/publications/a39e5ec16ed955bc02b1e11db6f120f5f812e093324a6a3171d368f710a8665b.json` | evidence | 2852 | 89 | `a39e5ec16ed9` | 1 |
| `services/runtime/research/authority/publications/e06cac5f69942068fabe80dc5da22fc1fb566d3004ce4951df545534fda289d9.json` | evidence | 15799 | 409 | `e06cac5f6994` | 1 |
| `services/runtime/research/authority/publications/e2eb5a6d46c50390ec4b666cd6faba5528ff42b2c9e1bfb75cb45b6c0c4177ed.json` | evidence | 5396 | 139 | `e2eb5a6d46c5` | 1 |
| `services/runtime/research/core/DERIVED-RUNTIME-CORE-LAWS.md` | research | 2668 | 49 | `63a16d120d55` |  |
| `services/runtime/research/core/ENGINEERING-CONSUMPTION.md` | research | 1102 | 16 | `d23f9a3c3497` |  |
| `services/runtime/research/core/FOUNDATION-FAMILIES.md` | research | 2821 | 47 | `24b61770f44a` |  |
| `services/runtime/research/core/HISTORICAL-EF27.md` | research | 967 | 23 | `1c2c32c58495` |  |
| `services/runtime/research/core/OWNER-BRIDGES.md` | research | 2674 | 43 | `6d342519e5f1` |  |
| `services/runtime/research/core/README.md` | research | 933 | 15 | `a74909d259e7` |  |
| `services/runtime/research/core/REGISTRY-PROVENANCE.md` | research | 6938 | 117 | `c53d705f201d` |  |
| `services/runtime/research/core/RUNTIME-ARCHITECTURE.md` | research | 3064 | 59 | `a1fa677d1893` |  |
| `services/runtime/research/core/SATURATION-NEGATIVE-EVIDENCE.md` | research | 2721 | 37 | `16b59661a334` |  |
| `services/runtime/research/core/SBF-OWNER-ROLE-MAP.md` | research | 4833 | 56 | `56210d8dc872` |  |
| `services/runtime/research/engineering/RUNTIME-FOUNDATIONS-V1-ENGINEERING-CONSUMPTION-CLOSEOUT.md` | research | 17459 | 539 | `595f4571e988` | 1 |
| `services/runtime/research/engineering/RUNTIME-FOUNDATIONS-V1-ENGINEERING-CONSUMPTION-R2-CONSUMERS.md` | research | 12937 | 357 | `87ac4b328788` | 1 |
| `services/runtime/research/engineering/RUNTIME-FOUNDATIONS-V1-ENGINEERING-CONSUMPTION-R3-INTEGRATION.md` | research | 20979 | 754 | `915c0672af09` | 1 |
| `services/runtime/research/engineering/RUNTIME-FOUNDATIONS-V1-ENGINEERING-CONSUMPTION.md` | research | 17130 | 227 | `e6b1fd7193f2` | 1 |
| `services/runtime/research/foundations/README.md` | research | 7403 | 189 | `37b253faf582` | 1 |
| `services/runtime/research/foundations/RF0-CLOSEOUT.json` | research | 2358 | 46 | `48f3b85f0151` | 1 |
| `services/runtime/research/foundations/RF0-CONTINUATION.md` | research | 3741 | 114 | `cec2b4fb8038` | 1 |
| `services/runtime/research/foundations/RF0-RUNTIME-PHENOMENON-SPACE.md` | research | 40485 | 1347 | `f94040c63347` | 1 |
| `services/runtime/research/foundations/RF0-SOURCES.md` | research | 8322 | 192 | `b269d5443c5f` | 1 |
| `services/runtime/research/foundations/RF1-CLOSEOUT.json` | research | 2828 | 52 | `64ae3c0f740c` | 1 |
| `services/runtime/research/foundations/RF1-CONTINUATION.md` | research | 5001 | 126 | `a38901a3c05e` | 1 |
| `services/runtime/research/foundations/RF1-SOURCES.md` | research | 10078 | 237 | `7256da8229dc` | 1 |
| `services/runtime/research/foundations/RF1-STATE-CHANGE-EVENT-BEHAVIOR-DYNAMICS.md` | research | 41455 | 1485 | `ffb1aaf6bf28` | 1 |
| `services/runtime/research/foundations/RF10-CLOSEOUT.json` | research | 4932 | 73 | `5990f4f32c39` | 1 |
| `services/runtime/research/foundations/RF10-CONTINUATION.md` | research | 8246 | 170 | `b804dcf9cd94` | 1 |
| `services/runtime/research/foundations/RF10-FAILURE-RECOVERY-RETRY-IDEMPOTENCY-EXACTLY-ONCE.md` | research | 52554 | 2074 | `63c5d7db1487` | 1 |
| `services/runtime/research/foundations/RF10-SOURCES.md` | research | 6900 | 166 | `2f5089dae447` | 1 |
| `services/runtime/research/foundations/RF11-CLOSEOUT.json` | research | 5992 | 82 | `c00f8aea85d3` | 1 |
| `services/runtime/research/foundations/RF11-CONTINUATION.md` | research | 9027 | 181 | `9c3d9094add2` | 1 |
| `services/runtime/research/foundations/RF11-OBSERVATION-EVIDENCE-PROOF-TRUTH-SURFACES.md` | research | 60257 | 2541 | `f53ce378599e` | 1 |
| `services/runtime/research/foundations/RF11-SOURCES.md` | research | 10015 | 263 | `7526d24781b9` | 1 |
| `services/runtime/research/foundations/RF12-CLOSEOUT.json` | research | 5742 | 80 | `2fa232405d78` | 1 |
| `services/runtime/research/foundations/RF12-COMPOSITION-TRANSACTIONS-CROSS-OPERATION-ATOMICITY.md` | research | 58489 | 2389 | `ca41e60e0b69` | 1 |
| `services/runtime/research/foundations/RF12-CONTINUATION.md` | research | 8633 | 178 | `501d80be2a9a` | 1 |
| `services/runtime/research/foundations/RF12-SOURCES.md` | research | 7312 | 184 | `b938dd9b9bf3` | 1 |
| `services/runtime/research/foundations/RF13-CLOSEOUT.json` | research | 6475 | 87 | `735a05570ebd` | 1 |
| `services/runtime/research/foundations/RF13-CONTINUATION.md` | research | 8390 | 180 | `7fc1f23e3234` | 1 |
| `services/runtime/research/foundations/RF13-ISOLATION-CONTAINMENT-TRUST.md` | research | 58434 | 2258 | `c34afa070c87` | 1 |
| `services/runtime/research/foundations/RF13-SOURCES.md` | research | 8374 | 215 | `604203f81f53` | 1 |
| `services/runtime/research/foundations/RF14-CLOSEOUT.json` | research | 6162 | 83 | `4ab34c448b5b` | 1 |
| `services/runtime/research/foundations/RF14-CONTINUATION.md` | research | 8460 | 178 | `62243790b108` | 1 |
| `services/runtime/research/foundations/RF14-DETERMINISM-NONDETERMINISM-AGENT-ACTION.md` | research | 54573 | 2106 | `9f70b8ee8cd8` | 1 |
| `services/runtime/research/foundations/RF14-SOURCES.md` | research | 7094 | 183 | `6941f49b3017` | 1 |
| `services/runtime/research/foundations/RF15-CLOSEOUT.json` | research | 6674 | 94 | `533294be719e` | 1 |
| `services/runtime/research/foundations/RF15-CONTINUATION.md` | research | 8042 | 178 | `a538a9b94413` | 1 |
| `services/runtime/research/foundations/RF15-EXTERNAL-WORLD-OPEN-SYSTEM-EFFECTS.md` | research | 67903 | 3192 | `6e353ccbe876` | 1 |
| `services/runtime/research/foundations/RF15-SOURCES.md` | research | 7186 | 180 | `89db26a80f34` | 1 |
| `services/runtime/research/foundations/RF16-CLOSEOUT.json` | research | 4255 | 72 | `18b0f9d9c531` | 1 |
| `services/runtime/research/foundations/RF16-CONTINUATION.md` | research | 2550 | 84 | `a78b9b98c029` | 1 |
| `services/runtime/research/foundations/RF16-CROSS-DOMAIN-FALSIFICATION-RUNTIME-FOUNDATIONS-V1.md` | research | 39353 | 1596 | `f0513d57ffb2` | 1 |
| `services/runtime/research/foundations/RF16-SOURCES.md` | research | 2760 | 71 | `ad7da2e3df42` | 1 |
| `services/runtime/research/foundations/RF2-ACTION-INTENT-PROPOSAL-COMMAND-OPERATION.md` | research | 43893 | 1765 | `75c40dcacc19` | 1 |
| `services/runtime/research/foundations/RF2-CLOSEOUT.json` | research | 3195 | 58 | `64f1a59e0eaa` | 1 |
| `services/runtime/research/foundations/RF2-CONTINUATION.md` | research | 5738 | 150 | `2f81d44b067f` | 1 |
| `services/runtime/research/foundations/RF2-SOURCES.md` | research | 6902 | 186 | `6698b36700d4` | 1 |
| `services/runtime/research/foundations/RF3-CLOSEOUT.json` | research | 4220 | 65 | `c7bc154ff8f9` | 1 |
| `services/runtime/research/foundations/RF3-CONTINUATION.md` | research | 7837 | 172 | `c7b51a0f991c` | 1 |
| `services/runtime/research/foundations/RF3-EXECUTION-REALIZATION-EFFECT-CONSEQUENCE.md` | research | 50226 | 1918 | `5e3171c39f8f` | 1 |
| `services/runtime/research/foundations/RF3-SOURCES.md` | research | 8429 | 234 | `25d72565ae86` | 1 |
| `services/runtime/research/foundations/RF4-CLOSEOUT.json` | research | 3933 | 66 | `6b7246dceb4d` | 1 |
| `services/runtime/research/foundations/RF4-CONTINUATION.md` | research | 6605 | 158 | `90455e300a2b` | 1 |
| `services/runtime/research/foundations/RF4-IDENTITY-SAMENESS-REPLAY-HISTORY.md` | research | 42537 | 1764 | `35403c72a227` | 1 |
| `services/runtime/research/foundations/RF4-SOURCES.md` | research | 5592 | 180 | `4fbe15a9a01c` | 1 |
| `services/runtime/research/foundations/RF5-CLOSEOUT.json` | research | 3936 | 65 | `d9134c76758a` | 1 |
| `services/runtime/research/foundations/RF5-CONTINUATION.md` | research | 6567 | 151 | `093f44ca621f` | 1 |
| `services/runtime/research/foundations/RF5-SOURCES.md` | research | 6118 | 173 | `50525fb90477` | 1 |
| `services/runtime/research/foundations/RF5-TIME-ORDERING-CONCURRENCY-CAUSALITY.md` | research | 38738 | 1507 | `67a2493740df` | 1 |
| `services/runtime/research/foundations/RF6-AUTHORITY-CAPABILITY-PERMISSION-CONTROL.md` | research | 48716 | 1903 | `55f5717943a7` | 1 |
| `services/runtime/research/foundations/RF6-CLOSEOUT.json` | research | 4536 | 71 | `91883b31eb08` | 1 |
| `services/runtime/research/foundations/RF6-CONTINUATION.md` | research | 7624 | 160 | `89ef075879e1` | 1 |
| `services/runtime/research/foundations/RF6-SOURCES.md` | research | 6632 | 183 | `12bbdff6117e` | 1 |
| `services/runtime/research/foundations/RF7-BOUNDARY-ENVIRONMENT-CONTEXT-DEPENDENCY.md` | research | 50889 | 2252 | `59d88095b996` | 1 |
| `services/runtime/research/foundations/RF7-CLOSEOUT.json` | research | 4766 | 73 | `1b049a3f3794` | 1 |
| `services/runtime/research/foundations/RF7-CONTINUATION.md` | research | 7521 | 162 | `18d003739308` | 1 |
| `services/runtime/research/foundations/RF7-SOURCES.md` | research | 7064 | 187 | `976cb13e9a07` | 1 |
| `services/runtime/research/foundations/RF8-CLOSEOUT.json` | research | 4560 | 72 | `ae48b0b2ecc1` | 1 |
| `services/runtime/research/foundations/RF8-CONTINUATION.md` | research | 7486 | 165 | `968e95b243e2` | 1 |
| `services/runtime/research/foundations/RF8-RESOURCE-CAPACITY-CONSTRAINT-SCARCITY.md` | research | 47509 | 2014 | `53377963a5de` | 1 |
| `services/runtime/research/foundations/RF8-SOURCES.md` | research | 5540 | 162 | `212fc2cf2e60` | 1 |
| `services/runtime/research/foundations/RF9-CLOSEOUT.json` | research | 5011 | 75 | `cc00d0aa9cd1` | 1 |
| `services/runtime/research/foundations/RF9-CONTINUATION.md` | research | 7571 | 159 | `f07f73ceaa6e` | 1 |
| `services/runtime/research/foundations/RF9-SCHEDULING-COORDINATION-ADMISSION-BACKPRESSURE.md` | research | 51546 | 2129 | `b1247e6e087d` | 1 |
| `services/runtime/research/foundations/RF9-SOURCES.md` | research | 6152 | 160 | `007129d0ae1d` | 1 |
| `services/runtime/research/foundations/RUNTIME-FOUNDATIONS-RF0-RF16-CLOSEOUT.md` | research | 17522 | 596 | `c5f6e7cb958f` | 1 |
| `services/runtime/research/foundations/RUNTIME-FOUNDATIONS-V1.md` | research | 5515 | 204 | `a859d601dbc0` | 1 |
| `services/runtime/research/programme/CONSTITUTION.md` | research | 3357 | 91 | `dd9048ee467c` |  |
| `services/runtime/research/programme/DOGFOOD-AND-CASE-STUDIES.md` | research | 1308 | 29 | `bd40bca49ad1` |  |
| `services/runtime/research/programme/EMERGING-RESEARCH.md` | research | 2882 | 53 | `b3cafd56352e` |  |
| `services/runtime/research/programme/ENGINEERING-CONSUMPTION.md` | research | 1331 | 30 | `3f6b9cb3ace1` |  |
| `services/runtime/research/programme/FALSIFIER-LIBRARY.md` | research | 2492 | 54 | `46fb30a6ebc8` |  |
| `services/runtime/research/programme/PROGRAMME-SATURATION-CLOSEOUT.md` | research | 3255 | 98 | `22b9cdaf56f9` |  |
| `services/runtime/research/programme/README.md` | research | 4940 | 50 | `ab7f4d41438a` |  |
| `services/runtime/research/programme/REOPEN-CONDITIONS.md` | research | 2316 | 61 | `9cc7312d7374` |  |
| `services/runtime/research/programme/THEORY-CORE.md` | research | 1237 | 35 | `a3d86ec0c991` |  |
| `services/runtime/research/programme/consumption/C1-STANDING-CURRENTNESS-RECOVERY.md` | research | 9491 | 260 | `f7d10864a34b` |  |
| `services/runtime/research/programme/consumption/C10-CROSS-FAMILY-SATURATION-AUDIT.md` | research | 16868 | 536 | `2c7b16994b7c` |  |
| `services/runtime/research/programme/consumption/C2-CONSEQUENTIAL-RETRY-REGROUNDING.md` | research | 5947 | 213 | `99ef9e5c5d4a` |  |
| `services/runtime/research/programme/consumption/C3-FRESH-EXECUTION-SUPPORT-REUSE.md` | research | 7932 | 231 | `9bd68429af4c` |  |
| `services/runtime/research/programme/consumption/C4-CROSS-OWNER-STANDING-CURRENTNESS.md` | research | 9203 | 254 | `2299548efb00` |  |
| `services/runtime/research/programme/consumption/C5-EVIDENCE-CLAIM-SCOPE.md` | research | 8137 | 267 | `c0dd1fda2cc7` |  |
| `services/runtime/research/programme/consumption/C6-LOCAL-GLOBAL-PUBLICATION-COMPOSITION.md` | research | 8188 | 302 | `4ca22f12d8db` |  |
| `services/runtime/research/programme/consumption/C7-IDENTITY-LINEAGE-CAUSAL-ATTRIBUTION.md` | research | 9559 | 291 | `80044f95f479` |  |
| `services/runtime/research/programme/consumption/C8-BINDING-AUTHORITY-REALIZATION-ORTHOGONALITY.md` | research | 8582 | 279 | `0bd66d2ebc85` |  |
| `services/runtime/research/programme/consumption/C9-LIFECYCLE-RETENTION-RECLAIMABILITY.md` | research | 9664 | 318 | `80b0771f59ca` |  |
| `services/runtime/research/programme/evidence/C1-STANDING-CURRENTNESS-RECOVERY.json` | evidence | 3964 | 89 | `f480f94c4ac6` | 1 |
| `services/runtime/research/programme/evidence/C10-CROSS-FAMILY-SATURATION-AUDIT.json` | evidence | 3756 | 79 | `5ba8486533a9` | 1 |
| `services/runtime/research/programme/evidence/C2-CONSEQUENTIAL-RETRY-REGROUNDING.json` | evidence | 2025 | 52 | `420d3f7b82ba` | 1 |
| `services/runtime/research/programme/evidence/C3-FRESH-EXECUTION-SUPPORT-REUSE.json` | evidence | 3187 | 62 | `eea0b89b2919` | 1 |
| `services/runtime/research/programme/evidence/C4-CROSS-OWNER-STANDING-CURRENTNESS.json` | evidence | 3372 | 72 | `fcd90d1421be` | 1 |
| `services/runtime/research/programme/evidence/C5-EVIDENCE-CLAIM-SCOPE.json` | evidence | 2881 | 60 | `173760d62e62` | 1 |
| `services/runtime/research/programme/evidence/C6-LOCAL-GLOBAL-PUBLICATION-COMPOSITION.json` | evidence | 2715 | 61 | `b9da895e0947` | 1 |
| `services/runtime/research/programme/evidence/C7-IDENTITY-LINEAGE-CAUSAL-ATTRIBUTION.json` | evidence | 3853 | 90 | `e124235867f8` | 1 |
| `services/runtime/research/programme/evidence/C8-BINDING-AUTHORITY-REALIZATION-ORTHOGONALITY.json` | evidence | 3279 | 74 | `f2b82943690f` | 1 |
| `services/runtime/research/programme/evidence/C9-LIFECYCLE-RETENTION-RECLAIMABILITY.json` | evidence | 2534 | 63 | `bbdb78d6e6bd` | 1 |
| `services/runtime/research/programme/tools/claim_scope_probe.py` | research | 2096 | 76 | `fa15be3fb9a8` |  |
| `services/runtime/research/programme/tools/composite_saturation_probe.py` | research | 4051 | 122 | `09d08cc0a24b` |  |
| `services/runtime/research/programme/tools/currentness_probe.py` | research | 3532 | 98 | `85fd2b8cc802` |  |
| `services/runtime/research/programme/tools/lifecycle_retention_probe.py` | research | 2156 | 58 | `43c53e09f60a` |  |
| `services/runtime/research/programme/tools/lineage_causation_probe.py` | research | 2388 | 64 | `91db9e9aeb87` |  |
| `services/runtime/research/programme/tools/orthogonality_probe.py` | research | 1820 | 50 | `ea9d049c5989` |  |
| `services/runtime/research/programme/tools/publication_pipeline_probe.py` | research | 2097 | 67 | `9c7ad1a57193` |  |
| `services/runtime/research/programme/tools/retry_admissibility_probe.py` | research | 2051 | 69 | `1773a54923a8` |  |
| `services/runtime/research/programme/tools/support_reuse_probe.py` | research | 1832 | 51 | `cce01ac5ce85` |  |
| `services/runtime/research/programme/tools/typed_currentness_probe.py` | research | 2964 | 83 | `2f335d340740` |  |
| `services/runtime/rust-toolchain.toml` | config | 86 | 4 | `c979a7d4d66b` |  |
| `services/runtime/scripts/agent_ux_report.py` | core | 8355 | 232 | `0cb53ea53f3d` |  |
| `services/runtime/scripts/backup.py` | core | 5429 | 139 | `ed6f14b77389` |  |
| `services/runtime/scripts/check_docs.py` | core | 12835 | 327 | `b5fbc28398ab` |  |
| `services/runtime/scripts/check_host_h2_r2_receipt.py` | core | 7420 | 167 | `9fa5f4905f23` |  |
| `services/runtime/scripts/check_runtime_standard_native_r3.py` | core | 6751 | 91 | `fc5356866cce` |  |
| `services/runtime/scripts/demo_runtime_flow.py` | core | 22817 | 563 | `26d99bc75237` |  |
| `services/runtime/scripts/local-acceptance` | other | 3388 | — | `24999663291c` |  |
| `services/runtime/scripts/mcp_e2e.py` | core | 101534 | 2376 | `8aa92f809830` |  |
| `services/runtime/scripts/mcp_probe.py` | core | 18856 | 435 | `e42b14e8b552` |  |
| `services/runtime/scripts/ordivon-runtime-archive` | other | 7338 | — | `f02e277eb6d5` |  |
| `services/runtime/scripts/ordivon-runtime-cache` | other | 36517 | — | `16a3af87ec9b` |  |
| `services/runtime/scripts/ordivon-runtime-capacity-acceptance` | other | 13738 | — | `bd7b3b70b8b3` |  |
| `services/runtime/scripts/ordivon-runtime-deploy` | other | 97534 | — | `137ed52a0ce5` |  |
| `services/runtime/scripts/ordivon-runtime-lifecycle` | other | 109887 | — | `3211605d1178` |  |
| `services/runtime/scripts/ordivon-runtime-pg-operator` | other | 201 | — | `92c205dc3494` |  |
| `services/runtime/scripts/ordivon-runtime-pg-reclaim` | other | 10885 | — | `09ee7234cc16` |  |
| `services/runtime/scripts/ordivon-runtime-pressure-control` | other | 21423 | — | `e4fdcd3ef78f` |  |
| `services/runtime/scripts/ordivon-runtime-reclaim` | other | 47050 | — | `8fc657494fa5` |  |
| `services/runtime/scripts/ordivon-runtime-status` | other | 67874 | — | `8b7e1acd32f4` |  |
| `services/runtime/scripts/ordivon_runtime_pg_operator.py` | core | 36853 | 782 | `b1c8e72ee0ac` |  |
| `services/runtime/scripts/owner-environment` | other | 8808 | — | `f71986e288a5` |  |
| `services/runtime/scripts/pg_disposable_physical.py` | core | 6363 | 169 | `d61699f6ef83` |  |
| `services/runtime/scripts/pg_retention_census.py` | core | 5845 | 140 | `6a988f6c8ee1` |  |
| `services/runtime/scripts/postgres_registry_currentness.py` | core | 6599 | 160 | `d0fcf97bcc76` |  |
| `services/runtime/scripts/postgres_registry_stage.py` | core | 14192 | 304 | `6394b8fa9ab2` |  |
| `services/runtime/scripts/resource_workload_profile.py` | core | 9197 | 222 | `2e1192d1c79d` |  |
| `services/runtime/scripts/restore.py` | core | 7404 | 169 | `78a624b0c9ab` |  |
| `services/runtime/scripts/snapshot_fds.py` | core | 1434 | 35 | `0f811cc6bc34` |  |
| `services/runtime/scripts/tests/pg_recovery_pitr_probe.py` | tests | 22017 | 481 | `615e0a04a7c5` |  |
| `services/runtime/scripts/tests/test_agent_ux_report.py` | tests | 6954 | 166 | `9ada4672f9dc` |  |
| `services/runtime/scripts/tests/test_archive.py` | tests | 13279 | 311 | `fcc7ab095931` |  |
| `services/runtime/scripts/tests/test_cache.py` | tests | 48574 | 1088 | `1594bf9fc785` |  |
| `services/runtime/scripts/tests/test_cache_root_singlepass.py` | tests | 4255 | 95 | `36df2734f570` |  |
| `services/runtime/scripts/tests/test_cache_singlewalk_consumer.py` | tests | 2062 | 45 | `6f168d52aa27` |  |
| `services/runtime/scripts/tests/test_cache_vanishing_entry.py` | tests | 2919 | 82 | `821719734a22` |  |
| `services/runtime/scripts/tests/test_capacity_acceptance.py` | tests | 5133 | 125 | `fd0a6ee39686` |  |
| `services/runtime/scripts/tests/test_demo_runtime_flow.py` | tests | 2849 | 72 | `85fc6bd25d95` |  |
| `services/runtime/scripts/tests/test_deploy_reclaim.py` | tests | 226416 | 5155 | `7928264a6300` |  |
| `services/runtime/scripts/tests/test_dirty_checkpoint.py` | tests | 14519 | 308 | `25acd651b274` |  |
| `services/runtime/scripts/tests/test_focused_verification_contract.py` | tests | 3155 | 74 | `b071182c7113` |  |
| `services/runtime/scripts/tests/test_formal_trace.py` | tests | 66763 | 1300 | `6af06206650e` |  |
| `services/runtime/scripts/tests/test_host_h2_r2_receipt.py` | tests | 2614 | 58 | `780c0f38fef1` |  |
| `services/runtime/scripts/tests/test_lifecycle.py` | tests | 116678 | 2677 | `623d97231d85` |  |
| `services/runtime/scripts/tests/test_mcp_e2e.py` | tests | 6111 | 151 | `0c4574858363` |  |
| `services/runtime/scripts/tests/test_mcp_e2e_reconciliation.py` | tests | 4938 | 124 | `36d6c3d8f3bc` |  |
| `services/runtime/scripts/tests/test_mcp_probe.py` | tests | 21794 | 539 | `5e1532305fbf` |  |
| `services/runtime/scripts/tests/test_operational_scripts.py` | tests | 27535 | 595 | `09318bcdbee2` |  |
| `services/runtime/scripts/tests/test_owner_python_pin.py` | tests | 4408 | 110 | `3986e252cb7f` |  |
| `services/runtime/scripts/tests/test_pg_consumer_source_bound_formal.py` | tests | 1305 | 27 | `30494a9e3187` |  |
| `services/runtime/scripts/tests/test_pg_disposable_physical.py` | tests | 3190 | 75 | `1c1d83d2afb3` |  |
| `services/runtime/scripts/tests/test_pg_operator_release.py` | tests | 27921 | 576 | `bc543143530c` |  |
| `services/runtime/scripts/tests/test_pg_physical_verification_contract.py` | tests | 4554 | 97 | `d05944181ed0` |  |
| `services/runtime/scripts/tests/test_pg_retention_census.py` | tests | 5402 | 112 | `e743d51f50fe` |  |
| `services/runtime/scripts/tests/test_pg_workspace_reclaim.py` | tests | 2022 | 50 | `dce47c907497` |  |
| `services/runtime/scripts/tests/test_postgres_registry_currentness.py` | tests | 5234 | 141 | `42e0e62fe90c` |  |
| `services/runtime/scripts/tests/test_postgres_registry_stage.py` | tests | 5995 | 131 | `9c19806f9636` |  |
| `services/runtime/scripts/tests/test_pressure_control.py` | tests | 13018 | 264 | `92fdedc7ad90` |  |
| `services/runtime/scripts/tests/test_reference_model_shards.py` | tests | 2162 | 50 | `197c6a05fc0d` |  |
| `services/runtime/scripts/tests/test_release_receipt_semantics_r1.py` | tests | 7694 | 179 | `ae2e8e4424ea` |  |
| `services/runtime/scripts/tests/test_resource_workload_profile.py` | tests | 6334 | 138 | `a854e260adc3` |  |
| `services/runtime/scripts/tests/test_status.py` | tests | 49729 | 1097 | `cb944283877f` |  |
| `services/runtime/scripts/tests/test_tla_formal_external_jar.py` | tests | 12140 | 279 | `1d86424b9e38` |  |
| `services/runtime/scripts/tla-formal` | other | 45712 | — | `f66a08b7d968` |  |
| `services/runtime/scripts/verify_formal_trace.py` | core | 55420 | 1266 | `aaca2a34ae86` |  |
| `services/runtime/scripts/verify_reference_model_shards.py` | core | 6240 | 164 | `3148a41201f8` |  |
| `services/runtime/scripts/windows-job-launcher-acceptance.py` | core | 30358 | 653 | `076b20641803` |  |
| `services/runtime/scripts/windows-native-runtime-r6c-acceptance.ps1` | core | 30179 | 764 | `678ced8abc62` |  |
| `services/runtime/sql/pg_resource_scheduler_v1.sql` | schemas | 767 | 11 | `030ff583b9f1` |  |
| `services/runtime/standards/runtime_standard_native_r3.sdoc` | other | 6060 | — | `00766a070883` |  |
| `services/runtime/standards/runtime_standard_native_r3.toml` | config | 3011 | 66 | `03e1dc7d2d59` |  |
| `services/runtime/standards/runtime_standard_native_r3_report.json` | config | 3940 | 144 | `f29f840cfc00` | 1 |
| `services/runtime/tests/test_systemd_liveness_contract.py` | tests | 483 | 13 | `e4c326eac671` |  |
| `services/runtime/tests/test_windows_launcher_effective_cwd_identity_contract.py` | tests | 1666 | 42 | `5dbd4642ad7c` |  |
| `services/runtime/tests/test_windows_launcher_error_evidence.py` | tests | 2001 | 36 | `f7649626db1d` |  |
| `services/runtime/tests/test_windows_launcher_verbatim_path_bridge.py` | tests | 681 | 14 | `38bc52f49d04` |  |
| `services/runtime/tests/test_windows_native_runtime_r6c_acceptance.py` | tests | 7001 | 142 | `60d6af76acda` |  |
| `services/runtime/tests/test_windows_privileged_broker_contract.py` | tests | 9870 | 191 | `89b782923439` |  |
| `services/runtime/tests/test_windows_runtime_service_materializer.py` | tests | 6728 | 143 | `f5b5299f8269` |  |

### host — services/host/（117 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `services/host/.gitignore` | other | 90 | — | `7b6c07bf544e` |  |
| `services/host/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `services/host/AGENTS.md` | docs | 3465 | 26 | `b5f987fe7c66` |  |
| `services/host/README.md` | docs | 12517 | 177 | `4b8a0c1b03cf` |  |
| `services/host/alembic.ini` | config | 551 | 31 | `ff9788508ddc` |  |
| `services/host/docs/HOST_OWNER_GUIDE.md` | docs | 22890 | 254 | `6f1fbfdacf09` |  |
| `services/host/docs/HOST_R21_AGENT_EXECUTION_PLAN.md` | docs | 16595 | 162 | `21c4c40b9a26` |  |
| `services/host/docs/HOST_R21_AGENT_EXECUTION_SPEC.md` | docs | 24699 | 251 | `e6c818b3c6d0` |  |
| `services/host/docs/SOCIAL_WORK_FABRIC_R1.md` | docs | 11487 | 103 | `cfcbaed59d9b` |  |
| `services/host/docs/SOCIAL_WORK_FABRIC_R2_IMPLEMENTATION.md` | docs | 5845 | 105 | `d3d60a42c2ec` |  |
| `services/host/docs/SOCIAL_WORK_FABRIC_R2_SPEC.md` | docs | 8156 | 134 | `65974154f3f0` |  |
| `services/host/formal/HostUnicodeGram.lean` | core | 3663 | 86 | `d9e70860cc9d` |  |
| `services/host/formal/HostWorkDAG.lean` | core | 3633 | 89 | `29da097334a8` |  |
| `services/host/formal/work_graph_dag.py` | core | 3686 | 95 | `8b5110de3149` |  |
| `services/host/mcp-surface.json` | config | 867 | 40 | `0f37fa67e395` | 1 |
| `services/host/migrations/env.py` | core | 1247 | 44 | `67f154017183` |  |
| `services/host/migrations/script.py.mako` | other | 604 | — | `0448c9b9366f` |  |
| `services/host/migrations/versions/0001_host_v2_core.py` | core | 2244 | 65 | `d3965dd44b74` |  |
| `services/host/migrations/versions/0002_concurrent_idempotency_claim.py` | core | 482 | 21 | `a1fc83ce0faf` |  |
| `services/host/migrations/versions/0003_product_surfaces.py` | core | 3738 | 71 | `de36c44d7192` |  |
| `services/host/migrations/versions/0004_r6_cleanup.py` | core | 2332 | 54 | `63cd99526d30` |  |
| `services/host/migrations/versions/0005_explicit_board_task_route.py` | core | 3831 | 106 | `11d87f4ae05c` |  |
| `services/host/migrations/versions/0006_social_work_fabric_work_graph.py` | core | 3065 | 78 | `d053da75605b` |  |
| `services/host/migrations/versions/0007_social_work_fabric_social_graph.py` | core | 5310 | 120 | `06609c02e136` |  |
| `services/host/migrations/versions/0008_social_work_fabric_attention.py` | core | 4618 | 111 | `2004a92dd01e` |  |
| `services/host/migrations/versions/0009_retire_legacy_task_board.py` | core | 1201 | 38 | `f9fc63160463` |  |
| `services/host/migrations/versions/0010_social_work_fabric_r2.py` | core | 2768 | 61 | `52f1abdd2e3e` |  |
| `services/host/migrations/versions/0011_retire_external_news.py` | core | 1138 | 38 | `2123bc3b674b` |  |
| `services/host/migrations/versions/0012_message_literal_trigram.py` | core | 1975 | 61 | `73e6bc666b1a` |  |
| `services/host/migrations/versions/0013_unicode_substring_gin.py` | core | 3065 | 81 | `bf2b189df97a` |  |
| `services/host/mise.toml` | config | 2735 | 84 | `28b6ff4b885a` |  |
| `services/host/packaging/install_release.sh` | core | 5658 | 155 | `4f0cf89db33a` |  |
| `services/host/packaging/systemd/host-v2.env.example` | other | 324 | — | `f72abfe70c11` |  |
| `services/host/packaging/systemd/ordivon-host-v2.service` | config | 1050 | 38 | `b56a0ad90c1d` |  |
| `services/host/packaging/verify_tool_surface.py` | core | 3134 | 76 | `e7e7b013ee96` |  |
| `services/host/planning/host-friction-observatory-r1.json` | config | 4948 | 192 | `db9e0e76d50c` | 1 |
| `services/host/planning/lego-plan-r1.json` | config | 29265 | 688 | `14dce9180c52` | 1 |
| `services/host/planning/lego-plan-r3.json` | config | 5947 | 209 | `d8e510fe01e3` | 3 |
| `services/host/planning/social-work-fabric-r1.json` | config | 13179 | 444 | `cc123c93e176` | 1 |
| `services/host/pyproject.toml` | config | 829 | 43 | `5ce8466512e6` |  |
| `services/host/src/ordivon_host_v2/__init__.py` | core | 129 | 4 | `4eeedb16c163` |  |
| `services/host/src/ordivon_host_v2/attention_projections.py` | core | 14298 | 324 | `69406a35bca8` |  |
| `services/host/src/ordivon_host_v2/attention_sql.py` | core | 9764 | 161 | `3979281b1be9` |  |
| `services/host/src/ordivon_host_v2/attention_store.py` | core | 7035 | 157 | `9aad74bffafc` |  |
| `services/host/src/ordivon_host_v2/canonical_json.py` | core | 283 | 14 | `260e1634b3a1` |  |
| `services/host/src/ordivon_host_v2/collaboration_inputs.py` | core | 3131 | 96 | `d4b51192ba9a` |  |
| `services/host/src/ordivon_host_v2/collection_pagination.py` | core | 1343 | 38 | `9c9e33594658` |  |
| `services/host/src/ordivon_host_v2/command_receipts.py` | core | 2104 | 58 | `349fe0c12f84` |  |
| `services/host/src/ordivon_host_v2/contracts.py` | core | 1546 | 66 | `82bb127cec45` |  |
| `services/host/src/ordivon_host_v2/coordination_inputs.py` | core | 1450 | 38 | `d6326de0c076` |  |
| `services/host/src/ordivon_host_v2/coordination_intent_commands.py` | core | 5564 | 123 | `162e8e2fddad` |  |
| `services/host/src/ordivon_host_v2/errors.py` | core | 181 | 14 | `ab335ccf7526` |  |
| `services/host/src/ordivon_host_v2/mcp_attention_tools.py` | core | 3694 | 111 | `efbb916ed92e` |  |
| `services/host/src/ordivon_host_v2/mcp_domain_errors.py` | core | 3820 | 116 | `8228473aaf6e` |  |
| `services/host/src/ordivon_host_v2/mcp_server.py` | core | 4131 | 104 | `c6684b572aa7` |  |
| `services/host/src/ordivon_host_v2/mcp_social_tools.py` | core | 10117 | 318 | `9155d2f22177` |  |
| `services/host/src/ordivon_host_v2/mcp_tool_registration.py` | core | 1176 | 32 | `b1304fe816ce` |  |
| `services/host/src/ordivon_host_v2/mcp_work_tools.py` | core | 3872 | 108 | `a0ef346a7869` |  |
| `services/host/src/ordivon_host_v2/native_pool_observability.py` | core | 2101 | 49 | `7edc7826893a` |  |
| `services/host/src/ordivon_host_v2/postgres_bounds.py` | core | 117 | 3 | `0bd76c0cc408` |  |
| `services/host/src/ordivon_host_v2/postgres_connections.py` | core | 834 | 24 | `4eff60e9b42a` |  |
| `services/host/src/ordivon_host_v2/py.typed` | other | 0 | — | `e3b0c44298fc` |  |
| `services/host/src/ordivon_host_v2/service.py` | core | 9336 | 211 | `463b93194b64` |  |
| `services/host/src/ordivon_host_v2/social_contracts.py` | core | 8249 | 327 | `e605e76128d0` |  |
| `services/host/src/ordivon_host_v2/social_errors.py` | core | 212 | 13 | `f34f48f0c986` |  |
| `services/host/src/ordivon_host_v2/social_message_commands.py` | core | 9468 | 197 | `1e38cf8e5067` |  |
| `services/host/src/ordivon_host_v2/social_message_queries.py` | core | 13531 | 305 | `357ae66a3d7a` |  |
| `services/host/src/ordivon_host_v2/social_read_queries.py` | core | 487 | 15 | `4c9f8b0a1b3b` |  |
| `services/host/src/ordivon_host_v2/social_space_commands.py` | core | 5342 | 111 | `bcce9ce4a56a` |  |
| `services/host/src/ordivon_host_v2/social_space_queries.py` | core | 14429 | 342 | `be75018a4321` |  |
| `services/host/src/ordivon_host_v2/social_store.py` | core | 2371 | 63 | `803c07650a65` |  |
| `services/host/src/ordivon_host_v2/social_topic_commands.py` | core | 9275 | 199 | `f6c47aa5fa2b` |  |
| `services/host/src/ordivon_host_v2/social_topic_queries.py` | core | 7787 | 181 | `b71483d171a2` |  |
| `services/host/src/ordivon_host_v2/work_inputs.py` | core | 4069 | 119 | `0abffb3fa862` |  |
| `services/host/src/ordivon_host_v2/work_queries.py` | core | 8052 | 178 | `7e0981d0e214` |  |
| `services/host/src/ordivon_host_v2/work_relation_commands.py` | core | 4717 | 96 | `4f50da907fb0` |  |
| `services/host/src/ordivon_host_v2/work_store.py` | core | 11315 | 239 | `e71cd3ea330a` |  |
| `services/host/tests/conftest.py` | tests | 692 | 21 | `58b4e2d8d4a2` |  |
| `services/host/tests/test_attention_query_boundary.py` | tests | 1272 | 30 | `cb4f0e6c4247` |  |
| `services/host/tests/test_attention_single_snapshot_postgres.py` | tests | 5448 | 138 | `b54297c67db2` |  |
| `services/host/tests/test_canonical_json_property.py` | tests | 931 | 25 | `1a354b1abbd8` |  |
| `services/host/tests/test_clean_room.py` | tests | 293 | 9 | `85820ebb5c72` |  |
| `services/host/tests/test_contract_policy.py` | tests | 11954 | 293 | `19ee14519065` |  |
| `services/host/tests/test_host_db_preflight_contract.py` | tests | 2189 | 69 | `57aa1e2946e6` |  |
| `services/host/tests/test_host_focused_default.py` | tests | 636 | 16 | `c800c541b71a` |  |
| `services/host/tests/test_host_history_doctor_postgres.py` | tests | 2959 | 78 | `6fdd0ec92b33` |  |
| `services/host/tests/test_host_queue_qualification.py` | tests | 3896 | 125 | `5e10333ee53f` |  |
| `services/host/tests/test_mcp_domain_errors.py` | tests | 10533 | 297 | `befcbfc44fa5` |  |
| `services/host/tests/test_mcp_native_pool_stats.py` | tests | 4311 | 109 | `11946e2d3420` |  |
| `services/host/tests/test_mcp_surface.py` | tests | 12119 | 300 | `94b82f3ad76c` |  |
| `services/host/tests/test_mcp_surface_identity.py` | tests | 2539 | 73 | `4493f3009d78` |  |
| `services/host/tests/test_message_get_contract.py` | tests | 2719 | 93 | `5e790046bf75` |  |
| `services/host/tests/test_native_pool_postgres.py` | tests | 8130 | 196 | `2f87298affc8` |  |
| `services/host/tests/test_release_packaging.py` | tests | 10113 | 245 | `6817c7a174a1` |  |
| `services/host/tests/test_schema_diagnostic.py` | tests | 381 | 10 | `c842802520fc` |  |
| `services/host/tests/test_social_creation_linearizability.py` | tests | 4171 | 121 | `759cb21c4c36` |  |
| `services/host/tests/test_social_message_digest_postgres.py` | tests | 6890 | 157 | `c8dc50a67845` |  |
| `services/host/tests/test_social_message_read_integrity.py` | tests | 1880 | 58 | `3505f0c2e043` |  |
| `services/host/tests/test_social_query_boundary.py` | tests | 2684 | 75 | `7bfcd65cd87a` |  |
| `services/host/tests/test_social_store_exact_integer_contract.py` | tests | 7151 | 178 | `c5d2c9a7671d` |  |
| `services/host/tests/test_social_timestamp_strict_bigint.py` | tests | 3065 | 87 | `e386097ac480` |  |
| `services/host/tests/test_social_work_fabric_architecture.py` | tests | 3917 | 95 | `f60efb4ebfff` |  |
| `services/host/tests/test_social_work_fabric_attention.py` | tests | 5689 | 136 | `88724f47dafc` |  |
| `services/host/tests/test_social_work_fabric_postgres.py` | tests | 53606 | 1452 | `943d51502950` |  |
| `services/host/tests/test_social_work_fabric_retirement.py` | tests | 2045 | 47 | `7fee3736e574` |  |
| `services/host/tests/test_social_work_fabric_social_graph.py` | tests | 3055 | 99 | `7b395d99479a` |  |
| `services/host/tests/test_social_work_fabric_social_store.py` | tests | 6930 | 171 | `1493bd0979fc` |  |
| `services/host/tests/test_social_work_fabric_society.py` | tests | 7004 | 185 | `5ec8d677bbaa` |  |
| `services/host/tests/test_social_work_fabric_work_graph.py` | tests | 8768 | 238 | `89ffa9aa39ee` |  |
| `services/host/tests/test_systemd_liveness_contract.py` | tests | 661 | 16 | `76d52110d137` |  |
| `services/host/tests/test_tool_surface_release_contract.py` | tests | 2834 | 84 | `77a9f4db5240` |  |
| `services/host/tests/test_topic_state_lifecycle_postgres.py` | tests | 6863 | 197 | `6689533282e6` |  |
| `services/host/tests/test_work_query_boundary.py` | tests | 2253 | 54 | `1910c64ff562` |  |
| `services/host/tests/test_work_relation_three_node_oracle.py` | tests | 5610 | 162 | `a5a97e7a0850` |  |
| `services/host/tests/test_work_snapshot_read_refinement.py` | tests | 3195 | 85 | `32bcf1b9e69c` |  |
| `services/host/tools/host_queue_verify.sh` | core | 2667 | 84 | `afdbc5a8f2d5` |  |
| `services/host/uv.lock` | config | 137088 | — | `4b3da3647e5e` |  |

### harness — services/harness/（731 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `services/harness/.github/ISSUE_TEMPLATE/bug_report.yml` | config | 1688 | 59 | `e054793a3c38` |  |
| `services/harness/.github/ISSUE_TEMPLATE/config.yml` | config | 222 | 5 | `d4ba6d6a86ef` |  |
| `services/harness/.github/ISSUE_TEMPLATE/feature_request.yml` | config | 1012 | 33 | `31a2ce1cb6fa` |  |
| `services/harness/.github/actionlint.yaml` | config | 76 | 5 | `6d062429a44d` |  |
| `services/harness/.github/pull_request_template.md` | docs | 1174 | 26 | `0c72f898bbbe` |  |
| `services/harness/.github/workflows/release-acceptance.yml` | config | 4002 | 96 | `3da4073f731e` |  |
| `services/harness/.gitignore` | other | 107 | — | `b6837200dc9c` |  |
| `services/harness/.ordivon/project.yaml` | config | 934 | 35 | `27dc84698e22` |  |
| `services/harness/.ordivon/publication.yaml` | config | 937 | 26 | `dae8b277d37b` |  |
| `services/harness/.ordivon/rights.yaml` | config | 610 | 16 | `99a29d728c2f` |  |
| `services/harness/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `services/harness/ARCHITECTURE.md` | docs | 51646 | 373 | `4fa657701e4e` | 1 |
| `services/harness/CHANGELOG.md` | docs | 54860 | 256 | `952355228c12` |  |
| `services/harness/CONTRIBUTING.md` | docs | 2187 | 55 | `2607e25503f9` |  |
| `services/harness/LICENSE` | other | 11357 | — | `c71d239df917` |  |
| `services/harness/README.md` | docs | 28009 | 440 | `15e48ae9b5a7` | 1 |
| `services/harness/SECURITY.md` | docs | 4350 | 54 | `b2f575a55557` |  |
| `services/harness/config/agent-automation-mcp-requirements.txt` | other | 532 | 29 | `fbd01d1c4388` |  |
| `services/harness/config/agent-automation-temporal-requirements.txt` | other | 74 | 5 | `5886a7b5e2ee` |  |
| `services/harness/config/agent-automation.toml` | config | 1514 | 33 | `fb1a32fd7ea5` |  |
| `services/harness/config/browser-benchmark-suite.json` | config | 1371 | 41 | `c4202180bb02` | 1 |
| `services/harness/config/browser-capability-routes.json` | config | 3529 | 136 | `901b3cbdf3cd` | 1 |
| `services/harness/config/browser-decision-corpus-r1.json` | config | 312752 | 9642 | `68d908cfa684` | 1 |
| `services/harness/config/browserless-playwright-requirements.txt` | other | 57 | 3 | `0fc7bf1a8bcd` |  |
| `services/harness/config/harness-otel-event-sink-requirements.txt` | other | 162 | 3 | `1c393be4c190` |  |
| `services/harness/config/mind2web-browser-decision-corpus-no-context-r1.json` | config | 326787 | 10331 | `47d529efa2b6` | 1 |
| `services/harness/config/mind2web-browser-decision-corpus-r1.json` | config | 451905 | 10330 | `dfdc567feea9` | 1 |
| `services/harness/config/system1-decision-corpus-r1.json` | config | 10089 | 331 | `31f14a9a4306` | 1 |
| `services/harness/containers/ordivon-browserless@.container` | other | 1194 | — | `afc2c42cd265` |  |
| `services/harness/docs/ADAPTIVE_EDIT_GATEWAY_R2.md` | docs | 15758 | 378 | `b27527e267a9` |  |
| `services/harness/docs/AM-DSH-EVOLUTION-CHALLENGER.md` | docs | 4705 | 60 | `cc55944cef7c` |  |
| `services/harness/docs/AM2-LOOP-BOUNDARY-FALSIFIERS.md` | docs | 6917 | 111 | `11a4a7b66128` |  |
| `services/harness/docs/AM5-GENERATED-MORPHOLOGY-CANDIDATE.md` | docs | 2783 | 66 | `fa749fa2ca2f` |  |
| `services/harness/docs/AM8-LIVE-MORPHING-GATE.md` | docs | 4285 | 67 | `4dac6911ac02` |  |
| `services/harness/docs/BROWSER-SECURITY-WITNESS-SOURCE-R1.md` | docs | 14154 | 243 | `927b44ef27ca` |  |
| `services/harness/docs/BROWSER_AX_GENERALIZATION_R1.md` | docs | 5320 | 139 | `2f40b3a1796c` |  |
| `services/harness/docs/BROWSER_BENCHMARK_CONTRACT_S2.md` | docs | 3483 | 98 | `4dde2979054c` |  |
| `services/harness/docs/BROWSER_BENCHMARK_PROSPECTIVE_S5.md` | docs | 3788 | 109 | `3aa390d3e8e9` |  |
| `services/harness/docs/BROWSER_BENCHMARK_RUNNER_S3.md` | docs | 4962 | 131 | `8899acf7dd05` |  |
| `services/harness/docs/BROWSER_BENCHMARK_RUNTIME_HANDOFF_S4.md` | docs | 5177 | 132 | `76c98ce432e1` |  |
| `services/harness/docs/BROWSER_CAPABILITY_ROUTER_R1.md` | docs | 5219 | 115 | `322a248d20f2` |  |
| `services/harness/docs/BROWSER_DECISION_ARCHITECTURE_R1.md` | docs | 12022 | 258 | `f3bbab03c80a` |  |
| `services/harness/docs/BROWSER_DECISION_PROVIDER_DUEL_R1.md` | docs | 4485 | 116 | `91d15575bf77` |  |
| `services/harness/docs/BROWSER_READINESS_OPS_R6.md` | docs | 5332 | 128 | `200c6c5f4377` |  |
| `services/harness/docs/CANONICAL_COMPATIBILITY.md` | docs | 1273 | 11 | `552355865458` |  |
| `services/harness/docs/COMPATIBILITY.md` | docs | 15780 | 102 | `107e0aca67da` | 1 |
| `services/harness/docs/DAP_PROVIDER_PORT_R8.md` | docs | 7073 | 231 | `0b843119b734` |  |
| `services/harness/docs/DATA_AND_PRIVACY.md` | docs | 17774 | 164 | `4db102750a07` | 1 |
| `services/harness/docs/DELIBERATION-BEFORE-TOOLS-H0.md` | docs | 10119 | 370 | `a4759be0be73` | 1 |
| `services/harness/docs/DELIBERATION-COMPOSITION-H1.md` | docs | 9600 | 334 | `6dfa6260db01` | 1 |
| `services/harness/docs/DELIBERATION-LIFECYCLE-H2.md` | docs | 12354 | 336 | `25ad1494216a` | 1 |
| `services/harness/docs/DOMAIN-TOOL-BRIDGE-P0.md` | docs | 3716 | 101 | `d55c0b52a224` | 1 |
| `services/harness/docs/EVIDENCE_CURRENTNESS.md` | docs | 2199 | 54 | `ba578edc7e9d` |  |
| `services/harness/docs/LAYA_ARCHITECTURE_DUEL_R1.md` | docs | 4001 | 101 | `61d4f2684c5b` |  |
| `services/harness/docs/LSP_PROVIDER_PORT_R7.md` | docs | 5531 | 148 | `3c4e9938fd95` |  |
| `services/harness/docs/LSP_WORKSPACE_EDIT_R7.md` | docs | 7491 | 206 | `6c0274c7d50f` |  |
| `services/harness/docs/OPERATIONS.md` | docs | 11407 | 215 | `6bc763b0b19e` | 1 |
| `services/harness/docs/ORDIVON_HARNESS_E1_E2_DESIGN.md` | docs | 25026 | 579 | `4b2d7092bb7d` |  |
| `services/harness/docs/ORDIVON_HARNESS_OH1_OH5_CLOSEOUT.md` | docs | 14525 | 267 | `19e0431ecd6f` |  |
| `services/harness/docs/P0-CAPABILITY-COMPOSITION-CLOSEOUT.md` | docs | 5670 | 75 | `92937d5faaad` |  |
| `services/harness/docs/P0-INDEPENDENT-PERSISTENCE.md` | docs | 19825 | 283 | `2d4c44c9a906` | 1 |
| `services/harness/docs/PROVIDER-BOUNDARY-DIAGNOSIS-R1.md` | docs | 2146 | 65 | `b2a4edd2461f` |  |
| `services/harness/docs/QUICKSTART.md` | docs | 20684 | 338 | `aa91766bacb2` | 1 |
| `services/harness/docs/RELEASES.md` | docs | 5598 | 99 | `fd7db7729c51` | 1 |
| `services/harness/docs/STATUS.md` | docs | 13237 | 136 | `f76b5a9c0ad9` | 1 |
| `services/harness/docs/SYSTEM1_DECISION_BENCHMARK_R1.md` | docs | 2018 | 54 | `d45b0cdaa72d` |  |
| `services/harness/docs/VERIFICATION.md` | docs | 11019 | 151 | `39bc4c2e0674` | 1 |
| `services/harness/docs/authority.md` | docs | 5780 | 83 | `db47a2d5e69f` | 1 |
| `services/harness/docs/harness-boundary-h5-decision.md` | docs | 12083 | 284 | `b9cda760c18a` |  |
| `services/harness/docs/ordivon-harness-v0.md` | docs | 20391 | 379 | `11bd060732cf` |  |
| `services/harness/docs/superpowers/plans/2026-09-19-durable-human-handoff-standards-replacement.md` | docs | 1916 | 37 | `a46844a2b23b` |  |
| `services/harness/evals/capability_environment_owner_dogfood.py` | core | 6907 | 189 | `a1ab6bae3477` |  |
| `services/harness/evals/fixtures/capability-environment-owner-dogfood-20260827.json` | config | 11437 | 314 | `90d49504c029` | 1 |
| `services/harness/evals/fresh_agent_ab/CLOSEOUT-v1-v2.md` | docs | 6131 | 95 | `13fff1d4ccf0` |  |
| `services/harness/evals/fresh_agent_ab/POSTHOC-AUDIT-v1.md` | docs | 4581 | 64 | `25bc47190caf` |  |
| `services/harness/evals/fresh_agent_ab/PREREGISTRATION-v1.md` | docs | 4259 | 70 | `0e234b264b0d` |  |
| `services/harness/evals/fresh_agent_ab/PREREGISTRATION-v2-currentness.md` | docs | 5216 | 86 | `c1affecfb637` |  |
| `services/harness/evals/fresh_agent_ab/audit-v2-currentness.json` | config | 2287 | 83 | `b17b40af3447` | 1 |
| `services/harness/evals/fresh_agent_ab/corpus-v1.json` | config | 375565 | 11355 | `e0f9399e1c5c` | 1 |
| `services/harness/evals/fresh_agent_ab/corpus-v2-currentness.json` | config | 337296 | 11379 | `6c0d95872fe5` | 1 |
| `services/harness/evals/fresh_agent_ab/corrected-metrics-v1.json` | config | 2282 | 68 | `54683b9d856c` | 1 |
| `services/harness/evals/fresh_agent_ab/result-v1.json` | config | 54621 | 1629 | `5acffe6e1192` | 1 |
| `services/harness/evals/fresh_agent_ab/result-v2-currentness.json` | config | 54728 | 1613 | `eeadbc748c4d` | 1 |
| `services/harness/evals/fresh_agent_ab/run_live_v1.py` | core | 15964 | 349 | `c150c752aace` |  |
| `services/harness/evals/fresh_agent_ab/run_live_v2_currentness.py` | core | 19229 | 472 | `de8cb6f40aea` |  |
| `services/harness/evals/fresh_agent_ab/summary-v1.json` | config | 1458 | 53 | `35b7cd76bc83` |  |
| `services/harness/evals/fresh_agent_ab/summary-v2-currentness.json` | config | 2127 | 69 | `2ac76154b383` |  |
| `services/harness/evals/harness-document-retirement-004/README.md` | docs | 1169 | 22 | `41599143f26f` |  |
| `services/harness/evals/harness-document-retirement-004/fixture/README.md` | docs | 239 | 5 | `939db7d7b936` |  |
| `services/harness/evals/harness-document-retirement-004/fixture/docs/MIGRATION-R1.md` | docs | 114 | 2 | `4a3308bb6b48` |  |
| `services/harness/evals/harness-document-retirement-004/fixture/docs/OLD-PHASE.md` | docs | 97 | 2 | `2b3b46ad1512` |  |
| `services/harness/evals/harness-document-retirement-004/fixture/docs/OPERATOR.md` | docs | 110 | 2 | `b216b72a7d9e` |  |
| `services/harness/evals/harness-document-retirement-004/fixture/evidence/consumed-fixture.json` | evidence | 85 | 1 | `03c82169ff4a` |  |
| `services/harness/evals/harness-document-retirement-004/task.json` | config | 2270 | 63 | `8cad70e5438e` | 1 |
| `services/harness/evals/harness-document-retirement-004/verifier.py` | core | 2346 | 69 | `14385eec26a5` |  |
| `services/harness/evals/harness-edit-addressing-002/README.md` | docs | 897 | 22 | `8edf960b18d5` |  |
| `services/harness/evals/harness-edit-addressing-002/evidence/r2-task-qa.json` | evidence | 1059 | 35 | `91e2da45bf96` | 1 |
| `services/harness/evals/harness-edit-addressing-002/known-invalid/both-enabled.py` | core | 91 | 6 | `4ff9a9197b55` |  |
| `services/harness/evals/harness-edit-addressing-002/oracle/feature_flags.py` | core | 92 | 6 | `970943c12c5f` |  |
| `services/harness/evals/harness-edit-addressing-002/qa.py` | core | 7504 | 204 | `f04106aa5519` |  |
| `services/harness/evals/harness-edit-addressing-002/task.json` | config | 2240 | 63 | `254c5209069f` | 1 |
| `services/harness/evals/harness-edit-addressing-002/verifier/test_outcome.py` | tests | 889 | 26 | `231bb0106851` |  |
| `services/harness/evals/harness-edit-multiregion-003/README.md` | docs | 647 | 14 | `5ad5c49fbdbc` |  |
| `services/harness/evals/harness-edit-multiregion-003/evidence/r2-task-qa.json` | evidence | 1164 | 43 | `e638193b1065` | 1 |
| `services/harness/evals/harness-edit-multiregion-003/known-invalid/collateral.py` | core | 119 | 9 | `411b4f11e7d8` |  |
| `services/harness/evals/harness-edit-multiregion-003/known-invalid/retry-only.py` | core | 119 | 9 | `1f6879257718` |  |
| `services/harness/evals/harness-edit-multiregion-003/known-invalid/timeout-only.py` | core | 119 | 9 | `5e348af16901` |  |
| `services/harness/evals/harness-edit-multiregion-003/oracle/pipeline.py` | core | 119 | 9 | `710135975936` |  |
| `services/harness/evals/harness-edit-multiregion-003/qa.py` | core | 7723 | 206 | `c7fc2622138c` |  |
| `services/harness/evals/harness-edit-multiregion-003/task.json` | config | 2269 | 63 | `03c7ac9b497e` | 1 |
| `services/harness/evals/harness-edit-multiregion-003/verifier/test_outcome.py` | tests | 909 | 25 | `cac878856bae` |  |
| `services/harness/evals/harness-repository-repair-001/README.md` | docs | 2068 | 55 | `2bbe2b4e3b5c` |  |
| `services/harness/evals/harness-repository-repair-001/evidence/r2-task-qa.json` | evidence | 1408 | 44 | `a15ebb27b492` | 1 |
| `services/harness/evals/harness-repository-repair-001/known-invalid/floor-only.py` | core | 651 | 15 | `aaa27b5d2183` |  |
| `services/harness/evals/harness-repository-repair-001/known-invalid/visible-suite-overfit.py` | core | 965 | 28 | `2b7a2b1da6f1` |  |
| `services/harness/evals/harness-repository-repair-001/oracle/allocation.py` | core | 1024 | 25 | `9d0689dcd19c` |  |
| `services/harness/evals/harness-repository-repair-001/qa.py` | core | 10061 | 286 | `6cb36ebb0fbc` |  |
| `services/harness/evals/harness-repository-repair-001/task.json` | config | 2523 | 70 | `35968c8d52b3` | 1 |
| `services/harness/evals/harness-repository-repair-001/verifier/test_outcome.py` | tests | 2438 | 74 | `65599a7f6200` |  |
| `services/harness/evidence/adaptive-edit-r2-live-ab-deepseek-flash-20260914.json` | evidence | 10239 | 287 | `99d0195bf479` | 1 |
| `services/harness/evidence/adaptive-edit-r2-live-ab-deepseek-flash-addressing-20260914.json` | evidence | 46062 | 1270 | `854e282ecd43` | 1 |
| `services/harness/evidence/adaptive-edit-r2-live-ab-deepseek-flash-multiregion-20260914.json` | evidence | 53238 | 1451 | `def799cedb83` | 1 |
| `services/harness/evidence/browser-security/agent-birth-provider-boundary-r1-20260918.json` | evidence | 2899 | 81 | `486419175388` | 1 |
| `services/harness/evidence/browser-security/browserless-canary-control-r1-20260918.json` | evidence | 2412 | 73 | `15b06e4e9ae8` | 1 |
| `services/harness/evidence/browser-security/browserless-canary-known-different-r1-20260918.json` | evidence | 2778 | 92 | `7e8137a2035a` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r1-20260917.json` | evidence | 6130 | 113 | `92b959e39c11` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r2-20260918.json` | evidence | 7751 | 130 | `a3e920b3d0ba` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r3-20260918.json` | evidence | 12138 | 376 | `82995409641d` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r3-geometry-ablation-20260918.json` | evidence | 1762 | 78 | `81d5e01336b4` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r3-repeatability-20260918.json` | evidence | 657 | 18 | `d07f995fab0d` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r3-run2-20260918.json` | evidence | 12138 | 376 | `82995409641d` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r4-cf07-analysis-20260918.json` | evidence | 4944 | 144 | `1e18a36e88c3` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r4-cf07-metadata-20260918.json` | evidence | 6905 | 251 | `cdd2d7e4d64c` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r4-cf07-outcome-anchor-20260918.json` | evidence | 638 | 17 | `bbc9cde55fa9` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r5-controlled-run1-20260918.json` | evidence | 17801 | 556 | `664034c1c524` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r5-controlled-run2-20260918.json` | evidence | 17801 | 556 | `664034c1c524` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r5-repeatability-20260918.json` | evidence | 1778 | 40 | `6d699e91b5fe` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r6-cf07-prospective-telemetry-20260918.json` | evidence | 3216 | 102 | `25fe7ddfbd3c` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r7-controlled-run1-20260918.json` | evidence | 23946 | 719 | `5b4dc770db2b` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r7-controlled-run2-20260918.json` | evidence | 23946 | 719 | `5b4dc770db2b` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r7-repeatability-20260918.json` | evidence | 1578 | 36 | `7163fababb41` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r8-fresh-service-run1-20260918.json` | evidence | 9150 | 283 | `d6c59d1efb23` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r8-fresh-service-run2-20260918.json` | evidence | 9150 | 283 | `d6c59d1efb23` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r8-repeatability-20260918.json` | evidence | 1911 | 53 | `c72b639b7985` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r9-repeatability-20260918.json` | evidence | 2618 | 84 | `018cb614ee09` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r9-window-placement-run1-20260918.json` | evidence | 9404 | 299 | `1f4dc26e898b` | 1 |
| `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r9-window-placement-run2-20260918.json` | evidence | 9404 | 299 | `1f4dc26e898b` | 1 |
| `services/harness/evidence/browser-security/pool-runner-r1-acceptance-20260918.json` | evidence | 6607 | 195 | `483495a12330` | 1 |
| `services/harness/evidence/codex-app-h3-live-64ab44b-20260731.json` | evidence | 19482 | 486 | `cd16c07bf415` | 1 |
| `services/harness/evidence/dap-r8-gdb-launch-20260914.json` | evidence | 6819 | 250 | `6ffb6f6ed6c6` | 1 |
| `services/harness/evidence/dap-r8-runtime-owned-attach-20260914.json` | evidence | 8628 | 292 | `8fb38d351c86` | 1 |
| `services/harness/evidence/harness-agent-first-mandate-6daeee4.json` | evidence | 3334 | 73 | `00cefdf50dad` | 1 |
| `services/harness/evidence/harness-agent-plugin-h1-acceptance-20260922.json` | evidence | 2354 | 69 | `92208b88962d` | 1 |
| `services/harness/evidence/harness-agent-plugin-h2-durable-gateway-effects-20260922.json` | evidence | 3190 | 86 | `aed7c7328458` | 1 |
| `services/harness/evidence/harness-agent-plugin-h2b-cooperative-cancellation-20260922.json` | evidence | 2005 | 53 | `c0c526ac6697` | 1 |
| `services/harness/evidence/harness-c3-agent-first-api-be7200a.json` | evidence | 2235 | 50 | `607214db8f30` | 1 |
| `services/harness/evidence/harness-campaign3-rich-effect-owner-v1-capture.json` | evidence | 3075 | 62 | `5695253f4148` | 1 |
| `services/harness/evidence/harness-campaign3-rich-effect-owner-v1-result.json` | evidence | 13241 | 334 | `bd251924d98b` | 1 |
| `services/harness/evidence/harness-campaign5-provider-route-preservation-v1-result.json` | evidence | 5120 | 123 | `0693df87e754` | 1 |
| `services/harness/evidence/harness-capability-environment-v1.json` | evidence | 5750 | 131 | `aa7d2c696268` | 1 |
| `services/harness/evidence/harness-conclusion-correction-separation-9e47ee6.json` | evidence | 6439 | 86 | `5a29ffeadb77` | 1 |
| `services/harness/evidence/harness-current-affordance-compact-v2.json` | evidence | 6282 | 144 | `e3a246284008` | 1 |
| `services/harness/evidence/harness-current-no-tool-conclusion-control-repair-v1.json` | evidence | 3034 | 84 | `d455cc726e63` | 1 |
| `services/harness/evidence/harness-deepseek-mixed-turn-6124cd2.json` | evidence | 2176 | 35 | `2a303fed515b` | 1 |
| `services/harness/evidence/harness-first-interface-owner-bridges-v2.json` | evidence | 5285 | 109 | `2e5590de0710` | 1 |
| `services/harness/evidence/harness-first-interface-owner-bridges-v3.json` | evidence | 4017 | 90 | `1f2abd65f175` | 1 |
| `services/harness/evidence/harness-first-interface-owner-bridges-v4.json` | evidence | 4817 | 90 | `3a2bd1a86071` | 1 |
| `services/harness/evidence/harness-first-interface-owner-bridges-v5.json` | evidence | 4793 | 111 | `2a2c8eaf2f38` | 1 |
| `services/harness/evidence/harness-first-interface-owner-composition-atlas-v1.json` | evidence | 4435 | 95 | `c14b0b932ed1` | 1 |
| `services/harness/evidence/harness-global-secondary-deepseek-51825aa.json` | evidence | 3757 | 89 | `4d9e168aa955` | 1 |
| `services/harness/evidence/harness-global-secondary-replan-a38f4cf.json` | evidence | 8766 | 191 | `eda4ac37044a` | 1 |
| `services/harness/evidence/harness-h0-deliberation-authority-9576039.json` | evidence | 46669 | 1 | `2398be1ddba7` | 1 |
| `services/harness/evidence/harness-h1-deliberation-composition-89a7fa1.json` | evidence | 23960 | 1 | `04a6a9164945` | 1 |
| `services/harness/evidence/harness-h1-independent-cli-e9612fa.json` | evidence | 2574 | 66 | `ced0eacfcd78` | 1 |
| `services/harness/evidence/harness-h2-deliberation-lifecycle-28d3a28.json` | evidence | 2460 | 1 | `feaa23f63b37` | 1 |
| `services/harness/evidence/harness-h2-deliberation-lifecycle-64f58c7.json` | evidence | 2460 | 1 | `9f4ecd3e5db3` | 1 |
| `services/harness/evidence/harness-h2-deliberation-lifecycle-6c0defb.json` | evidence | 2460 | 1 | `24de19548a41` | 1 |
| `services/harness/evidence/harness-h2-deliberation-lifecycle-8100879.json` | evidence | 2221 | 1 | `8a08890b40f3` | 1 |
| `services/harness/evidence/harness-h2-deliberation-lifecycle-89fc499.json` | evidence | 2460 | 1 | `9fa2ade3c9cf` | 1 |
| `services/harness/evidence/harness-h2-deliberation-lifecycle-ae02d6b.json` | evidence | 2221 | 1 | `c6ed2d527d6a` | 1 |
| `services/harness/evidence/harness-h2-runtime-r2-live-d50f609-20260731.json` | evidence | 9097 | 221 | `51ac196a80c9` | 1 |
| `services/harness/evidence/harness-h3-independent-product-1577610.json` | evidence | 2684 | 71 | `92eec4da2efe` | 1 |
| `services/harness/evidence/harness-h4-stress-ce7e861.json` | evidence | 3914 | 114 | `2912646e1fae` | 1 |
| `services/harness/evidence/harness-ha5-structured-completion-d7d5417.json` | evidence | 2698 | 55 | `c0ca99c13a99` | 1 |
| `services/harness/evidence/harness-i0-source-integration-0ec4f1b.json` | evidence | 1589 | 41 | `8dd34980fe1a` | 1 |
| `services/harness/evidence/harness-no-progress-conclusion-ownership-8170e65.json` | evidence | 5996 | 92 | `838a51499ce5` | 1 |
| `services/harness/evidence/harness-no-vpn-tool-continuity-49a3882.json` | evidence | 5661 | 105 | `3e3b0e48d5ed` | 1 |
| `services/harness/evidence/harness-pc11-working-view-ea38f34.json` | evidence | 4235 | 54 | `6b6c07585d33` | 1 |
| `services/harness/evidence/harness-pc110-caller-cognition-ingress-b640f2d.json` | evidence | 10735 | 71 | `10b134aa709c` | 1 |
| `services/harness/evidence/harness-pc111-interaction-durable-promotion-9e6f7dd.json` | evidence | 16472 | 95 | `9f41d2424d56` | 1 |
| `services/harness/evidence/harness-pc112-durable-cognition-supersession-425373c.json` | evidence | 11043 | 75 | `2ad7ac024e7f` | 1 |
| `services/harness/evidence/harness-pc12a-privacy-authority-a8a6a2f.json` | evidence | 4741 | 50 | `941f4a14bc15` | 1 |
| `services/harness/evidence/harness-pc12b-multiturn-working-view-fd13fab.json` | evidence | 4840 | 52 | `d163d2323989` | 1 |
| `services/harness/evidence/harness-pc13-agent-owned-working-set-fa23bfc.json` | evidence | 5507 | 54 | `de2a0d72bf08` | 1 |
| `services/harness/evidence/harness-pc14-discovery-selection-55cfe64.json` | evidence | 6650 | 57 | `7aa967dc2b20` | 1 |
| `services/harness/evidence/harness-pc15-epistemic-control-9e65feb.json` | evidence | 7258 | 60 | `2bc0b2b6ba7b` | 1 |
| `services/harness/evidence/harness-pc16-cross-process-tool-exchange-253f792.json` | evidence | 7005 | 57 | `11055aff28e1` | 1 |
| `services/harness/evidence/harness-pc17-durable-knowledge-promotion-5a0530a.json` | evidence | 7247 | 58 | `3e73938ccd2e` | 1 |
| `services/harness/evidence/harness-pc18-historical-cognition-recall-fceb781.json` | evidence | 9303 | 65 | `21270a45e0aa` | 1 |
| `services/harness/evidence/harness-pc19-cognition-transition-progress-8b0f025.json` | evidence | 9481 | 66 | `e4e2fa5f5bfc` | 1 |
| `services/harness/evidence/harness-post-skills-extraction-python-3.14.7-20260921.json` | evidence | 2168 | 70 | `5a4542db0e33` | 1 |
| `services/harness/evidence/harness-python-3.14.7-upgrade-20260921.json` | evidence | 2633 | 73 | `07273e2651b7` | 1 |
| `services/harness/evidence/harness-r0-cognition-product-composition-debb576.json` | evidence | 7941 | 61 | `d420a9095550` | 1 |
| `services/harness/evidence/harness-r1-single-capability-truth-716cc4b.json` | evidence | 9692 | 77 | `03620676ac61` | 1 |
| `services/harness/evidence/harness-r2-proven-kernel-extraction-a983c1a.json` | evidence | 12109 | 109 | `471d527e9d47` | 1 |
| `services/harness/evidence/harness-r2-three-kernel-lineage-badae55.json` | evidence | 7295 | 111 | `7573c8270a3b` | 1 |
| `services/harness/evidence/harness-r3-static-composition-admission-4e9d4b9.json` | evidence | 7945 | 117 | `0bfe2f95b8a9` | 1 |
| `services/harness/evidence/harness-r3-supported-agent-surface-fe6fc1a.json` | evidence | 8233 | 127 | `ec84b221889b` | 1 |
| `services/harness/evidence/harness-replacement-h5-live-76420e4-20260731.json` | evidence | 78540 | 1495 | `21f66bf54cd5` | 1 |
| `services/harness/evidence/harness-rsi-p0-agent-owned-multi-attempt-ae02d6b.json` | evidence | 5659 | 103 | `6b884e9dfe51` | 1 |
| `services/harness/evidence/harness-rsi-p1-live-multi-attempt-6c0defb.json` | evidence | 7261 | 1 | `603750ee88d4` | 1 |
| `services/harness/evidence/harness-rsi-p2-self-modification-5360130.json` | evidence | 7005 | 132 | `52eeee305839` | 1 |
| `services/harness/evidence/harness-rsi-p3-recursive-improvement-aea4ec1.json` | evidence | 9785 | 172 | `38800050c137` | 1 |
| `services/harness/evidence/harness-rsi-p4-capability-composition-9032d0f.json` | evidence | 7150 | 128 | `b93080439e85` | 1 |
| `services/harness/evidence/harness-rsi-p5-final-acceptance-89fc499.json` | evidence | 8579 | 134 | `d5b24697bc0b` | 1 |
| `services/harness/evidence/harness-rsi-p5-high-information-discovery-999d753.json` | evidence | 9995 | 156 | `be60e16fb782` | 1 |
| `services/harness/evidence/harness-source-reconciliation-structured-observation-v1.json` | evidence | 3843 | 75 | `db9d22a113a1` | 1 |
| `services/harness/evidence/harness-unreachable-abandonment-retirement-v1.json` | evidence | 4896 | 112 | `f0f415fe6677` | 1 |
| `services/harness/evidence/hermes-acp-h4-live-3d9a559-20260731.json` | evidence | 19322 | 479 | `3d4686c83604` | 1 |
| `services/harness/evidence/hho-p0-fault-matrix-50cb9b5.json` | evidence | 5729 | 144 | `d605b74f1d5d` | 1 |
| `services/harness/evidence/hho-p0-local-host-compat-73f7150.json` | evidence | 1382 | 38 | `7fde041086d6` | 1 |
| `services/harness/evidence/hho-p0-production-preflight-43d7820.json` | evidence | 2494 | 65 | `a99146a950f4` | 1 |
| `services/harness/evidence/hho-p0-release-h2-f7e03aa.json` | evidence | 9185 | 222 | `f5dbaed660e0` | 1 |
| `services/harness/evidence/hho-p0-scale-1000x100-50cb9b5.json` | evidence | 1338 | 49 | `c773d7b21601` | 1 |
| `services/harness/evidence/hho-p0-scale-1000x100-73f7150.json` | evidence | 1337 | 49 | `ecd8831d4b2d` | 1 |
| `services/harness/evidence/hho-p0-scale-1000x100-f7e03aa.json` | evidence | 1337 | 49 | `4c498fb23ecd` | 1 |
| `services/harness/evidence/index.json` | evidence | 59610 | 741 | `c4e1fd5e70fe` | 1 |
| `services/harness/evidence/lsp-r7-clangd-runtime-patch-20260914.json` | evidence | 3078 | 75 | `13e894c61b7b` | 1 |
| `services/harness/evidence/lsp-r7-lifecycle-faults-20260914.json` | evidence | 4851 | 162 | `dbb9660b8b00` | 1 |
| `services/harness/evidence/lsp-r7-lsp-client-lifecycle-20260914.json` | evidence | 5342 | 161 | `f3a99927d1a6` | 1 |
| `services/harness/evidence/lsp-r7-taplo-runtime-patch-20260914.json` | evidence | 3557 | 78 | `63cb32b0d743` | 1 |
| `services/harness/evidence/observation-exporter-e3cb34b.json` | evidence | 1762 | 47 | `06ec5071322a` | 1 |
| `services/harness/evidence/ordivon-harness-oh3-deepseek-live-20260801.json` | evidence | 2054 | 54 | `b0a9ba28c6bb` | 1 |
| `services/harness/evidence/ordivon-harness-oh4-deepseek-live-20260801.json` | evidence | 3403 | 68 | `4908e98c4edd` | 1 |
| `services/harness/evidence/ordivon-harness-oh5-recovery-live-20260801.json` | evidence | 3031 | 65 | `261524846bd4` | 1 |
| `services/harness/evidence/repository-repair-conclusion-gate-b23d5fa.json` | evidence | 1713 | 42 | `bb775ec76ed4` | 1 |
| `services/harness/evidence/repository-repair-edit-runtime-bridge-dd50136.json` | evidence | 1862 | 44 | `05fff350c418` | 1 |
| `services/harness/evidence/repository-repair-edit-runtime-bridge-e625671.json` | evidence | 1862 | 44 | `6328ea155446` | 1 |
| `services/harness/evidence/repository-repair-runtime-bridge-7664240.json` | evidence | 1670 | 41 | `9884b6fcb929` | 1 |
| `services/harness/evidence/system1-decision/browser-decision-crossencoder-r1-20260921.json` | evidence | 51594 | 1200 | `ad2bce7c0482` | 1 |
| `services/harness/evidence/system1-decision/browser-decision-jev-blocked-r1-20260921.json` | evidence | 9762 | 312 | `f1078b3031a0` | 1 |
| `services/harness/evidence/system1-decision/browser-decision-laya-r1-20260921.json` | evidence | 50477 | 1200 | `148857836a19` | 1 |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_domain__test_domain_0.json.json` | tests | 3219 | 1 | `be6884fbfc2c` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_domain__test_domain_1.json.json` | tests | 3322 | 1 | `9cbbfe59b910` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_domain__test_domain_2.json.json` | tests | 2997 | 1 | `4bb691f55809` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_domain__test_domain_3.json.json` | tests | 3483 | 1 | `378dbaa0fe3d` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_domain__test_domain_4.json.json` | tests | 2996 | 1 | `4373e96ce8fe` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_domain__test_domain_5.json.json` | tests | 2870 | 1 | `f4d991a7569c` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_domain__test_domain_6.json.json` | tests | 2967 | 1 | `776a7a07372d` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_domain__test_domain_7.json.json` | tests | 3218 | 1 | `30b307acbe00` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_domain__test_domain_8.json.json` | tests | 3267 | 1 | `dd354d5bbb0c` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_domain__test_domain_9.json.json` | tests | 515 | 1 | `9d93d311e191` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_task__test_task_0.json.json` | tests | 4197 | 1 | `339855e851b8` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_task__test_task_1.json.json` | tests | 3985 | 1 | `abf58bf7d865` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_task__test_task_2.json.json` | tests | 2417 | 1 | `e596c9f69ab6` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_website__test_website_0.json.json` | tests | 3685 | 1 | `a291eab42886` |  |
| `services/harness/evidence/system1-decision/mind2web-census-r1/test_website__test_website_1.json.json` | tests | 2640 | 1 | `dcd4acd249e6` |  |
| `services/harness/evidence/ts11-tool-surface-ablation.json` | evidence | 1846 | 52 | `a27a6194999c` | 1 |
| `services/harness/fixtures/harness-edit-addressing-repeated-v1/SPEC.md` | docs | 398 | 10 | `99237867516c` |  |
| `services/harness/fixtures/harness-edit-addressing-repeated-v1/feature_flags.py` | core | 93 | 6 | `0ca38f23695b` |  |
| `services/harness/fixtures/harness-edit-addressing-repeated-v1/test_feature_flags.py` | tests | 270 | 14 | `f39edbc84a4f` |  |
| `services/harness/fixtures/harness-edit-multiregion-v1/SPEC.md` | docs | 272 | 9 | `489aa796b13a` |  |
| `services/harness/fixtures/harness-edit-multiregion-v1/pipeline.py` | core | 119 | 9 | `68d63720f416` |  |
| `services/harness/fixtures/harness-edit-multiregion-v1/test_pipeline.py` | tests | 352 | 15 | `69b126073a14` |  |
| `services/harness/fixtures/harness-replacement-repository-repair-v1/SPEC.md` | docs | 933 | 24 | `e8e1700acd04` |  |
| `services/harness/fixtures/harness-replacement-repository-repair-v1/allocation.py` | core | 733 | 17 | `8440bc4569e8` |  |
| `services/harness/fixtures/harness-replacement-repository-repair-v1/artifacts/.gitkeep` | other | 0 | — | `e3b0c44298fc` |  |
| `services/harness/fixtures/harness-replacement-repository-repair-v1/test_allocation.py` | tests | 1227 | 38 | `ce3e62b4d533` |  |
| `services/harness/formal/ConversationBindingCutoverR1.admission-probe.cfg` | config | 147 | 5 | `f17e078d11ec` |  |
| `services/harness/formal/ConversationBindingCutoverR1.cfg` | config | 292 | 11 | `3b26d81bf6f6` |  |
| `services/harness/formal/ConversationBindingCutoverR1.growth-probe.cfg` | config | 159 | 5 | `ee83e3898d2c` |  |
| `services/harness/formal/ConversationBindingCutoverR1.interrupted-probe.cfg` | config | 153 | 5 | `3c2ff9925f25` |  |
| `services/harness/formal/ConversationBindingCutoverR1.tla` | core | 4240 | 135 | `989336d100ff` |  |
| `services/harness/formal/ProviderClaimR1.ack-probe.cfg` | config | 153 | 6 | `c5677f9557af` |  |
| `services/harness/formal/ProviderClaimR1.cfg` | config | 433 | 16 | `a1ee6171bbcb` |  |
| `services/harness/formal/ProviderClaimR1.delivery-probe.cfg` | config | 135 | 6 | `772ee86b7cad` |  |
| `services/harness/formal/ProviderClaimR1.expiry-probe.cfg` | config | 143 | 6 | `3b472355b40b` |  |
| `services/harness/formal/ProviderClaimR1.privacy-fresh-probe.cfg` | config | 147 | 6 | `21801553e83a` |  |
| `services/harness/formal/ProviderClaimR1.privacy-redacted-probe.cfg` | config | 148 | 6 | `4efba5908dbd` |  |
| `services/harness/formal/ProviderClaimR1.tla` | core | 7517 | 196 | `56b83453f71b` |  |
| `services/harness/formal/README.md` | docs | 4862 | 85 | `708b2eeb2cf6` |  |
| `services/harness/mise.toml` | config | 8383 | 189 | `86930c862f44` |  |
| `services/harness/planning/HARNESS_AGENT_TASK_REFINEMENT_SPEC_R1.md` | docs | 19027 | 172 | `107599aa3b37` |  |
| `services/harness/planning/browser-capability-router-r1.json` | config | 7769 | 227 | `1ec811a7111b` | 1 |
| `services/harness/planning/human-handoff-lego-r1.json` | config | 12592 | 321 | `f696e48acccc` | 1 |
| `services/harness/planning/lego-plan-r1.json` | config | 26017 | 338 | `252da3c7a687` | 1 |
| `services/harness/pyproject.toml` | config | 1621 | 68 | `95d663d34185` |  |
| `services/harness/research/00-OWNER-BOUNDARY.md` | research | 3712 | 48 | `8f45c27c0c74` |  |
| `services/harness/research/05-PROJECT-CONSTITUTION-V1.md` | research | 6175 | 104 | `00f983ee5c56` |  |
| `services/harness/research/10-FOUNDATION-FAMILIES.md` | research | 4307 | 79 | `5a605c20de77` |  |
| `services/harness/research/100-CAMPAIGN3-OPERATIONAL-EFFECT-STANDING-CHARTER-V1.md` | research | 15928 | 327 | `8a19be7a5706` |  |
| `services/harness/research/101-CAMPAIGN3-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md` | research | 16581 | 343 | `d6eb5a00fd2e` |  |
| `services/harness/research/102-CAMPAIGN3-ROUND2-ENGINEERING-DOGFOOD-CONTRACT.md` | research | 6211 | 120 | `72e485ae6718` |  |
| `services/harness/research/103-CAMPAIGN3-ROUND2-ENGINEERING-DOGFOOD-RESULT.md` | research | 7581 | 202 | `fdcb62bc99f9` |  |
| `services/harness/research/104-CAMPAIGN3-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md` | research | 12202 | 295 | `12d0848511de` |  |
| `services/harness/research/106-CAMPAIGN4-OPERATIONAL-ACCOUNTABILITY-CHARTER-V1.md` | research | 15551 | 345 | `b504f2792bb1` |  |
| `services/harness/research/107-CAMPAIGN4-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md` | research | 15954 | 374 | `d9c8bf8d3a9b` |  |
| `services/harness/research/108-CAMPAIGN4-ROUND2-ENGINEERING-DOGFOOD-CONTRACT.md` | research | 7165 | 143 | `e7fd2ad672ac` |  |
| `services/harness/research/109-CAMPAIGN4-ROUND2-ENGINEERING-DOGFOOD-RESULT.md` | research | 8210 | 218 | `994bd3f99e93` |  |
| `services/harness/research/110-CAMPAIGN4-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md` | research | 11984 | 282 | `bd12b2281788` |  |
| `services/harness/research/112-CAMPAIGN5-BOUNDARY-RECONFIGURATION-CHARTER-V1.md` | research | 13057 | 278 | `e87ef6ba972a` |  |
| `services/harness/research/113-CAMPAIGN5-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md` | research | 13845 | 317 | `5447fc5e12b8` |  |
| `services/harness/research/114-CAMPAIGN5-ROUND2-ENGINEERING-DOGFOOD-CONTRACT.md` | research | 5878 | 118 | `b80b3ca1899d` |  |
| `services/harness/research/115-CAMPAIGN5-ROUND2-ENGINEERING-DOGFOOD-RESULT.md` | research | 5636 | 116 | `bebc2bc999e3` |  |
| `services/harness/research/116-CAMPAIGN5-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md` | research | 11827 | 287 | `82b26fd48b0b` |  |
| `services/harness/research/118-CAMPAIGN6-FEDERATED-OPERATIONAL-IDENTITY-CHARTER-V1.md` | research | 11980 | 236 | `48f0e68a38f6` |  |
| `services/harness/research/119-CAMPAIGN6-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md` | research | 11846 | 324 | `ea3a9370c6ce` |  |
| `services/harness/research/120-CAMPAIGN6-ROUND2-ADJACENT-ENGINEERING-DOGFOOD-CONTRACT.md` | research | 5749 | 121 | `887a9213ddca` |  |
| `services/harness/research/121-CAMPAIGN6-ROUND2-ADJACENT-ENGINEERING-DOGFOOD-RESULT.md` | research | 6733 | 201 | `8fe6c4b7b95d` |  |
| `services/harness/research/122-CAMPAIGN6-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md` | research | 13413 | 344 | `3dce87340ae3` |  |
| `services/harness/research/124-FOR-DIRECT-DOGFOOD-V1-EXPERIMENT-CONTRACT.md` | research | 8948 | 228 | `6039486f86e6` |  |
| `services/harness/research/125-FOR-DIRECT-DOGFOOD-V1-RESULT-AND-CLOSEOUT.md` | research | 9995 | 283 | `160bdaa8d6ab` |  |
| `services/harness/research/127-OPERATIONAL-CLAIM-STANDING-V0-CHARTER.md` | research | 7771 | 193 | `914a5625cb28` |  |
| `services/harness/research/128-OPERATIONAL-CLAIM-STANDING-V0-DESTRUCTIVE-ANALYSIS.md` | research | 10286 | 304 | `c11a827c307c` |  |
| `services/harness/research/129-OPERATIONAL-CLAIM-STANDING-V0-REFERENCE-CONTRACT.md` | research | 7049 | 201 | `aed3863ec7ff` |  |
| `services/harness/research/130-OPERATIONAL-CLAIM-STANDING-V0-BOUNDARY-AUDIT-AND-CLOSEOUT.md` | research | 6013 | 189 | `282c71685c97` |  |
| `services/harness/research/132-CLAIM-STANDING-MINIMAL-MATERIALIZATION-V1-ACCEPTANCE-CONTRACT.md` | research | 7049 | 207 | `c1d31c4e5112` |  |
| `services/harness/research/133-CLAIM-STANDING-MINIMAL-MATERIALIZATION-V1-E5V2-RESULT-AND-CLOSEOUT.md` | research | 8793 | 295 | `9558f3331715` |  |
| `services/harness/research/135-CAMPAIGN4-COUNTEREVIDENCE-REBUTTAL-DIRECT-DOGFOOD-V1-CONTRACT.md` | research | 3966 | 136 | `9751fa9b437e` |  |
| `services/harness/research/136-CAMPAIGN4-COUNTEREVIDENCE-REBUTTAL-DIRECT-DOGFOOD-V1-RESULT-AND-CLOSEOUT.md` | research | 7468 | 233 | `991b8d387923` |  |
| `services/harness/research/137-TYPED-FRONTIER-TOURNAMENT-V2.md` | research | 15470 | 357 | `4200cfcfc82b` |  |
| `services/harness/research/138-CAMPAIGN3-REAL-RICH-EFFECT-OWNER-DOGFOOD-V1-CONTRACT.md` | research | 10400 | 262 | `6fd3b03daf69` |  |
| `services/harness/research/139-CAMPAIGN3-REAL-RICH-EFFECT-OWNER-DOGFOOD-V1-RESULT-AND-CLOSEOUT.md` | research | 9495 | 194 | `c28af6be3cf6` |  |
| `services/harness/research/140-POST-RICH-EFFECT-TYPED-FRONTIER-TOURNAMENT-V1.md` | research | 13195 | 297 | `5f20c94d74c3` |  |
| `services/harness/research/141-CAMPAIGN5-PROVIDER-ROUTE-PRESERVATION-DIRECT-DOGFOOD-V1-CONTRACT.md` | research | 10547 | 248 | `45864f4bb149` |  |
| `services/harness/research/142-CAMPAIGN5-PROVIDER-ROUTE-PRESERVATION-DIRECT-DOGFOOD-V1-RESULT-AND-CLOSEOUT.md` | research | 10319 | 255 | `943b78eb8ad9` |  |
| `services/harness/research/143-POST-PROVIDER-ROUTE-TYPED-FRONTIER-TOURNAMENT-V1.md` | research | 18560 | 361 | `3a6284ac31aa` |  |
| `services/harness/research/144-CURRENT-NO-TOOL-CONCLUSION-CONTROL-REGRESSION-REPAIR-V1-CONTRACT.md` | research | 10230 | 246 | `2f8670c11f93` |  |
| `services/harness/research/145-CURRENT-NO-TOOL-CONCLUSION-CONTROL-REGRESSION-REPAIR-V1-RESULT-AND-CLOSEOUT.md` | research | 10198 | 300 | `c87d6280afc8` |  |
| `services/harness/research/146-POST-NO-TOOL-REPAIR-TYPED-FRONTIER-TOURNAMENT-V1.md` | research | 13229 | 320 | `df5f3356b326` |  |
| `services/harness/research/147-EVIDENCE-INDEX-TYPED-INGESTION-CURRENTNESS-REPAIR-V1-CONTRACT.md` | research | 5733 | 150 | `548f430b2657` |  |
| `services/harness/research/148-EVIDENCE-INDEX-TYPED-INGESTION-CURRENTNESS-REPAIR-V1-RESULT-AND-CLOSEOUT.md` | research | 11778 | 315 | `fb5c7c3e74fe` |  |
| `services/harness/research/149-POST-EVIDENCE-REPAIR-TYPED-FRONTIER-TOURNAMENT-V1.md` | research | 9559 | 242 | `2e8917226f47` |  |
| `services/harness/research/15-RESEARCH-PROGRAMME-MAP-V1.md` | research | 7308 | 144 | `cba0c5b57482` |  |
| `services/harness/research/150-WHEEL-PUBLIC-API-CONTRACT-CURRENTNESS-REPAIR-V1-CONTRACT.md` | research | 2387 | 68 | `d8c40dbb9bb3` |  |
| `services/harness/research/151-WHEEL-PUBLIC-API-CONTRACT-CURRENTNESS-REPAIR-V1-RESULT-AND-CLOSEOUT.md` | research | 3555 | 145 | `ea989b68333b` |  |
| `services/harness/research/152-POST-WHEEL-REPAIR-TYPED-FRONTIER-TOURNAMENT-V1.md` | research | 5728 | 158 | `2ebb0a9b31a3` |  |
| `services/harness/research/153-FRESH-AGENT-CAPABILITY-CURRENTNESS-ABLATION-V1-V2-RESULT-AND-CLOSEOUT.md` | research | 11070 | 275 | `e33285327319` |  |
| `services/harness/research/153-PROVIDER-FIRST-HTTPX-TRANSPORT-CURRENT-REVALIDATION-V1-RESULT-AND-CLOSEOUT.md` | research | 11209 | 254 | `90c511f4f6b5` |  |
| `services/harness/research/154-POST-HTTPX-EVIDENCE-CURRENTNESS-REPAIR-V1-CONTRACT.md` | research | 2733 | 43 | `8930945fcfc3` |  |
| `services/harness/research/155-POST-HTTPX-EVIDENCE-CURRENTNESS-REPAIR-V1-RESULT-AND-CLOSEOUT.md` | research | 4653 | 124 | `721d0bcd714c` |  |
| `services/harness/research/156-POST-BATCH-SEARCH-EVIDENCE-CURRENTNESS-REPAIR-V1-CONTRACT.md` | research | 1880 | 24 | `c1f4222392b5` |  |
| `services/harness/research/157-POST-BATCH-SEARCH-EVIDENCE-CURRENTNESS-REPAIR-V1-RESULT-AND-CLOSEOUT.md` | research | 3533 | 89 | `fb2c429d1a52` |  |
| `services/harness/research/20-OPERATIONAL-SPINE.md` | research | 1898 | 36 | `3e1c0b1ab973` |  |
| `services/harness/research/30-DERIVED-LAWS.md` | research | 9624 | 110 | `aa39e096ae07` |  |
| `services/harness/research/40-CROSS-OWNER-BRIDGES.md` | research | 2763 | 48 | `7a4d48a6ce80` |  |
| `services/harness/research/50-ENGINEERING-CONSUMPTION-MAP.md` | research | 4219 | 79 | `80ab38ca2631` |  |
| `services/harness/research/60-HAF-REGISTRY-AND-PROVENANCE.md` | research | 10908 | 79 | `aa0c8a5549d2` |  |
| `services/harness/research/70-HISTORY-NEGATIVE-RESULTS-AND-REPAIRS.md` | research | 2509 | 48 | `4243ad25805d` |  |
| `services/harness/research/80-OPEN-FRONTIER-AND-REOPEN.md` | research | 1917 | 38 | `4ae61494d781` |  |
| `services/harness/research/85-FRONTIER-AUDIT-V1.md` | research | 7021 | 131 | `c2e7677e2903` |  |
| `services/harness/research/88-CAMPAIGN1-OPERATIONAL-IDENTITY-UNDER-FAILURE-CHARTER-V1.md` | research | 13729 | 239 | `06843cc88475` |  |
| `services/harness/research/89-CAMPAIGN1-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md` | research | 13983 | 259 | `e4c31416dd2b` |  |
| `services/harness/research/90-CAMPAIGN1-ROUND2-ENGINEERING-DOGFOOD-CONTRACT.md` | research | 6317 | 135 | `471f5cd0c89e` |  |
| `services/harness/research/91-CAMPAIGN1-ROUND2-ENGINEERING-DOGFOOD-RESULT.md` | research | 8411 | 167 | `fd2074e96c62` |  |
| `services/harness/research/92-CAMPAIGN1-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md` | research | 10710 | 250 | `cc98844fe9fd` |  |
| `services/harness/research/94-CAMPAIGN2-OPERATIONAL-CONTEXT-EQUIVALENCE-CHARTER-V1.md` | research | 15773 | 279 | `520ffbdbae71` |  |
| `services/harness/research/95-CAMPAIGN2-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md` | research | 14995 | 283 | `dbca14e2e369` |  |
| `services/harness/research/96-CAMPAIGN2-ROUND2-ENGINEERING-DOGFOOD-CONTRACT.md` | research | 6010 | 115 | `c00f058f857d` |  |
| `services/harness/research/97-CAMPAIGN2-ROUND2-ENGINEERING-DOGFOOD-RESULT.md` | research | 7332 | 167 | `a803234e78de` |  |
| `services/harness/research/98-CAMPAIGN2-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md` | research | 10894 | 240 | `9084957721c0` |  |
| `services/harness/research/README.md` | research | 14571 | 123 | `c6f3a2e8c7ba` |  |
| `services/harness/research/authority/CURRENT.json` | research | 399 | 8 | `b7f2192cfa07` | 1 |
| `services/harness/research/authority/publications/7fa847df5d74a23380b3fa830cf7996382bbdc3f0c29533015588c2b780ab333.json` | evidence | 11185 | 290 | `7fa847df5d74` | 1 |
| `services/harness/research/experiments/browser-security-r3/neutral_differential.py` | research | 16671 | 465 | `e09fefd82fce` |  |
| `services/harness/research/experiments/browser-security-r4/cf07_metadata_snapshot.py` | research | 16707 | 476 | `9e6136a40b37` |  |
| `services/harness/research/experiments/browser-security-r5/container_direct_differential.py` | research | 17809 | 491 | `8127aa6e6aad` |  |
| `services/harness/research/experiments/browser-security-r7/launcher_default_ablation.py` | research | 14772 | 409 | `3c7c0efabcbf` |  |
| `services/harness/research/experiments/browser-security-r8/fresh_service_attribution.py` | research | 9907 | 236 | `7d0cbf5c9be9` |  |
| `services/harness/research/experiments/browser-security-r9/window_placement_attribution.py` | research | 13191 | 321 | `18273f131b08` |  |
| `services/harness/research/experiments/browser_ax_projection_v1.py` | research | 13235 | 390 | `e4cf0c750e6e` |  |
| `services/harness/research/experiments/browser_decision_duel_analysis_r1.py` | research | 14355 | 380 | `0b69a8cff756` |  |
| `services/harness/research/experiments/browser_decision_provider_eval_r1.py` | research | 9772 | 278 | `c5d11a4fdc4d` |  |
| `services/harness/research/experiments/build_browser_decision_corpus_r1.py` | research | 15525 | 309 | `40b5d060287c` |  |
| `services/harness/research/experiments/campaign3_rich_effect_owner_v1.py` | research | 10656 | 185 | `8aa7ccbe7efe` |  |
| `services/harness/research/experiments/campaign4_rebuttal_direct_v1.py` | research | 5295 | 119 | `99605ee0aadc` |  |
| `services/harness/research/experiments/campaign5_provider_route_preservation_v1.py` | research | 16520 | 428 | `a2c6cca08198` |  |
| `services/harness/research/experiments/claim_standing_e5_v2.py` | research | 5110 | 138 | `3e24988731c8` |  |
| `services/harness/research/experiments/for_direct_federation_v1.py` | research | 21471 | 555 | `f77de7f548eb` |  |
| `services/harness/research/experiments/harness_temporal_needs_input_pilot.py` | research | 8812 | 242 | `9d8c621eb467` |  |
| `services/harness/research/experiments/harness_temporal_needs_input_segment.py` | research | 6959 | 171 | `987d529db209` |  |
| `services/harness/research/fixtures/browser_ax_cross_origin_child.html` | research | 380 | — | `f5ef74657220` |  |
| `services/harness/research/fixtures/browser_ax_generalization_r1.html` | research | 3966 | — | `a69f0d10471e` |  |
| `services/harness/research/fixtures/research-fresh-agent-corpus-r1.json` | research | 6830 | 190 | `3e0a74ab4075` | 1 |
| `services/harness/schemas/agent-automation/campaign-spec-v2.schema.json` | schemas | 821 | 26 | `bc06612764f8` |  |
| `services/harness/scripts/acceptance_h0_deliberation_authority.py` | core | 21886 | 589 | `70ce11c53d55` |  |
| `services/harness/scripts/agent_automation_browserless.py` | core | 84099 | 1937 | `8f9c849cd47e` |  |
| `services/harness/scripts/agent_automation_browserless_effects.py` | core | 31127 | 692 | `066e40d1f4c6` |  |
| `services/harness/scripts/agent_automation_ledger_reconcile.py` | core | 5859 | 173 | `baf9c65c4935` |  |
| `services/harness/scripts/agent_automation_mcp.py` | core | 23496 | 552 | `cae021b7a730` |  |
| `services/harness/scripts/agent_automation_mcp_deploy.py` | core | 15644 | 430 | `ff8c282f3947` |  |
| `services/harness/scripts/agent_automation_registry.py` | core | 9101 | 244 | `aa86194e3b70` |  |
| `services/harness/scripts/agent_automation_release.py` | core | 48383 | 1218 | `20ecd686be04` |  |
| `services/harness/scripts/browser_benchmark_contract.py` | core | 21886 | 514 | `cf151ff5ff73` |  |
| `services/harness/scripts/browser_benchmark_prospective.py` | core | 11925 | 323 | `b4c34c8f384f` |  |
| `services/harness/scripts/browser_benchmark_route_adapter.py` | core | 21303 | 531 | `7bf55d9166ae` |  |
| `services/harness/scripts/browser_benchmark_runner.py` | core | 11519 | 310 | `2dff1c5261c9` |  |
| `services/harness/scripts/browser_benchmark_runtime_handoff.py` | core | 16509 | 430 | `1b7853880037` |  |
| `services/harness/scripts/browser_capability_router.py` | core | 24100 | 630 | `7f96388ad46c` |  |
| `services/harness/scripts/browser_security_browserless_canary.py` | core | 23311 | 602 | `aa18b7c3f44f` |  |
| `services/harness/scripts/browser_security_pool_runner.py` | core | 16166 | 448 | `12dc75830516` |  |
| `services/harness/scripts/browser_security_witness_source.py` | core | 22039 | 575 | `14f912c092a9` |  |
| `services/harness/scripts/browser_use_browserless.py` | core | 15567 | 405 | `5ff70ef02f0f` |  |
| `services/harness/scripts/browserless_display_auth.py` | core | 3839 | 114 | `247ea7a50936` |  |
| `services/harness/scripts/browserless_human_handoff.py` | core | 8330 | 248 | `0d4d916e3509` |  |
| `services/harness/scripts/browserless_human_interaction.py` | core | 5041 | 158 | `bceb7c2776c1` |  |
| `services/harness/scripts/browserless_idle_reaper.py` | core | 6000 | 170 | `89301cd9e127` |  |
| `services/harness/scripts/browserless_image_promotion.py` | core | 37373 | 863 | `f59cea6269f5` |  |
| `services/harness/scripts/browserless_materialization_target.py` | core | 17434 | 391 | `2ffdaec4e48c` |  |
| `services/harness/scripts/browserless_podman_deploy.py` | core | 30857 | 711 | `ddd159753bb1` |  |
| `services/harness/scripts/browserless_substrate.py` | core | 22268 | 512 | `c9cfc762aab7` |  |
| `services/harness/scripts/campaign_materialization.py` | core | 9108 | 255 | `b42e74745696` |  |
| `services/harness/scripts/cft_human_materialization.py` | core | 16753 | 384 | `287960a182bf` |  |
| `services/harness/scripts/cft_human_session.py` | core | 23644 | 605 | `46cab2263dc4` |  |
| `services/harness/scripts/cft_human_session_auth.py` | core | 2207 | 84 | `ce3f67f7aa9c` |  |
| `services/harness/scripts/cft_human_session_deploy.py` | core | 6126 | 163 | `e8be6d2f6307` |  |
| `services/harness/scripts/chatgpt_conversation_discovery.py` | core | 7120 | 193 | `226f108bd162` |  |
| `services/harness/scripts/chatgpt_provider_gate.py` | core | 1156 | 40 | `7c028cd8ed6e` |  |
| `services/harness/scripts/chatgpt_provider_resource.py` | core | 2756 | 73 | `8a5c8cc59c87` |  |
| `services/harness/scripts/check_adaptive_edit_r2_benchmark.py` | core | 7763 | 209 | `244d8621ed65` |  |
| `services/harness/scripts/check_codex_app_h3_receipt.py` | core | 14716 | 313 | `41a7f35cbac3` |  |
| `services/harness/scripts/check_dependencies.py` | core | 3280 | 85 | `552423487165` |  |
| `services/harness/scripts/check_docs.py` | core | 18550 | 456 | `aa60d7bd34a6` |  |
| `services/harness/scripts/check_evidence.py` | core | 39062 | 1008 | `a2a475f4a79e` |  |
| `services/harness/scripts/check_harness_replacement_h5_receipt.py` | core | 28656 | 599 | `bea75a868d76` |  |
| `services/harness/scripts/check_harness_without_host.py` | core | 4342 | 114 | `2ce5344f4fc4` |  |
| `services/harness/scripts/check_hermes_acp_h4_receipt.py` | core | 18911 | 404 | `c332fa94959f` |  |
| `services/harness/scripts/check_repository_repair_edit_runtime_receipt.py` | core | 5489 | 151 | `49fcdeaf4101` |  |
| `services/harness/scripts/check_runtime_search_profile.py` | core | 938 | 32 | `65d42f472a57` |  |
| `services/harness/scripts/check_wheel.py` | core | 14280 | 368 | `beddc24a7bb1` |  |
| `services/harness/scripts/configure_deepseek_api.py` | core | 8804 | 247 | `db44494364ef` |  |
| `services/harness/scripts/conversation_binding_contract.py` | core | 3016 | 100 | `ab41eed0bda2` |  |
| `services/harness/scripts/conversation_relay_carrier.py` | core | 7614 | 194 | `6bc66f05d45d` |  |
| `services/harness/scripts/demo_deterministic_run.py` | core | 4056 | 135 | `6ac9266804dc` |  |
| `services/harness/scripts/finance_current_state_application.py` | core | 15836 | 404 | `a07657eee6dd` |  |
| `services/harness/scripts/finance_readonly_observation.py` | core | 16476 | 440 | `1b721d69ebb3` |  |
| `services/harness/scripts/harness_otel_event_sink.py` | core | 7507 | 179 | `86f9b31c75e2` |  |
| `services/harness/scripts/harness_p0_scale_acceptance.py` | core | 10903 | 279 | `ce7d61a036d6` |  |
| `services/harness/scripts/harness_replacement_h5_support.py` | core | 7010 | 209 | `b59eb24412f1` |  |
| `services/harness/scripts/jev_active_user_launcher.ps1` | core | 1724 | 45 | `8246eea2dcb8` |  |
| `services/harness/scripts/jev_fastpath_adapter.py` | core | 24999 | 682 | `eff17eaade78` |  |
| `services/harness/scripts/local-acceptance` | other | 2567 | — | `b410149febf9` |  |
| `services/harness/scripts/materialization_reconciliation_archive.py` | core | 11665 | 302 | `74bcf0569bbd` |  |
| `services/harness/scripts/mind2web_crossencoder_benchmark.py` | core | 5382 | 156 | `908c44fc6c58` |  |
| `services/harness/scripts/mind2web_external_corpus.py` | core | 14628 | 384 | `784fe1ed3103` |  |
| `services/harness/scripts/mind2web_laya_benchmark.py` | core | 5421 | 159 | `3bd3a28d4853` |  |
| `services/harness/scripts/mind2web_shard_census.py` | core | 1080 | 38 | `a41c6d8e63d3` |  |
| `services/harness/scripts/owner-environment` | other | 3361 | — | `777335490741` |  |
| `services/harness/scripts/playwright_browserless_binding_reconcile.py` | core | 3383 | 89 | `9865ca8bc107` |  |
| `services/harness/scripts/playwright_browserless_chatgpt_submit.py` | core | 15076 | 399 | `f888d7e5ca96` |  |
| `services/harness/scripts/playwright_browserless_conversation_output.py` | core | 11723 | 267 | `fbd2a9b72497` |  |
| `services/harness/scripts/playwright_browserless_human_resume.py` | core | 14140 | 376 | `d2e7b9cef7af` |  |
| `services/harness/scripts/playwright_browserless_provider_preflight.py` | core | 8517 | 224 | `ed80630641b8` |  |
| `services/harness/scripts/playwright_browserless_turn_once.py` | core | 20582 | 454 | `3445cf11ce24` |  |
| `services/harness/scripts/playwright_cft_chatgpt_resume.py` | core | 7793 | 190 | `985dc5052e92` |  |
| `services/harness/scripts/postgres_conversation_binding.py` | core | 22177 | 470 | `55edd372ff08` |  |
| `services/harness/scripts/postgres_turn_effects.py` | core | 22125 | 439 | `d223a2f1283a` |  |
| `services/harness/scripts/postgres_wake_turn_map.py` | core | 27270 | 578 | `1fc7083cc106` |  |
| `services/harness/scripts/provider_boundary_diagnosis.py` | core | 6790 | 187 | `7d09d61e65ab` |  |
| `services/harness/scripts/run_adaptive_edit_r2_live_ab.py` | core | 29603 | 722 | `21e35d4ee67d` |  |
| `services/harness/scripts/sqlite_conversation_binding.py` | core | 8978 | 235 | `39b265e32ad5` |  |
| `services/harness/scripts/sqlite_conversation_materializer.py` | core | 19280 | 444 | `23985b95f95b` |  |
| `services/harness/scripts/sqlite_wake_turn_map.py` | core | 6782 | 176 | `7b7de0f97da5` |  |
| `services/harness/scripts/standard_identifiers.py` | core | 848 | 21 | `24f751090b7f` |  |
| `services/harness/scripts/system1_decision_benchmark.py` | core | 15761 | 364 | `7891ea979152` |  |
| `services/harness/scripts/temporal_agent_automation.py` | core | 25492 | 538 | `2fa79e118d2e` |  |
| `services/harness/scripts/temporal_agent_automation_deploy.py` | core | 7685 | 204 | `5ab85554200f` |  |
| `services/harness/scripts/temporal_agent_automation_launch.py` | core | 13282 | 333 | `a309a450d75a` |  |
| `services/harness/scripts/temporal_agent_automation_worker.py` | core | 604 | 21 | `4fc5ce6c4abf` |  |
| `services/harness/scripts/wake_turn_contract.py` | core | 914 | 33 | `631ce6e1ae1f` |  |
| `services/harness/scripts/windows_user_browser_chatgpt.ps1` | core | 13317 | 288 | `b66210f115cc` |  |
| `services/harness/scripts/windows_user_browser_materialization_target.py` | core | 6198 | 141 | `170232099cf0` |  |
| `services/harness/src/anc_canonical/__init__.py` | core | 456 | 25 | `6e2f6221144e` |  |
| `services/harness/src/anc_canonical/canonical.py` | core | 3165 | 102 | `476271a65135` |  |
| `services/harness/src/ordivon_harness/__init__.py` | core | 304 | 10 | `fabf01bd9929` |  |
| `services/harness/src/ordivon_harness/adaptive_edit.py` | core | 18770 | 523 | `a9deb6347c8a` |  |
| `services/harness/src/ordivon_harness/agent_plugin.py` | core | 9320 | 235 | `39945fc1858a` |  |
| `services/harness/src/ordivon_harness/agent_run.py` | core | 23899 | 580 | `d0e3d069b614` |  |
| `services/harness/src/ordivon_harness/agent_tool_observation.py` | core | 8654 | 203 | `2b896e76617d` |  |
| `services/harness/src/ordivon_harness/api.py` | core | 3807 | 121 | `0a17146bcfb0` |  |
| `services/harness/src/ordivon_harness/cli.py` | core | 4263 | 128 | `77385d24a48e` |  |
| `services/harness/src/ordivon_harness/completion.py` | core | 4788 | 128 | `1310ec659882` |  |
| `services/harness/src/ordivon_harness/core_contracts.py` | core | 17669 | 405 | `686a56bd60f1` |  |
| `services/harness/src/ordivon_harness/dap_provider_port.py` | core | 13510 | 385 | `660a7a2b7523` |  |
| `services/harness/src/ordivon_harness/domain_tools.py` | core | 9549 | 250 | `c7ba2bc00141` |  |
| `services/harness/src/ordivon_harness/execution_binding.py` | core | 6410 | 157 | `73f6678e34c6` |  |
| `services/harness/src/ordivon_harness/gateway_execution_port.py` | core | 14079 | 312 | `d1f5cdea90a7` |  |
| `services/harness/src/ordivon_harness/independent_cli.py` | core | 9139 | 250 | `ae68fce5721b` |  |
| `services/harness/src/ordivon_harness/independent_result.py` | core | 42822 | 902 | `1551a35d6c1e` |  |
| `services/harness/src/ordivon_harness/lsp_provider_port.py` | core | 9064 | 254 | `b04e419a7c8f` |  |
| `services/harness/src/ordivon_harness/lsp_workspace_edit.py` | core | 14412 | 359 | `e266db24e0b2` |  |
| `services/harness/src/ordivon_harness/mcp_http_client.py` | core | 6414 | 169 | `25155b045183` |  |
| `services/harness/src/ordivon_harness/object_store.py` | core | 8174 | 208 | `1e7a6da2e65e` |  |
| `services/harness/src/ordivon_harness/ordivon/__init__.py` | core | 330 | 10 | `590ff6bd6b9d` |  |
| `services/harness/src/ordivon_harness/ordivon/adaptive_edit_bridge.py` | core | 17757 | 485 | `27dcdd4b8a26` |  |
| `services/harness/src/ordivon_harness/ordivon/agent_bridge.py` | core | 15563 | 389 | `6b87d3ac3f8d` |  |
| `services/harness/src/ordivon_harness/ordivon/cognition_admission.py` | core | 4146 | 116 | `5ca9858c1207` |  |
| `services/harness/src/ordivon_harness/ordivon/continuity_guards.py` | core | 6738 | 169 | `3da645ce370b` |  |
| `services/harness/src/ordivon_harness/ordivon/continuity_records.py` | core | 19304 | 483 | `f251ce2109fd` |  |
| `services/harness/src/ordivon_harness/ordivon/control.py` | core | 2891 | 91 | `903b1654b517` |  |
| `services/harness/src/ordivon_harness/ordivon/deepseek.py` | core | 47319 | 1154 | `a4abc666d697` |  |
| `services/harness/src/ordivon_harness/ordivon/deepseek_protocol.py` | core | 21247 | 515 | `109e435ba380` |  |
| `services/harness/src/ordivon_harness/ordivon/events.py` | core | 7683 | 201 | `37027adeb3aa` |  |
| `services/harness/src/ordivon_harness/ordivon/loop.py` | core | 109873 | 2366 | `ecd016f277a8` |  |
| `services/harness/src/ordivon_harness/ordivon/model.py` | core | 32392 | 804 | `f07dcb1ffbbc` |  |
| `services/harness/src/ordivon_harness/ordivon/provider_lifecycle.py` | core | 5599 | 142 | `e9a84f54db0d` |  |
| `services/harness/src/ordivon_harness/ordivon/provider_state_guards.py` | core | 8743 | 228 | `43c8aa6a5b83` |  |
| `services/harness/src/ordivon_harness/ordivon/run_continuity.py` | core | 139920 | 3186 | `95b27a07b5bb` |  |
| `services/harness/src/ordivon_harness/ordivon/run_contract.py` | core | 9612 | 232 | `5bf195f18a14` |  |
| `services/harness/src/ordivon_harness/ordivon/run_recovery.py` | core | 12456 | 317 | `e12c8a48057c` |  |
| `services/harness/src/ordivon_harness/ordivon/run_store_port.py` | core | 7471 | 275 | `56c94c8d99dd` |  |
| `services/harness/src/ordivon_harness/ordivon/runtime_bridge.py` | core | 62068 | 1492 | `05cb6fbf0e22` |  |
| `services/harness/src/ordivon_harness/ordivon/runtime_lowering.py` | core | 26489 | 661 | `b360e73f3380` |  |
| `services/harness/src/ordivon_harness/ordivon/tool_bridge.py` | core | 483 | 20 | `aa582202d3fc` |  |
| `services/harness/src/ordivon_harness/ordivon/tool_errors.py` | core | 901 | 35 | `fdfdb22be06e` |  |
| `services/harness/src/ordivon_harness/ordivon/turn_projection.py` | core | 13691 | 342 | `93517d008ed4` |  |
| `services/harness/src/ordivon_harness/ordivon/working_set_queries.py` | core | 15665 | 368 | `389f2e6754de` |  |
| `services/harness/src/ordivon_harness/plugin_gateway_effect.py` | core | 32679 | 758 | `ca9010a9b6a5` |  |
| `services/harness/src/ordivon_harness/plugin_mcp.py` | core | 6470 | 162 | `9a2ffcccc0bf` |  |
| `services/harness/src/ordivon_harness/postgres_store.py` | core | 33244 | 758 | `5328bd75c5ba` |  |
| `services/harness/src/ordivon_harness/protocol.py` | core | 36117 | 956 | `ed210e935d5b` |  |
| `services/harness/src/ordivon_harness/run_state.py` | core | 22744 | 539 | `fc2d342e0126` |  |
| `services/harness/src/ordivon_harness/runtime_port.py` | core | 2062 | 65 | `c72c407e9010` |  |
| `services/harness/src/ordivon_harness/sqlite_store.py` | core | 46296 | 1065 | `cafa88c52405` |  |
| `services/harness/src/ordivon_harness/standalone.py` | core | 15011 | 392 | `63f8a9ef0189` |  |
| `services/harness/src/ordivon_harness/store.py` | core | 7599 | 254 | `0cc00c8f06a6` |  |
| `services/harness/src/ordivon_harness/store_errors.py` | core | 554 | 36 | `02d558700033` |  |
| `services/harness/src/ordivon_harness/structured_result_conformance.py` | core | 6777 | 179 | `f1cd0f817728` |  |
| `services/harness/src/ordivon_harness/tool_program.py` | core | 10271 | 256 | `6958121fe82a` |  |
| `services/harness/src/ordivon_harness/tool_program_contract.py` | core | 10522 | 272 | `afa2e40f1ba6` |  |
| `services/harness/src/ordivon_harness/tool_program_recovery.py` | core | 10913 | 280 | `b8eb79c4a13b` |  |
| `services/harness/src/ordivon_harness/user_browser_gateway.py` | core | 9760 | 217 | `f827923255af` |  |
| `services/harness/src/ordivon_harness/version.py` | core | 345 | 15 | `cfe4177b5f4d` |  |
| `services/harness/src/ordivon_harness/working_view.py` | core | 24952 | 675 | `c98214ddfd64` |  |
| `services/harness/systemd/ordivon-agent-automation-mcp.service` | config | 2012 | 35 | `c22bc88f9b66` |  |
| `services/harness/systemd/ordivon-agent-temporal-worker.service` | config | 1576 | 37 | `4b705b40caf5` |  |
| `services/harness/systemd/ordivon-browser-agent.target` | config | 295 | — | `857c99101217` |  |
| `services/harness/systemd/ordivon-browserless-display@.service` | config | 461 | 14 | `fb4a7f76737f` |  |
| `services/harness/systemd/ordivon-browserless-human-vnc@.service` | config | 506 | 16 | `dbc612d24aa6` |  |
| `services/harness/systemd/ordivon-browserless-human-web@.service` | config | 477 | 16 | `8d53c5e5a3f1` |  |
| `services/harness/systemd/ordivon-browserless-idle-reaper.service` | config | 366 | 8 | `a6cede4adf8b` |  |
| `services/harness/systemd/ordivon-browserless-idle-reaper.timer` | config | 230 | — | `f646713ff4fc` |  |
| `services/harness/systemd/ordivon-browserless-operator-proxy@.service` | config | 399 | 13 | `5c245a595a59` |  |
| `services/harness/systemd/ordivon-cft-human-browser@.service` | config | 958 | 27 | `b163a0a7dd9a` |  |
| `services/harness/systemd/ordivon-cft-human-display@.service` | config | 530 | 18 | `f01b9594bb00` |  |
| `services/harness/systemd/ordivon-cft-human-session@.target` | config | 376 | — | `6574f2768218` |  |
| `services/harness/systemd/ordivon-cft-human-vnc@.service` | config | 662 | 20 | `182ef93e8174` |  |
| `services/harness/systemd/ordivon-cft-human-web@.service` | config | 554 | 20 | `29b02c57ad94` |  |
| `services/harness/tests/conftest.py` | tests | 297 | 13 | `7c31935d3daf` |  |
| `services/harness/tests/fixtures/engineering_incident_browserless_20260909.json` | tests | 5954 | 123 | `adf496bfafd7` | 1 |
| `services/harness/tests/fixtures/provider-call-v3-s0-frozen.json` | tests | 1619 | 30 | `04377b5dfe4d` | 3 |
| `services/harness/tests/pg_test_support.py` | tests | 1752 | 50 | `17207df2a54f` |  |
| `services/harness/tests/test_adaptive_edit.py` | tests | 12293 | 312 | `2a3ebe9597e8` |  |
| `services/harness/tests/test_adaptive_edit_bridge.py` | tests | 17455 | 418 | `0b8ef5f5238d` |  |
| `services/harness/tests/test_adaptive_edit_r2_benchmark.py` | tests | 1424 | 36 | `7e354a092c2a` |  |
| `services/harness/tests/test_adaptive_edit_r2_live_ab_runner.py` | tests | 9422 | 225 | `ff907ee5b238` |  |
| `services/harness/tests/test_agent_automation_browserless.py` | tests | 106054 | 2285 | `2baba29d6cb3` |  |
| `services/harness/tests/test_agent_automation_browserless_effects.py` | tests | 1446 | 46 | `7a7d605fb71b` |  |
| `services/harness/tests/test_agent_automation_jcs_standard.py` | tests | 2395 | 54 | `6c17fd576b94` |  |
| `services/harness/tests/test_agent_automation_ledger_reconcile.py` | tests | 6429 | 185 | `bf85b2d63ad8` |  |
| `services/harness/tests/test_agent_automation_mcp.py` | tests | 13956 | 316 | `44658b01baa4` |  |
| `services/harness/tests/test_agent_automation_mcp_deploy.py` | tests | 21344 | 474 | `cbcbd0917e64` |  |
| `services/harness/tests/test_agent_automation_occurrence_retirement.py` | tests | 3271 | 83 | `e0b25faf06f6` |  |
| `services/harness/tests/test_agent_automation_otel_resource_identity.py` | tests | 1344 | 40 | `3743a2be2b3d` |  |
| `services/harness/tests/test_agent_automation_reconcile_surface.py` | tests | 5860 | 152 | `56f6be43996b` |  |
| `services/harness/tests/test_agent_automation_registry.py` | tests | 4757 | 118 | `d3a82b7cbedc` |  |
| `services/harness/tests/test_agent_automation_release.py` | tests | 55269 | 1148 | `a9e7a0055e56` |  |
| `services/harness/tests/test_agent_automation_release_monorepo.py` | tests | 8634 | 219 | `49b94996c911` |  |
| `services/harness/tests/test_agent_automation_turn_receipt_jcs.py` | tests | 677 | 18 | `fd961a2e4467` |  |
| `services/harness/tests/test_agent_automation_write_authority.py` | tests | 5159 | 124 | `bbe42b1d64e4` |  |
| `services/harness/tests/test_agent_plugin_composition.py` | tests | 9525 | 238 | `1fcaeb6e387c` |  |
| `services/harness/tests/test_agent_plugin_harness_run.py` | tests | 8538 | 251 | `6189a49455ba` |  |
| `services/harness/tests/test_browser_ax_projection_v1.py` | tests | 14943 | 488 | `2a2b5ab3dcb6` |  |
| `services/harness/tests/test_browser_benchmark_contract.py` | tests | 10150 | 239 | `57884ae7b978` |  |
| `services/harness/tests/test_browser_benchmark_prospective.py` | tests | 8193 | 209 | `e9ceb5ce3417` |  |
| `services/harness/tests/test_browser_benchmark_route_adapter.py` | tests | 10741 | 271 | `469643c4b587` |  |
| `services/harness/tests/test_browser_benchmark_runner.py` | tests | 7000 | 151 | `c29c41402696` |  |
| `services/harness/tests/test_browser_benchmark_runtime_handoff.py` | tests | 13281 | 305 | `c070eb348df4` |  |
| `services/harness/tests/test_browser_capability_router.py` | tests | 19073 | 462 | `3662f67cc7af` |  |
| `services/harness/tests/test_browser_decision_corpus_r1.py` | tests | 2166 | 52 | `0d1757682cd2` |  |
| `services/harness/tests/test_browser_decision_duel_analysis_r1.py` | tests | 1935 | 41 | `846806c97995` |  |
| `services/harness/tests/test_browser_security_browserless_canary.py` | tests | 8963 | 222 | `2339cf8ab4d5` |  |
| `services/harness/tests/test_browser_security_cf07_metadata_r4.py` | tests | 3431 | 87 | `e51c64493375` |  |
| `services/harness/tests/test_browser_security_pool_runner.py` | tests | 16406 | 382 | `dcf5d401a85e` |  |
| `services/harness/tests/test_browser_security_r5.py` | tests | 5929 | 136 | `a1bcdc125bc4` |  |
| `services/harness/tests/test_browser_security_r7.py` | tests | 3504 | 84 | `e7eadf99a51d` |  |
| `services/harness/tests/test_browser_security_r8.py` | tests | 3686 | 83 | `6c3128b3df9f` |  |
| `services/harness/tests/test_browser_security_r9.py` | tests | 3945 | 102 | `35da515e4527` |  |
| `services/harness/tests/test_browser_security_witness_source.py` | tests | 7649 | 177 | `6a5b4323de10` |  |
| `services/harness/tests/test_browser_use_browserless.py` | tests | 12329 | 298 | `f8a4390ace38` |  |
| `services/harness/tests/test_browserless_conversation_output_contract.py` | tests | 2773 | 58 | `59d2eeabd215` |  |
| `services/harness/tests/test_browserless_display_auth.py` | tests | 2508 | 65 | `5067129b658c` |  |
| `services/harness/tests/test_browserless_human_interaction.py` | tests | 1395 | 40 | `4ecfc3ecb945` |  |
| `services/harness/tests/test_browserless_idle_reaper.py` | tests | 8246 | 170 | `97568e3fccb3` |  |
| `services/harness/tests/test_browserless_image_promotion.py` | tests | 25608 | 598 | `184e912808ae` |  |
| `services/harness/tests/test_browserless_materialization_target.py` | tests | 3793 | 99 | `fd2831f2e184` |  |
| `services/harness/tests/test_browserless_pg_required_consumer.py` | tests | 3389 | 89 | `27632376a84f` |  |
| `services/harness/tests/test_browserless_podman_deploy.py` | tests | 15974 | 352 | `86c33be44a3a` |  |
| `services/harness/tests/test_browserless_post_send_route.py` | tests | 2897 | 70 | `d2e878ccd0d6` |  |
| `services/harness/tests/test_browserless_postgres_wake_selection.py` | tests | 5169 | 126 | `e69e913ce3b8` |  |
| `services/harness/tests/test_browserless_provider_preflight.py` | tests | 1531 | 38 | `52079d4124d5` |  |
| `services/harness/tests/test_browserless_sqlite_connection_lifetime.py` | tests | 2123 | 62 | `c643197db44f` |  |
| `services/harness/tests/test_browserless_submit_clean_surface.py` | tests | 5939 | 172 | `c59778fc567f` |  |
| `services/harness/tests/test_browserless_submit_no_human_session.py` | tests | 2144 | 66 | `7be2f3fd2e54` |  |
| `services/harness/tests/test_browserless_substrate.py` | tests | 10352 | 221 | `242f57dda9ed` |  |
| `services/harness/tests/test_campaign_census_freshness.py` | tests | 4352 | 102 | `de134c926e5f` |  |
| `services/harness/tests/test_cft_human_session.py` | tests | 2158 | 56 | `bf7edeae909c` |  |
| `services/harness/tests/test_cft_human_session_deploy.py` | tests | 2926 | 80 | `2ca94c96adf3` |  |
| `services/harness/tests/test_cft_human_session_durable.py` | tests | 11281 | 297 | `510f921a3574` |  |
| `services/harness/tests/test_chatgpt_conversation_discovery.py` | tests | 5212 | 157 | `7bdf19085a9a` |  |
| `services/harness/tests/test_cli_currentness.py` | tests | 4134 | 103 | `d359d140d7b1` |  |
| `services/harness/tests/test_codex_app_h3_receipt.py` | tests | 2476 | 61 | `e8841c827353` |  |
| `services/harness/tests/test_conclusion_correction_separation.py` | tests | 7024 | 165 | `97cf6b7b9c6f` |  |
| `services/harness/tests/test_configure_deepseek_api.py` | tests | 4454 | 101 | `0778f9849555` |  |
| `services/harness/tests/test_conversation_adopt.py` | tests | 7687 | 209 | `e9d0160e80a1` |  |
| `services/harness/tests/test_conversation_affinity.py` | tests | 7567 | 209 | `629a3c1d27a7` |  |
| `services/harness/tests/test_conversation_binding_pg_selection.py` | tests | 6886 | 178 | `cd7a7a9ba0c6` |  |
| `services/harness/tests/test_conversation_continue_first.py` | tests | 7856 | 213 | `1ed03eac946b` |  |
| `services/harness/tests/test_conversation_continue_transport.py` | tests | 4233 | 120 | `50f0d06ad35f` |  |
| `services/harness/tests/test_current_no_tool_conclusion_control_regression.py` | tests | 22990 | 502 | `4c596a087ed0` |  |
| `services/harness/tests/test_dap_provider_port.py` | tests | 6819 | 195 | `51a968a6078f` |  |
| `services/harness/tests/test_deepseek_httpx_transport.py` | tests | 8326 | 228 | `2901dfe19bfd` |  |
| `services/harness/tests/test_deepseek_loopback_proxy.py` | tests | 4790 | 143 | `28dd407f1efa` |  |
| `services/harness/tests/test_deepseek_mixed_turn.py` | tests | 10925 | 296 | `49b52d1ef712` |  |
| `services/harness/tests/test_deepseek_terminal_state_contract.py` | tests | 2719 | 79 | `b5283e7a27b7` |  |
| `services/harness/tests/test_domain_tool_bridge.py` | tests | 6392 | 187 | `57ff00738564` |  |
| `services/harness/tests/test_durable_human_control_api.py` | tests | 5669 | 149 | `694da892a4ab` |  |
| `services/harness/tests/test_durable_human_materialization.py` | tests | 10304 | 258 | `93770a6e638e` |  |
| `services/harness/tests/test_durable_human_temporal_wait.py` | tests | 2644 | 67 | `73a910342677` |  |
| `services/harness/tests/test_eval_harness_document_retirement_004.py` | tests | 6569 | 158 | `7fdd0afbab7d` |  |
| `services/harness/tests/test_eval_harness_edit_addressing_002.py` | tests | 1649 | 41 | `3fd762c597e6` |  |
| `services/harness/tests/test_eval_harness_edit_multiregion_003.py` | tests | 1771 | 42 | `cf2369c6f45d` |  |
| `services/harness/tests/test_eval_harness_repository_repair_001.py` | tests | 2145 | 51 | `617c01023f7d` |  |
| `services/harness/tests/test_evidence_index_typed_ingestion.py` | tests | 32053 | 715 | `5330f93821b0` |  |
| `services/harness/tests/test_finance_current_state_application.py` | tests | 11035 | 263 | `c2bbccc11607` |  |
| `services/harness/tests/test_finance_owner_uv_selection_contract.py` | tests | 2280 | 58 | `4e0a432bc588` |  |
| `services/harness/tests/test_finance_readonly_observation.py` | tests | 14664 | 360 | `a2c725fa9eeb` |  |
| `services/harness/tests/test_gateway_execution_port.py` | tests | 13406 | 332 | `de0ff8fb0ea1` |  |
| `services/harness/tests/test_h0_deliberation_authority.py` | tests | 2348 | 61 | `018b60bf539d` |  |
| `services/harness/tests/test_harness_otel_event_sink.py` | tests | 12887 | 345 | `acd7b9aa9d40` |  |
| `services/harness/tests/test_harness_replacement_h5.py` | tests | 5889 | 140 | `cddb1b12df9b` |  |
| `services/harness/tests/test_harness_replacement_h5_receipt.py` | tests | 4946 | 110 | `e7bc2de08ed6` |  |
| `services/harness/tests/test_hermes_acp_h4_receipt.py` | tests | 3026 | 71 | `848dda7beadd` |  |
| `services/harness/tests/test_independent_proposal_claim_binding.py` | tests | 7066 | 175 | `93dbe2fa1962` |  |
| `services/harness/tests/test_independent_receipt_type_refinement.py` | tests | 5134 | 137 | `6c91b6ac4b94` |  |
| `services/harness/tests/test_jev_fastpath_adapter.py` | tests | 12183 | 365 | `df33dbfe881b` |  |
| `services/harness/tests/test_lsp_provider_port.py` | tests | 5028 | 145 | `e57bc1d9993c` |  |
| `services/harness/tests/test_lsp_workspace_edit.py` | tests | 9747 | 257 | `0537caf70ea1` |  |
| `services/harness/tests/test_materialization_reconciliation_archive.py` | tests | 5617 | 158 | `b33f0ad996e2` |  |
| `services/harness/tests/test_mcp_http_client.py` | tests | 3520 | 94 | `844d2f1fb86f` |  |
| `services/harness/tests/test_mcp_python315_release_contract.py` | tests | 1982 | 44 | `20b27f19cb20` |  |
| `services/harness/tests/test_observation_gate_and_port.py` | tests | 1846 | 52 | `3b59e1e400c2` |  |
| `services/harness/tests/test_owner_environment_doctor_contract.py` | tests | 5635 | 146 | `3dddece82d12` |  |
| `services/harness/tests/test_p0_composition_projection.py` | tests | 2597 | 67 | `0378ec3f75bf` |  |
| `services/harness/tests/test_p0_continuity_records.py` | tests | 10753 | 267 | `03be3cd74e13` |  |
| `services/harness/tests/test_p0_core_contracts.py` | tests | 8391 | 206 | `1b5ddaa9e2ec` |  |
| `services/harness/tests/test_p0_core_package_boundary.py` | tests | 10934 | 235 | `a6caed0cc5d4` |  |
| `services/harness/tests/test_p0_execution_binding.py` | tests | 15679 | 382 | `dea7acf014fa` |  |
| `services/harness/tests/test_p0_run_store_port.py` | tests | 2465 | 65 | `1b39c9945924` |  |
| `services/harness/tests/test_p0_scale_acceptance.py` | tests | 1585 | 43 | `af2301c7228d` |  |
| `services/harness/tests/test_p0_sqlite_agent_loop.py` | tests | 19545 | 492 | `05b21d2a0074` |  |
| `services/harness/tests/test_p0_sqlite_provider_store.py` | tests | 22457 | 530 | `2131c766c0f0` |  |
| `services/harness/tests/test_p0_sqlite_runtime_bridge.py` | tests | 43175 | 1043 | `ce5d7573bdd5` |  |
| `services/harness/tests/test_p0_sqlite_store.py` | tests | 26570 | 595 | `696d436b7e33` |  |
| `services/harness/tests/test_p0_sqlite_tool_store.py` | tests | 18340 | 408 | `b3c975b521a0` |  |
| `services/harness/tests/test_p0_standalone_runner.py` | tests | 24173 | 567 | `835c85dfc4bd` |  |
| `services/harness/tests/test_p1_procedural_capital.py` | tests | 6160 | 158 | `f988122d96ee` |  |
| `services/harness/tests/test_p2_tool_program.py` | tests | 17054 | 410 | `38fe398821d8` |  |
| `services/harness/tests/test_p2_tool_program_provider_loop.py` | tests | 9832 | 251 | `400fa5bd26ac` |  |
| `services/harness/tests/test_p2_tool_program_recovery.py` | tests | 10625 | 241 | `1d767579d4a4` |  |
| `services/harness/tests/test_pc110_caller_cognition_ingress.py` | tests | 36843 | 886 | `6bcf0b1c9177` |  |
| `services/harness/tests/test_pc111_interaction_durable_promotion.py` | tests | 42257 | 1014 | `2fa43ff2f617` |  |
| `services/harness/tests/test_pc112_durable_cognition_supersession.py` | tests | 16731 | 376 | `8e7ba4ab10e6` |  |
| `services/harness/tests/test_pc12_privacy_authority.py` | tests | 16890 | 408 | `08384826577a` |  |
| `services/harness/tests/test_pc12b_multiturn_projection.py` | tests | 19285 | 449 | `0173ba70dc78` |  |
| `services/harness/tests/test_pc13_agent_owned_working_set.py` | tests | 38368 | 881 | `734ce79e3dc0` |  |
| `services/harness/tests/test_pc14_candidate_discovery_overlay.py` | tests | 42165 | 952 | `c5ce0cb181e2` |  |
| `services/harness/tests/test_pc15_epistemic_control.py` | tests | 17528 | 477 | `dfe2e6135efb` |  |
| `services/harness/tests/test_pc16_cross_process_tool_exchange.py` | tests | 22142 | 501 | `dc96e7dc915e` |  |
| `services/harness/tests/test_pc17_durable_knowledge_promotion.py` | tests | 27528 | 622 | `a6f6327ee2d2` |  |
| `services/harness/tests/test_pc18_historical_cognition_recall.py` | tests | 26130 | 605 | `ec90fd058273` |  |
| `services/harness/tests/test_pc19_cognition_transition_progress.py` | tests | 27677 | 697 | `1d77b875bac7` |  |
| `services/harness/tests/test_pc1_working_view.py` | tests | 19936 | 427 | `c6b9859a8056` |  |
| `services/harness/tests/test_pg_binding_cutover_formal_gate.py` | tests | 1603 | 41 | `2f4940a503f2` |  |
| `services/harness/tests/test_plugin_gateway_effect.py` | tests | 28284 | 704 | `0f09d33b1ff7` |  |
| `services/harness/tests/test_postgres_cli.py` | tests | 4415 | 105 | `9549433bdd83` |  |
| `services/harness/tests/test_postgres_conversation_binding.py` | tests | 15819 | 373 | `2fabdf2c18ce` |  |
| `services/harness/tests/test_postgres_harness_store.py` | tests | 18747 | 363 | `39e3cff3510c` |  |
| `services/harness/tests/test_postgres_turn_effects.py` | tests | 21331 | 493 | `a5c0cbef77ca` |  |
| `services/harness/tests/test_postgres_wake_turn_map.py` | tests | 26069 | 640 | `2fa545397d71` |  |
| `services/harness/tests/test_provider_boundary_diagnosis.py` | tests | 5558 | 107 | `0dd2acb1fcfc` |  |
| `services/harness/tests/test_provider_call_protocol.py` | tests | 19142 | 479 | `d0d9dd22df01` |  |
| `services/harness/tests/test_provider_claim_formal_gate.py` | tests | 1548 | 39 | `6e257772f00d` |  |
| `services/harness/tests/test_provider_effect_policy_convergence.py` | tests | 3427 | 91 | `e11f2c1f89b5` |  |
| `services/harness/tests/test_provider_recovery_signal_fence_p1.py` | tests | 4393 | 117 | `97e07f679357` |  |
| `services/harness/tests/test_public_api.py` | tests | 6560 | 180 | `9beb7606073c` |  |
| `services/harness/tests/test_r0_cognition_product_composition.py` | tests | 19212 | 448 | `3184a1948502` |  |
| `services/harness/tests/test_r1_single_capability_truth.py` | tests | 9951 | 252 | `0c3e416621d3` |  |
| `services/harness/tests/test_r2_cognition_admission_kernel.py` | tests | 5425 | 142 | `4f88e32c65ac` |  |
| `services/harness/tests/test_r2_provider_lifecycle_port.py` | tests | 9665 | 240 | `7f0fec7b349a` |  |
| `services/harness/tests/test_r2_turn_projection_kernel.py` | tests | 11253 | 254 | `9ee60d5942d3` |  |
| `services/harness/tests/test_r3_supported_agent_run.py` | tests | 22091 | 583 | `3c86e9c91532` |  |
| `services/harness/tests/test_repository_boundary.py` | tests | 6124 | 129 | `db9191045756` |  |
| `services/harness/tests/test_repository_repair_edit_runtime_receipt.py` | tests | 5785 | 143 | `b83fe851fd5d` |  |
| `services/harness/tests/test_research_fresh_agent_corpus_r1.py` | tests | 6292 | 156 | `5544f6a138ff` |  |
| `services/harness/tests/test_research_owner_publication.py` | tests | 5792 | 117 | `ecc68720e523` |  |
| `services/harness/tests/test_runtime_python_compatibility_currentness.py` | tests | 4045 | 100 | `bfd920dbb2c3` |  |
| `services/harness/tests/test_runtime_task_cursor_refinement_cegar.py` | tests | 3875 | 106 | `5914e6905144` |  |
| `services/harness/tests/test_search_workspace_batch.py` | tests | 20900 | 474 | `86f9712e38bd` |  |
| `services/harness/tests/test_security_owner_locator.py` | tests | 4345 | 87 | `a2f314237fe5` |  |
| `services/harness/tests/test_sqlite_connection_context_law.py` | tests | 1383 | 36 | `4232862c163c` |  |
| `services/harness/tests/test_sqlite_conversation_binding.py` | tests | 6835 | 180 | `b36d021bf0ca` |  |
| `services/harness/tests/test_sqlite_materializer_transaction_guard.py` | tests | 6542 | 156 | `236d78c15c0d` |  |
| `services/harness/tests/test_sqlite_wake_turn_map.py` | tests | 6206 | 176 | `b60eb164fd2e` |  |
| `services/harness/tests/test_structured_completion.py` | tests | 12801 | 319 | `64fb4393ae16` |  |
| `services/harness/tests/test_structured_no_progress_completion.py` | tests | 7040 | 179 | `afd9ea8c7485` |  |
| `services/harness/tests/test_structured_result_carrier.py` | tests | 5557 | 140 | `b9011c0a9e66` |  |
| `services/harness/tests/test_structured_result_conformance.py` | tests | 14606 | 357 | `539032f6cf6f` |  |
| `services/harness/tests/test_system1_decision_benchmark.py` | tests | 11980 | 320 | `8d22fb9d3990` |  |
| `services/harness/tests/test_temporal_agent_automation_contract.py` | tests | 11929 | 279 | `ccc66d2caa9d` |  |
| `services/harness/tests/test_temporal_agent_automation_deploy.py` | tests | 7095 | 146 | `38a295c476ea` |  |
| `services/harness/tests/test_temporal_latest_runtime_contract.py` | tests | 3159 | 77 | `2131a1f42bd8` |  |
| `services/harness/tests/test_tool_observation_evidence_seal.py` | tests | 6906 | 158 | `6faa2cd35412` |  |
| `services/harness/tests/test_trace_type_refinement.py` | tests | 4104 | 98 | `eac98a4ac371` |  |
| `services/harness/tests/test_turn_evidence_transition.py` | tests | 3521 | 116 | `b8989e497ec0` |  |
| `services/harness/tests/test_user_browser_gateway_controller.py` | tests | 5877 | 155 | `66519c9b4780` |  |
| `services/harness/tests/test_user_browser_gateway_receipt_ambiguity.py` | tests | 3153 | 93 | `691ba23c9a3a` |  |
| `services/harness/tests/test_wheel_public_api_contract.py` | tests | 4364 | 113 | `8d4fef48897f` |  |
| `services/harness/tests/test_wheel_python_baseline.py` | tests | 1151 | 33 | `2624dd4eb712` |  |
| `services/harness/tests/test_windows_user_browser_materialization_target.py` | tests | 5226 | 124 | `16d03a3c404c` |  |
| `services/harness/uv.lock` | config | 98191 | — | `f7b778997f0c` |  |

### gateway — services/gateway/（107 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `services/gateway/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `services/gateway/AGENTS.md` | docs | 11268 | 194 | `b31c89d8e95b` |  |
| `services/gateway/README.md` | docs | 27521 | 428 | `c37e559f7521` |  |
| `services/gateway/enforcement-surface.json` | config | 8726 | 311 | `c05ab5ee41dd` | 1 |
| `services/gateway/formal/GatewayCapabilityAuthzR1.cfg` | config | 194 | 7 | `b259b80d2c16` |  |
| `services/gateway/formal/GatewayCapabilityAuthzR1.reachability.cfg` | config | 69 | 3 | `6edd2bd8b1c6` |  |
| `services/gateway/formal/GatewayCapabilityAuthzR1.tla` | core | 4358 | 149 | `b6c87584995f` |  |
| `services/gateway/formal/GatewayCapabilityAuthzR1.unsafe.cfg` | config | 78 | 3 | `0f54ab81b2d7` |  |
| `services/gateway/formal/GatewayOwnerObservationR1.cfg` | config | 101 | 4 | `f8e1c1b5d931` |  |
| `services/gateway/formal/GatewayOwnerObservationR1.reachability.cfg` | config | 44 | 2 | `76d8509536ab` |  |
| `services/gateway/formal/GatewayOwnerObservationR1.tla` | core | 2610 | 85 | `470149d5fe16` |  |
| `services/gateway/formal/GatewayOwnerObservationR1.unsafe.cfg` | config | 51 | 2 | `bfd80e181d97` |  |
| `services/gateway/formal/GatewayRoutingR1.cfg` | config | 222 | 8 | `411a13f97607` |  |
| `services/gateway/formal/GatewayRoutingR1.reachability.cfg` | config | 159 | 6 | `5c82104143ca` |  |
| `services/gateway/formal/GatewayRoutingR1.tla` | core | 2793 | 86 | `33000cb49e51` |  |
| `services/gateway/formal/GatewayRoutingR1.unsafe.cfg` | config | 179 | 6 | `af14b296a987` |  |
| `services/gateway/formal/check_owner_status_contract.py` | core | 3847 | 115 | `c74e5f084a29` |  |
| `services/gateway/formal/check_routing_conformance.py` | core | 4114 | 118 | `ee85c474b277` |  |
| `services/gateway/formal/evidence/GatewayOwnerObservationR1-20261108.json` | evidence | 1932 | 48 | `df6482c9345d` | 1 |
| `services/gateway/formal/evidence/GatewayOwnerRPCPhase-20261108.json` | evidence | 1791 | 52 | `c4650ddeea56` | 1 |
| `services/gateway/formal/evidence/GatewayRoutingR1-20261107.json` | evidence | 1657 | 51 | `d92da5daff95` | 1 |
| `services/gateway/formal/evidence/GatewayVerification-20261108.json` | evidence | 3104 | 94 | `edbd234aed11` | 1 |
| `services/gateway/mcp-surface.json` | config | 1137 | 48 | `bd6f05318cc6` | 1 |
| `services/gateway/packaging/enable_local_service_identity.sh` | core | 1036 | 30 | `e882c60fe96e` |  |
| `services/gateway/packaging/enable_trace_export.sh` | core | 935 | 29 | `47363c74bade` |  |
| `services/gateway/packaging/enable_windows_service_identity.sh` | core | 1542 | 45 | `294734cea74f` |  |
| `services/gateway/packaging/install_release.sh` | core | 4099 | 114 | `e6c256e75feb` |  |
| `services/gateway/packaging/verify_tool_surface.py` | core | 3816 | 89 | `613541b882cb` |  |
| `services/gateway/packaging/windows/activate_service.ps1` | core | 7648 | 175 | `e83e7cf57697` |  |
| `services/gateway/packaging/windows/install_release.ps1` | core | 10768 | 296 | `e521bc5e0ac2` |  |
| `services/gateway/packaging/windows/materialize_credentials.ps1` | core | 8463 | 247 | `7e18352a377e` |  |
| `services/gateway/packaging/windows/materialize_service.ps1` | core | 13961 | 324 | `1ccf973b23e2` |  |
| `services/gateway/packaging/windows/probe_candidate.py` | core | 1419 | 39 | `03f6ae195bd5` |  |
| `services/gateway/packaging/windows/protect_candidate_acl.ps1` | core | 4921 | 143 | `a90bec1ce971` |  |
| `services/gateway/packaging/windows/verify_release.py` | core | 2548 | 68 | `bad24294dacc` |  |
| `services/gateway/planning/GATEWAY_WINDOWS_CANDIDATE_CARRIER_EVIDENCE_R1.json` | config | 1225 | 39 | `0d1859f24d61` | 1 |
| `services/gateway/planning/GATEWAY_WINDOWS_R2_CRASH_HOST_READBACK_EVIDENCE.json` | config | 1522 | 42 | `ee892dfc630d` | 1 |
| `services/gateway/planning/GATEWAY_WINDOWS_RELEASE_EVIDENCE_R1.json` | config | 1032 | 25 | `e80f9932dab8` | 1 |
| `services/gateway/planning/GATEWAY_WINDOWS_SERVICE_CARRIER_EVIDENCE_R1.json` | config | 1076 | 31 | `e855e62a3794` | 1 |
| `services/gateway/planning/GATEWAY_WINDOWS_TOOLCHAIN_EVIDENCE_R1.json` | config | 1214 | 27 | `d2778738e555` | 1 |
| `services/gateway/planning/lego-plan-r1.json` | config | 24486 | 540 | `64589454db87` | 1 |
| `services/gateway/planning/lego-plan-windows-carrier-r2.json` | config | 22729 | 692 | `13487fda3efb` | 1 |
| `services/gateway/pyproject.toml` | config | 878 | 41 | `ab93e180f23c` |  |
| `services/gateway/src/ordivon_gateway/__init__.py` | core | 145 | 5 | `47c4a4295c65` |  |
| `services/gateway/src/ordivon_gateway/access_auth.py` | core | 7554 | 205 | `ef1d8cdb56d3` |  |
| `services/gateway/src/ordivon_gateway/audit.py` | core | 3923 | 112 | `a0931a98c5e1` |  |
| `services/gateway/src/ordivon_gateway/authzen_authorizer.py` | core | 6061 | 161 | `4f07f045c37f` |  |
| `services/gateway/src/ordivon_gateway/capability_authz.py` | core | 12774 | 339 | `241bb2dc94e7` |  |
| `services/gateway/src/ordivon_gateway/capability_catalog.py` | core | 16218 | 386 | `b2160632d09d` |  |
| `services/gateway/src/ordivon_gateway/capability_projection.py` | core | 8699 | 246 | `a7c1271d0160` |  |
| `services/gateway/src/ordivon_gateway/contracts.py` | core | 6112 | 181 | `978914e01843` |  |
| `services/gateway/src/ordivon_gateway/execution_commands.py` | core | 5456 | 129 | `4071cba1afa9` |  |
| `services/gateway/src/ordivon_gateway/execution_coordinator.py` | core | 684 | 20 | `4f2efa378577` |  |
| `services/gateway/src/ordivon_gateway/execution_observations.py` | core | 9402 | 231 | `b9f76ffb55d4` |  |
| `services/gateway/src/ordivon_gateway/execution_refs.py` | core | 987 | 29 | `cb5b56488d84` |  |
| `services/gateway/src/ordivon_gateway/host_attention_tools.py` | core | 3397 | 105 | `8111a950f7d9` |  |
| `services/gateway/src/ordivon_gateway/host_social_tools.py` | core | 8748 | 281 | `fb3e177884a9` |  |
| `services/gateway/src/ordivon_gateway/host_tool_contracts.py` | core | 282 | 10 | `d709af0789ff` |  |
| `services/gateway/src/ordivon_gateway/host_tools.py` | core | 1030 | 28 | `724042e2a9cf` |  |
| `services/gateway/src/ordivon_gateway/host_work_tools.py` | core | 2795 | 84 | `4efaf4fd67e7` |  |
| `services/gateway/src/ordivon_gateway/http_ingress_guard.py` | core | 2488 | 61 | `320ed8382a6a` |  |
| `services/gateway/src/ordivon_gateway/mcp_server.py` | core | 17837 | 489 | `562124bf876a` |  |
| `services/gateway/src/ordivon_gateway/owner_protocol.py` | core | 1111 | 36 | `fcc90cdd9754` |  |
| `services/gateway/src/ordivon_gateway/research_resolution.py` | core | 5901 | 137 | `5fe0ba500b59` |  |
| `services/gateway/src/ordivon_gateway/research_routes.py` | core | 18737 | 424 | `0fd7bec5f994` |  |
| `services/gateway/src/ordivon_gateway/routing.py` | core | 3172 | 82 | `b46558e5f5e1` |  |
| `services/gateway/src/ordivon_gateway/service.py` | core | 6133 | 183 | `2f3ca05d894b` |  |
| `services/gateway/src/ordivon_gateway/upstream.py` | core | 18332 | 426 | `7e2695cfe65d` |  |
| `services/gateway/src/ordivon_gateway/upstream_identity.py` | core | 7226 | 184 | `299d26a95881` |  |
| `services/gateway/systemd/ordivon-gateway.service` | config | 1542 | 46 | `2f522bb6566c` |  |
| `services/gateway/systemd/ordivon-gateway.service.d/10-local-service-identity.example.conf` | config | 241 | 4 | `5d34d8c55369` |  |
| `services/gateway/systemd/ordivon-gateway.service.d/20-public-access.example.conf` | config | 491 | 7 | `799f83336c91` |  |
| `services/gateway/systemd/ordivon-gateway.service.d/30-windows-service-identity.example.conf` | config | 592 | 8 | `de2232b04577` |  |
| `services/gateway/systemd/ordivon-gateway.service.d/35-skills-owner.example.conf` | config | 290 | 8 | `8e8d46e9e9d6` |  |
| `services/gateway/systemd/ordivon-gateway.service.d/40-otel-traces.example.conf` | config | 377 | 7 | `079c230c8848` |  |
| `services/gateway/tests/test_access_auth.py` | tests | 5734 | 174 | `13058bdfdc17` |  |
| `services/gateway/tests/test_audit.py` | tests | 3345 | 86 | `5ce9e8479475` |  |
| `services/gateway/tests/test_authzen_authorizer.py` | tests | 9033 | 249 | `5a45e22b7342` |  |
| `services/gateway/tests/test_capability_authz_middleware.py` | tests | 17727 | 465 | `26d8a5087441` |  |
| `services/gateway/tests/test_capability_projection.py` | tests | 17039 | 457 | `8ff1f9296227` |  |
| `services/gateway/tests/test_capability_readiness_state.py` | tests | 4230 | 109 | `141affc61caa` |  |
| `services/gateway/tests/test_execution_principal_request_namespace.py` | tests | 12808 | 331 | `7c39be5cfdb6` |  |
| `services/gateway/tests/test_gateway_service.py` | tests | 28362 | 769 | `bb459518e58c` |  |
| `services/gateway/tests/test_host_byte_budget_tool_contract.py` | tests | 2618 | 71 | `54a9945568cc` |  |
| `services/gateway/tests/test_http_ingress_coverage.py` | tests | 7434 | 197 | `7759540b698a` |  |
| `services/gateway/tests/test_latest_runtime_release_carrier.py` | tests | 1593 | 48 | `d39e0b4c8e6b` |  |
| `services/gateway/tests/test_linux_pg_business_sdk_bridge.py` | tests | 7772 | 210 | `84954eb92c4d` |  |
| `services/gateway/tests/test_live_epoch5_runtime_currentness.py` | tests | 2537 | 76 | `94ced928943c` |  |
| `services/gateway/tests/test_live_streamable_http_ingress.py` | tests | 3713 | 101 | `9efb7566c23c` |  |
| `services/gateway/tests/test_owner_http_pool.py` | tests | 3800 | 106 | `2c5a74cf9c4b` |  |
| `services/gateway/tests/test_owner_mcp_protocol_mode.py` | tests | 10887 | 300 | `9c3a9f80e617` |  |
| `services/gateway/tests/test_pg_real_runtime_owner.py` | tests | 14812 | 387 | `c4229b810373` |  |
| `services/gateway/tests/test_projection_concurrency.py` | tests | 12299 | 325 | `c64757a15843` |  |
| `services/gateway/tests/test_research_capability_resolution.py` | tests | 10837 | 252 | `52b686668f97` |  |
| `services/gateway/tests/test_search_observation_isolation.py` | tests | 7213 | 183 | `e799a88cba5f` |  |
| `services/gateway/tests/test_skills_owner_optin.py` | tests | 2621 | 59 | `20f727624566` |  |
| `services/gateway/tests/test_systemd_contract.py` | tests | 8084 | 177 | `4f454203e921` |  |
| `services/gateway/tests/test_tool_surface_release_contract.py` | tests | 5712 | 144 | `db9d5853b8a5` |  |
| `services/gateway/tests/test_upstream_identity.py` | tests | 11740 | 333 | `746f764d25c9` |  |
| `services/gateway/tests/test_windows_acl_preflight.py` | tests | 1942 | 54 | `4ce7d4d88d64` |  |
| `services/gateway/tests/test_windows_activation_contract.py` | tests | 2623 | 58 | `697de2d5144b` |  |
| `services/gateway/tests/test_windows_credential_contract.py` | tests | 2035 | 48 | `bd117e17bd01` |  |
| `services/gateway/tests/test_windows_local_identity.py` | tests | 4073 | 106 | `800fbcef851d` |  |
| `services/gateway/tests/test_windows_release_contract.py` | tests | 2884 | 67 | `988782a318f1` |  |
| `services/gateway/tests/test_windows_runtime_typed_status_read.py` | tests | 6835 | 183 | `61b259ba8d55` |  |
| `services/gateway/tests/test_windows_service_contract.py` | tests | 6462 | 138 | `8d1798c01389` |  |
| `services/gateway/uv.lock` | config | 105298 | — | `6416a5a98524` |  |

### skills — extensions/chatgpt-skills-mcp/（45 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `extensions/chatgpt-skills-mcp/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `extensions/chatgpt-skills-mcp/README.md` | docs | 1536 | 30 | `a4e4b0732807` |  |
| `extensions/chatgpt-skills-mcp/config/skills-mcp-requirements.txt` | other | 63 | 4 | `c465bcf3c621` |  |
| `extensions/chatgpt-skills-mcp/config/skills-mcp.example.json` | config | 772 | 36 | `f66f07e6ca1e` | 2 |
| `extensions/chatgpt-skills-mcp/docs/SKILL_MCP_STANDARDS_ALIGNMENT.md` | docs | 11067 | 121 | `94c8cf022dc3` |  |
| `extensions/chatgpt-skills-mcp/docs/chatgpt-skills-mcp-registration.md` | docs | 3269 | 36 | `cad53a4d1301` |  |
| `extensions/chatgpt-skills-mcp/docs/skills-standards-alignment.md` | docs | 6061 | 77 | `247c554c3c73` |  |
| `extensions/chatgpt-skills-mcp/mise.toml` | config | 785 | 30 | `2ce7c2bf27e0` |  |
| `extensions/chatgpt-skills-mcp/planning/lego-plan-r1.json` | config | 16145 | 453 | `f80123c98136` | 1 |
| `extensions/chatgpt-skills-mcp/plugins/ordivon-skills-bridge/mcp.json` | config | 203 | 9 | `4f19c760a9b6` |  |
| `extensions/chatgpt-skills-mcp/plugins/ordivon-skills-bridge/plugin.json` | config | 312 | 7 | `af9950359e60` |  |
| `extensions/chatgpt-skills-mcp/pyproject.toml` | config | 798 | 42 | `3355ca260510` |  |
| `extensions/chatgpt-skills-mcp/scripts/cloudflare_skill_route.py` | core | 10298 | 259 | `c3c13fff512c` |  |
| `extensions/chatgpt-skills-mcp/scripts/skills_mcp.py` | core | 29582 | 692 | `85a09948f335` |  |
| `extensions/chatgpt-skills-mcp/scripts/skills_mcp_consumer_readiness.py` | core | 7921 | 217 | `afa275c4c5de` |  |
| `extensions/chatgpt-skills-mcp/src/ordivon_skills/__init__.py` | core | 585 | 33 | `0de19f033858` |  |
| `extensions/chatgpt-skills-mcp/src/ordivon_skills/catalog.py` | core | 31651 | 750 | `9fc3576cf1f8` |  |
| `extensions/chatgpt-skills-mcp/src/ordivon_skills/config.py` | core | 8522 | 222 | `bce2698cb5d1` |  |
| `extensions/chatgpt-skills-mcp/src/ordivon_skills/eligibility.py` | core | 3359 | 98 | `3ad7801e5037` |  |
| `extensions/chatgpt-skills-mcp/src/ordivon_skills/http_auth.py` | core | 5034 | 133 | `ca0f034620d2` |  |
| `extensions/chatgpt-skills-mcp/src/ordivon_skills/model.py` | core | 6416 | 180 | `5f2bce74c7e5` |  |
| `extensions/chatgpt-skills-mcp/src/ordivon_skills/parser.py` | core | 8016 | 196 | `5400a6fa2d57` |  |
| `extensions/chatgpt-skills-mcp/src/ordivon_skills/scanner.py` | core | 10954 | 268 | `13318d7bb28b` |  |
| `extensions/chatgpt-skills-mcp/src/ordivon_skills/sep2640.py` | core | 10249 | 240 | `b96ee4a99e21` |  |
| `extensions/chatgpt-skills-mcp/systemd/ordivon-skills-mcp.service` | config | 1216 | 37 | `fe922776e223` |  |
| `extensions/chatgpt-skills-mcp/tests/fixtures/agent-plugins-1.0.0/PROVENANCE.json` | tests | 483 | 14 | `00fce24c0096` |  |
| `extensions/chatgpt-skills-mcp/tests/fixtures/agent-plugins-1.0.0/mcp.schema.json` | tests | 3408 | 120 | `6539175bfcdf` |  |
| `extensions/chatgpt-skills-mcp/tests/fixtures/agent-plugins-1.0.0/plugin.schema.json` | tests | 1805 | 65 | `0a4aad95ce33` |  |
| `extensions/chatgpt-skills-mcp/tests/test_agent_plugins_conformance.py` | tests | 1938 | 43 | `1dd8a7c352fc` |  |
| `extensions/chatgpt-skills-mcp/tests/test_method_router_skill.py` | tests | 8517 | 205 | `cea8477dee0a` |  |
| `extensions/chatgpt-skills-mcp/tests/test_native_thinking_skill_discovery.py` | tests | 3756 | 88 | `774052801fc4` |  |
| `extensions/chatgpt-skills-mcp/tests/test_owner_boundary.py` | tests | 2291 | 56 | `29986af6201a` |  |
| `extensions/chatgpt-skills-mcp/tests/test_recursive_lego_math_discovery.py` | tests | 2140 | 53 | `40217687400e` |  |
| `extensions/chatgpt-skills-mcp/tests/test_skill_catalog_r2.py` | tests | 41869 | 906 | `ae895bd47683` |  |
| `extensions/chatgpt-skills-mcp/tests/test_skills_mcp_oauth.py` | tests | 6178 | 163 | `603ad746b6a9` |  |
| `extensions/chatgpt-skills-mcp/tests/test_skills_mcp_r2.py` | tests | 21226 | 474 | `6b326f947d6f` |  |
| `extensions/chatgpt-skills-mcp/tests/test_skills_mcp_r3.py` | tests | 18778 | 410 | `4e239be4f892` |  |
| `extensions/chatgpt-skills-mcp/tests/test_skills_sep2640.py` | tests | 26698 | 614 | `7c97d566e963` |  |
| `extensions/chatgpt-skills-mcp/tests/test_source_config_single_valued_r21.py` | tests | 5657 | 148 | `e4818c517ffe` |  |
| `extensions/chatgpt-skills-mcp/tests/test_source_enabled_boolean_r21.py` | tests | 4310 | 123 | `a8e1a93ece93` |  |
| `extensions/chatgpt-skills-mcp/tests/test_source_scope_policy_r21.py` | tests | 2969 | 89 | `df55c98f85c6` |  |
| `extensions/chatgpt-skills-mcp/tests/test_task_space_obligation_handoff.py` | tests | 6159 | 147 | `a4d3d3da49de` |  |
| `extensions/chatgpt-skills-mcp/tests/test_task_space_reentry.py` | tests | 2092 | 49 | `0f3d969dcbff` |  |
| `extensions/chatgpt-skills-mcp/tests/test_task_space_reentry_adversarial_r1.py` | tests | 3595 | 82 | `f47612ef1118` |  |
| `extensions/chatgpt-skills-mcp/uv.lock` | config | 71162 | — | `b485f3f5ad5f` |  |

### security — platform/security/（162 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `platform/security/.clusterfuzzlite/Dockerfile` | other | 159 | — | `bd3fb6abcb29` |  |
| `platform/security/.clusterfuzzlite/build.sh` | core | 511 | 17 | `4ba6f602e622` |  |
| `platform/security/.clusterfuzzlite/project.yaml` | config | 17 | 1 | `c1f351570cf9` |  |
| `platform/security/.gitignore` | other | 64 | — | `f8c81fe051d7` |  |
| `platform/security/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `platform/security/README.md` | docs | 2295 | 30 | `6c31e59901f1` |  |
| `platform/security/artifacts/.gitkeep` | other | 0 | — | `e3b0c44298fc` |  |
| `platform/security/contracts/agent-admission-v1/README.md` | schemas | 2270 | 51 | `e89ebf54b335` |  |
| `platform/security/contracts/agent-admission-v1/evaluate.py` | schemas | 5132 | 147 | `952f14aec5eb` |  |
| `platform/security/contracts/agent-request-verifier-v1/.gitignore` | schemas | 14 | — | `4d56952b0fb1` |  |
| `platform/security/contracts/agent-request-verifier-v1/README.md` | schemas | 2553 | 63 | `34eeed0975e1` |  |
| `platform/security/contracts/agent-request-verifier-v1/RFC7800-KEYCLOAK-INTEROP-ACCEPTANCE-R1.md` | schemas | 3664 | 89 | `245fbfcc74b6` |  |
| `platform/security/contracts/agent-request-verifier-v1/evidence/CNF-EXTENSION-INTEROP-R1.json` | schemas | 1230 | 44 | `114b8f530983` | 1 |
| `platform/security/contracts/agent-request-verifier-v1/package.json` | schemas | 491 | 23 | `cffc9f28e13e` |  |
| `platform/security/contracts/agent-request-verifier-v1/patches/oauth4webapi@3.8.8.patch` | schemas | 981 | — | `30c4fbbcc165` |  |
| `platform/security/contracts/agent-request-verifier-v1/pnpm-lock.yaml` | schemas | 13139 | 410 | `7c9f0e8c8c0b` |  |
| `platform/security/contracts/agent-request-verifier-v1/pnpm-workspace.yaml` | schemas | 95 | 5 | `40b51199ffe1` |  |
| `platform/security/contracts/agent-request-verifier-v1/src/index.ts` | schemas | 3685 | 131 | `2210962ff873` |  |
| `platform/security/contracts/agent-request-verifier-v1/test/cnf-extension-interop.test.ts` | schemas | 5615 | 206 | `ed39ee16ee2f` |  |
| `platform/security/contracts/agent-request-verifier-v1/tsconfig.json` | schemas | 421 | 16 | `0225bc903b67` |  |
| `platform/security/docs/ATTESTATION-MODEL.md` | docs | 2019 | 19 | `18a86fe05e44` |  |
| `platform/security/docs/BROWSER-SECURITY-WITNESS-R1.md` | docs | 13097 | 287 | `d6b850b66a70` |  |
| `platform/security/docs/CONSEQUENCE-VERIFICATION-DIFFERENTIAL.md` | docs | 5013 | 54 | `6f595bc22158` |  |
| `platform/security/docs/CYCLONEDX-VEX-ACCEPTANCE-R1.md` | docs | 3414 | 63 | `cc5b1734c18d` |  |
| `platform/security/docs/DIFFERENTIAL-R1.md` | docs | 5621 | 104 | `41c532d8aae0` |  |
| `platform/security/docs/REMEDIATION-REVERIFY-ACCEPTANCE-R1.md` | docs | 2648 | 52 | `1b357406462e` |  |
| `platform/security/docs/SCOPE-PROFILES.md` | docs | 999 | 25 | `1228888c905e` |  |
| `platform/security/docs/SCORECARD-ACCEPTANCE-R1.md` | docs | 2846 | 53 | `c4d87973179a` |  |
| `platform/security/docs/SIGNED-VSA.md` | docs | 1897 | 36 | `8d3d1ba71a72` |  |
| `platform/security/docs/STANDARDS-BASELINE.md` | docs | 3629 | 58 | `7e05f70d17c5` |  |
| `platform/security/docs/TECHNOLOGY-SELECTION-R2.md` | docs | 11420 | 188 | `c63140665eb3` |  |
| `platform/security/docs/THREAT-MODEL-ACCEPTANCE-R1.md` | docs | 2139 | 34 | `2b4be6b0dbb6` |  |
| `platform/security/docs/VM-PROVIDER-DISPLACEMENT-R1.md` | docs | 5458 | 93 | `45ff6e526c00` |  |
| `platform/security/docs/ZAP-ACTIVE-SCAN-ACCEPTANCE-R1.md` | docs | 4109 | 75 | `1275e9b01b72` |  |
| `platform/security/docs/security-owner-guide.md` | docs | 27094 | 153 | `2f6c2eb40a72` |  |
| `platform/security/fixtures/agent-admission/v0-allow.json` | config | 1303 | 30 | `9e0c6e9813a1` | 1 |
| `platform/security/fixtures/browser-security/harness-r2-live-lkg-carrier11-bundle.json` | config | 5809 | 183 | `a5edb47e6757` | 1 |
| `platform/security/fixtures/browser-security/harness-r2-live-lkg-carrier11-manifest.json` | config | 6635 | 207 | `24ed74939bd9` | 1 |
| `platform/security/fixtures/browser-security/harness-r2-live-lkg-carrier12-bundle.json` | config | 5808 | 183 | `da7b9496da7b` | 1 |
| `platform/security/fixtures/browser-security/harness-r2-live-lkg-carrier12-manifest.json` | config | 6634 | 207 | `083a1f82e816` | 1 |
| `platform/security/fixtures/browser-security/harness-r2-live-lkg-carrier13-bundle.json` | config | 5808 | 183 | `daf798c3b7f8` | 1 |
| `platform/security/fixtures/browser-security/harness-r2-live-lkg-carrier13-manifest.json` | config | 6634 | 207 | `c8ae3904f1ed` | 1 |
| `platform/security/fixtures/browser-security/harness-r2-live-lkg-pool-index.json` | config | 3374 | 67 | `16e7fd965475` | 1 |
| `platform/security/fixtures/browser-security/r2-reference-bundle.json` | config | 6589 | 197 | `55387c0171dd` | 1 |
| `platform/security/fixtures/browser-security/r2-reference-manifest.json` | config | 5642 | 161 | `75a35395fd03` | 1 |
| `platform/security/fixtures/clean/app.py` | core | 63 | 2 | `0049214146c0` |  |
| `platform/security/fixtures/clean/requirements.txt` | other | 16 | 1 | `badbb87d9903` |  |
| `platform/security/fixtures/zap_reflected_xss_server.py` | core | 1460 | 38 | `1f1c1bd37e8e` |  |
| `platform/security/formal/AgentApprovalBinding.lean` | core | 1625 | 45 | `1b29a5473662` |  |
| `platform/security/formal/ConsequenceEvidence.lean` | core | 2268 | 61 | `e90aa483b228` |  |
| `platform/security/formal/EffectAuthorityBinding.lean` | core | 2640 | 65 | `c70ef9653263` |  |
| `platform/security/fuzz/replay_binding_fuzzer.py` | core | 1716 | 57 | `cb051e8191d2` |  |
| `platform/security/labs/agent-admission-rs/.gitignore` | other | 77 | — | `00e4c6baf990` |  |
| `platform/security/labs/agent-admission-rs/KEYCLOAK-OAUTH4WEBAPI-COMPAT.md` | docs | 3916 | 118 | `8e3bb0cff6cb` |  |
| `platform/security/labs/agent-admission-rs/README.md` | docs | 7259 | 199 | `96fb2689d149` |  |
| `platform/security/labs/agent-admission-rs/e2e.sh` | core | 3915 | 119 | `ed336f6e2ddb` |  |
| `platform/security/labs/agent-admission-rs/evidence/AGENT-ADMISSION-E2E-R1.json` | evidence | 3674 | 119 | `d53bbb37f3ad` | 1 |
| `platform/security/labs/agent-admission-rs/evidence/AGENT-ADMISSION-WEBAUTHN-E2E-R1.json` | evidence | 14636 | 372 | `ac600aeca581` | 1 |
| `platform/security/labs/agent-admission-rs/keycloak/realm-agent-admission-lab.json` | config | 1740 | 55 | `ad407890e518` |  |
| `platform/security/labs/agent-admission-rs/package.json` | config | 798 | 31 | `2c959173ccf2` |  |
| `platform/security/labs/agent-admission-rs/patches/oauth4webapi@3.8.8.patch` | other | 981 | — | `30c4fbbcc165` |  |
| `platform/security/labs/agent-admission-rs/pnpm-lock.yaml` | config | 22072 | 688 | `8a68ea6fe296` |  |
| `platform/security/labs/agent-admission-rs/pnpm-workspace.yaml` | config | 95 | 5 | `40b51199ffe1` |  |
| `platform/security/labs/agent-admission-rs/src/app.ts` | core | 10083 | 349 | `89ffe4df19d6` |  |
| `platform/security/labs/agent-admission-rs/src/bootstrap-grant.ts` | core | 1649 | 58 | `d1c163143467` |  |
| `platform/security/labs/agent-admission-rs/src/e2e-client.ts` | core | 8100 | 254 | `e4d9925d77a1` |  |
| `platform/security/labs/agent-admission-rs/src/errors.ts` | core | 506 | 16 | `9e0500e08752` |  |
| `platform/security/labs/agent-admission-rs/src/grant-store.ts` | core | 12826 | 429 | `8ec7b9d4f67d` |  |
| `platform/security/labs/agent-admission-rs/src/model.ts` | core | 3692 | 129 | `eb066a2e113f` |  |
| `platform/security/labs/agent-admission-rs/src/oauth-verifier.ts` | core | 3429 | 115 | `e017b41d06ec` |  |
| `platform/security/labs/agent-admission-rs/src/opa.ts` | core | 3968 | 142 | `3240223a8754` |  |
| `platform/security/labs/agent-admission-rs/src/principal-store.ts` | core | 14270 | 477 | `53b5cd341ec7` |  |
| `platform/security/labs/agent-admission-rs/src/server.ts` | core | 4339 | 139 | `c703aa117083` |  |
| `platform/security/labs/agent-admission-rs/src/webauthn-e2e.ts` | core | 15520 | 477 | `5e3313e916bc` |  |
| `platform/security/labs/agent-admission-rs/src/webauthn-router.ts` | core | 6042 | 164 | `366b9684c70b` |  |
| `platform/security/labs/agent-admission-rs/src/webauthn-service.ts` | core | 12832 | 402 | `0228450b94a6` |  |
| `platform/security/labs/agent-admission-rs/test/app.test.ts` | core | 7367 | 237 | `9e8365960c51` |  |
| `platform/security/labs/agent-admission-rs/test/compat.test.ts` | core | 670 | 18 | `8a76c5f6e2e5` |  |
| `platform/security/labs/agent-admission-rs/test/webauthn-state.test.ts` | core | 3314 | 106 | `9d1c70d64f79` |  |
| `platform/security/labs/agent-admission-rs/tsconfig.json` | config | 421 | 16 | `0225bc903b67` |  |
| `platform/security/labs/agent-admission-rs/webauthn-e2e.sh` | core | 3773 | 113 | `bdf1ef19dcd4` |  |
| `platform/security/mise.toml` | config | 1584 | 35 | `b7642b57b4cc` |  |
| `platform/security/planning/lego-plan-r1.json` | config | 14811 | 348 | `ef90efce3f17` | 1 |
| `platform/security/policies/admission.rego` | core | 6258 | 227 | `9887b7b288dc` |  |
| `platform/security/policies/admission_test.rego` | core | 6894 | 159 | `e0cf26d71f4c` |  |
| `platform/security/policies/agent_admission.rego` | core | 5008 | 196 | `88d0f3c171b5` |  |
| `platform/security/policies/agent_admission_effect_integration_test.rego` | core | 2712 | 83 | `693cd9bbec17` |  |
| `platform/security/policies/agent_admission_test.rego` | core | 6396 | 171 | `bb89ea186c41` |  |
| `platform/security/policies/consequence_verification.rego` | core | 2903 | 103 | `6b7ca8573f33` |  |
| `platform/security/policies/consequence_verification_test.rego` | core | 3369 | 101 | `1633eefea65e` |  |
| `platform/security/policies/effect_admission.rego` | core | 2631 | 109 | `66cbb6637ef0` |  |
| `platform/security/policies/effect_admission_test.rego` | core | 4764 | 136 | `161da172985b` |  |
| `platform/security/profiles/product/gitleaks.toml` | config | 392 | 11 | `f7f3ac6c5e88` |  |
| `platform/security/profiles/zap/local-authorized-r1.yaml` | config | 806 | 35 | `75b0200655ac` |  |
| `platform/security/providers/packer/plugins.pkr.hcl` | other | 126 | — | `b3b0b989bd4e` |  |
| `platform/security/providers/packer/validation.pkr.hcl` | other | 829 | — | `1c551dca841a` |  |
| `platform/security/pyproject.toml` | config | 476 | 25 | `eceb267de1be` |  |
| `platform/security/schemas/agent-admission-input-v0.schema.json` | schemas | 3636 | 81 | `115e02d23516` |  |
| `platform/security/schemas/owasp-threat-model-v1.0.2.schema.json` | schemas | 34317 | 969 | `428772fecfed` |  |
| `platform/security/scripts/assemble_gate_input.py` | core | 1724 | 49 | `4d999dba5e02` |  |
| `platform/security/scripts/build_browser_security_witness.py` | core | 1636 | 50 | `c27d540d21d2` |  |
| `platform/security/scripts/compare_browser_security_bundles.py` | core | 964 | 34 | `05cd4109e9cb` |  |
| `platform/security/scripts/compare_browser_security_pool.py` | core | 2714 | 66 | `99c25ff4f7dc` |  |
| `platform/security/scripts/compare_browser_security_witnesses.py` | core | 911 | 26 | `61d5c2061808` |  |
| `platform/security/scripts/differential_consequence_verification.py` | core | 7571 | 156 | `e59e9cd08c3f` |  |
| `platform/security/scripts/emit_attestations.py` | core | 5320 | 127 | `8e70ed11412f` |  |
| `platform/security/scripts/promote_browser_security_pool_lkg.py` | core | 20394 | 453 | `130290b0b618` |  |
| `platform/security/scripts/scan_product.sh` | core | 4002 | 86 | `a7cb09907593` |  |
| `platform/security/scripts/sign_vsa_cosign.sh` | core | 398 | 15 | `788fed3d0d9c` |  |
| `platform/security/scripts/smoke_libvirt_lifecycle.sh` | core | 1980 | 66 | `e93b9a5274b0` |  |
| `platform/security/scripts/smoke_libvirt_tpm.sh` | core | 1957 | 77 | `e5bb95e70e36` |  |
| `platform/security/scripts/smoke_scorecard_public.sh` | core | 977 | 24 | `73cbe3e82472` |  |
| `platform/security/scripts/smoke_zap_authorized_local.sh` | core | 5488 | 165 | `104e4ad9388a` |  |
| `platform/security/scripts/validate_cyclonedx_vex.py` | core | 514 | 21 | `4ece9f187b3b` |  |
| `platform/security/scripts/validate_packer_qemu.sh` | core | 280 | 8 | `aae1ec7fd823` |  |
| `platform/security/scripts/validate_scorecard_result.py` | core | 775 | 29 | `5d1dd7dde83e` |  |
| `platform/security/scripts/validate_threat_model_binding.py` | core | 537 | 22 | `0f658a38466a` |  |
| `platform/security/scripts/validate_tmbom.sh` | core | 786 | 12 | `d95265c98577` |  |
| `platform/security/scripts/verify_build_provenance.py` | core | 1262 | 35 | `e62acabb7ac3` |  |
| `platform/security/scripts/verify_remediation_delta.py` | core | 743 | 23 | `b58b72b1967c` |  |
| `platform/security/scripts/verify_vsa_bundle.py` | core | 1532 | 44 | `40b757e1bd38` |  |
| `platform/security/scripts/verify_vsa_cosign.sh` | core | 1025 | 32 | `1048b57cd1e8` |  |
| `platform/security/src/ordivon_security_v2/__init__.py` | core | 978 | 30 | `fad8e0b1616f` |  |
| `platform/security/src/ordivon_security_v2/admission.py` | core | 1568 | 46 | `0990a82a90af` |  |
| `platform/security/src/ordivon_security_v2/attestations.py` | core | 2328 | 72 | `06a30c1902d6` |  |
| `platform/security/src/ordivon_security_v2/browser_security_comparison.py` | core | 6121 | 150 | `fe296c3798f5` |  |
| `platform/security/src/ordivon_security_v2/browser_security_observation.py` | core | 3303 | 84 | `72ab3d5a0357` |  |
| `platform/security/src/ordivon_security_v2/browser_security_pool.py` | core | 5875 | 135 | `f9ceb1eebcbd` |  |
| `platform/security/src/ordivon_security_v2/browser_security_witness.py` | core | 12352 | 296 | `d11cf9ce2bb7` |  |
| `platform/security/src/ordivon_security_v2/evidence.py` | core | 2616 | 77 | `f5d2a311132b` |  |
| `platform/security/src/ordivon_security_v2/provenance.py` | core | 3611 | 84 | `fd929e6aa337` |  |
| `platform/security/src/ordivon_security_v2/remediation.py` | core | 2947 | 71 | `439c8b6fe44d` |  |
| `platform/security/src/ordivon_security_v2/scorecard.py` | core | 3433 | 95 | `aa4bf1403998` |  |
| `platform/security/src/ordivon_security_v2/signed_vsa.py` | core | 4986 | 112 | `a802633b8c15` |  |
| `platform/security/src/ordivon_security_v2/threat_model.py` | core | 2656 | 67 | `f9c3e6253bae` |  |
| `platform/security/src/ordivon_security_v2/vex.py` | core | 5845 | 137 | `5ac7498e6c17` |  |
| `platform/security/tests/fixtures/signed-vsa-r2/subject.carrier` | tests | 41 | — | `f5d3a15399b2` |  |
| `platform/security/tests/fixtures/signed-vsa-r2/trust-policy.json` | tests | 195 | 8 | `21d2510b501c` | 1 |
| `platform/security/tests/fixtures/signed-vsa-r2/verification-summary.vsa.intoto.json` | tests | 3019 | 73 | `dc313924cfb9` |  |
| `platform/security/tests/fixtures/signed-vsa-r2/verifier.pub` | tests | 178 | — | `426a1044bec0` |  |
| `platform/security/tests/fixtures/signed-vsa-r2/vsa.sigstore.json` | tests | 8001 | 1 | `719dd115d591` |  |
| `platform/security/tests/test_admission.py` | tests | 1380 | 34 | `be69715a8915` |  |
| `platform/security/tests/test_agent_admission_contract.py` | tests | 2876 | 71 | `c64f2f26a8b7` |  |
| `platform/security/tests/test_agent_admission_schema_boundary.py` | tests | 4727 | 103 | `7f17bfa0a1ca` |  |
| `platform/security/tests/test_attestations.py` | tests | 7423 | 184 | `508011b6a661` |  |
| `platform/security/tests/test_browser_security.py` | tests | 2769 | 67 | `56f07ae75f89` |  |
| `platform/security/tests/test_browser_security_collector.py` | tests | 7535 | 171 | `9e3517b81307` |  |
| `platform/security/tests/test_browser_security_lkg_reseal.py` | tests | 13184 | 319 | `4b38ea413afa` |  |
| `platform/security/tests/test_browser_security_observation_validity.py` | tests | 7655 | 199 | `63ef55f0af2d` |  |
| `platform/security/tests/test_browser_security_pool.py` | tests | 6315 | 142 | `787316d815ed` |  |
| `platform/security/tests/test_evidence.py` | tests | 2223 | 49 | `fd3810875538` |  |
| `platform/security/tests/test_opa_container_gate.py` | tests | 2593 | 62 | `4fa179ccadea` |  |
| `platform/security/tests/test_owner_uv_lock_freshness.py` | tests | 4644 | 107 | `be90e708c6cd` |  |
| `platform/security/tests/test_provenance.py` | tests | 3366 | 84 | `79b386e9f0ee` |  |
| `platform/security/tests/test_remediation.py` | tests | 2526 | 49 | `635137521df8` |  |
| `platform/security/tests/test_scorecard.py` | tests | 2358 | 58 | `261306047bf0` |  |
| `platform/security/tests/test_signed_vsa.py` | tests | 5723 | 136 | `aeaf3372e956` |  |
| `platform/security/tests/test_threat_model.py` | tests | 1839 | 45 | `74b233fcd7f6` |  |
| `platform/security/tests/test_tmbom_pinned_schema.py` | tests | 1493 | 39 | `42dd166fb427` |  |
| `platform/security/tests/test_vex.py` | tests | 2414 | 58 | `591b7641ecc5` |  |
| `platform/security/threat-models/security-v2-r1.json` | config | 12319 | 362 | `a4755e707f6d` |  |
| `platform/security/uv.lock` | config | 6062 | — | `c8e27fd02683` |  |

### workstation — platform/workstation/（265 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `platform/workstation/.gitignore` | other | 23 | — | `6feaded4e28e` |  |
| `platform/workstation/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `platform/workstation/README.md` | docs | 6938 | 86 | `bdc4a81185eb` |  |
| `platform/workstation/ansible/bootstrap.yml` | config | 875 | 28 | `e1cf36c90680` |  |
| `platform/workstation/ansible/game-production-tools.yml` | config | 672 | 20 | `aec952f50a2a` |  |
| `platform/workstation/ansible/host-substrate.yml` | config | 3043 | 87 | `0bb69bf49639` |  |
| `platform/workstation/ansible/inventory.ini` | config | 98 | 2 | `da82e5114284` |  |
| `platform/workstation/ansible/jev-fastpath-provider.yml` | config | 3475 | 109 | `a8d29923bc0c` |  |
| `platform/workstation/ansible/n8n.yml` | config | 22836 | 623 | `88ae85ddb448` |  |
| `platform/workstation/ansible/observability-grafana.yml` | config | 7203 | 208 | `52e44db92859` |  |
| `platform/workstation/ansible/observability-logs.yml` | config | 2890 | 98 | `6d45c25be741` |  |
| `platform/workstation/ansible/observability-metrics.yml` | config | 2772 | 89 | `672b91b60f7b` |  |
| `platform/workstation/ansible/observability-traces.yml` | config | 2660 | 83 | `e1be44e53c21` |  |
| `platform/workstation/ansible/postgresql-backup.yml` | config | 5114 | 148 | `b2b2c1074686` |  |
| `platform/workstation/ansible/ppt-master-provider.yml` | config | 8148 | 229 | `16393c9bb0de` |  |
| `platform/workstation/ansible/retire-wsl-cloudflare-canary.yml` | config | 655 | 22 | `b5183ce53d5b` |  |
| `platform/workstation/ansible/retire-wsl-windows-runtime-provider.yml` | config | 1884 | 53 | `fef4cf37d8be` |  |
| `platform/workstation/ansible/temporal-production.yml` | config | 9635 | 316 | `7fca03853c3b` |  |
| `platform/workstation/ansible/workstation-node-carriers.yml` | config | 1335 | 42 | `a64b56eaa632` |  |
| `platform/workstation/ansible/workstation-retire-legacy-launchers.yml` | config | 458 | 15 | `0b90302f86eb` |  |
| `platform/workstation/ansible/workstation-service-profiles.yml` | config | 3269 | 104 | `021bec6a1983` |  |
| `platform/workstation/ansible/workstation-tool-bindings.yml` | config | 2496 | 75 | `409630b6f2b3` |  |
| `platform/workstation/ansible/workstation-windows-jev-fastpath-provider.yml` | config | 1920 | 55 | `12c5c3582ac9` |  |
| `platform/workstation/contracts/README.md` | schemas | 1537 | 13 | `e43109cb2257` |  |
| `platform/workstation/contracts/asyncapi/distribution-admission-data.schema.json` | schemas | 1111 | 32 | `50a0b5eadd65` |  |
| `platform/workstation/contracts/asyncapi/distribution-integration-result-data.schema.json` | schemas | 701 | 17 | `783c2dace597` |  |
| `platform/workstation/contracts/asyncapi/integration-events.asyncapi.yaml` | schemas | 3292 | 94 | `7e646b0884a1` |  |
| `platform/workstation/contracts/cloudevents/ordivon-event.schema.json` | schemas | 846 | 20 | `d5a6310b7a63` |  |
| `platform/workstation/contracts/outbox/postgresql-outbox.sql.example` | schemas | 531 | — | `8d48a02f9867` |  |
| `platform/workstation/docs/ARCHITECTURE.md` | docs | 5550 | 129 | `00354ee7427c` |  |
| `platform/workstation/docs/CANONICAL_PATH_CUTOVER_R6.md` | docs | 2079 | 18 | `383830c98ae7` |  |
| `platform/workstation/docs/CLOUDFLARE_PROVIDER_MAINTENANCE.md` | docs | 1175 | 27 | `6d03ab78cd20` |  |
| `platform/workstation/docs/D_DRIVE_OFFLINE_MAINTENANCE_R3.md` | docs | 5287 | 47 | `0ad3e6176e60` |  |
| `platform/workstation/docs/HOST_HISTORICAL_PROJECTION_R3.md` | docs | 7355 | 227 | `c11c67cbca44` |  |
| `platform/workstation/docs/JEV_FASTPATH_PROVIDER.md` | docs | 3645 | 27 | `b8c3bca0321e` |  |
| `platform/workstation/docs/MIGRATION_R1.md` | docs | 4571 | 73 | `36db695b38c0` |  |
| `platform/workstation/docs/N8N_DISTRIBUTION_ADAPTER_SMOKE.md` | docs | 1884 | 32 | `9e415b52c755` |  |
| `platform/workstation/docs/N8N_INTEGRATION_SMOKE.md` | docs | 3517 | 81 | `7620544a68f4` |  |
| `platform/workstation/docs/N8N_SERVICE.md` | docs | 5148 | 86 | `2b6c1e7b8130` |  |
| `platform/workstation/docs/PPT_MASTER_PROVIDER.md` | docs | 1989 | 26 | `e8053a86a721` |  |
| `platform/workstation/docs/STANDARDS_FIRST_COMPOSITION.md` | docs | 3590 | 42 | `57b0dab5dd5b` |  |
| `platform/workstation/docs/TEMPORAL_PRODUCTION_GREEN.md` | docs | 1548 | 34 | `8d0a07acef88` |  |
| `platform/workstation/docs/UPDATE_DISCOVERY_R2.md` | docs | 8069 | 142 | `2987a8f4172c` |  |
| `platform/workstation/docs/WINDOWS_CLOUDFLARED_RUNTIME_INGRESS.md` | docs | 4170 | 69 | `e02c803c58bd` |  |
| `platform/workstation/docs/WORKSTATION_CONTRACT_FIRST_EXECUTION_SPEC_R1.md` | docs | 27804 | 404 | `dd413bf17950` |  |
| `platform/workstation/evidence/host-v1-final-pg-archive-20260913.json` | evidence | 5196 | 163 | `03d87c5c640c` | 1 |
| `platform/workstation/evidence/host-v1-parquet-duckdb-r3-20260913.json` | evidence | 10057 | 265 | `5d84d4bb2224` | 1 |
| `platform/workstation/grafana/grafana.env` | other | 935 | — | `679aaffd19f9` |  |
| `platform/workstation/grafana/ordivon-grafana.container` | other | 746 | — | `0dca0b444779` |  |
| `platform/workstation/host/coredump.conf.d-20-ordivon-agent-node.conf` | config | 41 | 3 | `6868e6143a5f` |  |
| `platform/workstation/host/system.conf.d-20-ordivon-agent-limits.conf` | config | 43 | 2 | `cebf04f23836` |  |
| `platform/workstation/host/user.conf.d-20-ordivon-agent-limits.conf` | config | 43 | 2 | `cebf04f23836` |  |
| `platform/workstation/inventory/README.md` | docs | 5840 | 112 | `4473ebfbc41a` |  |
| `platform/workstation/inventory/current-substrate.md` | docs | 5190 | 83 | `441704bde059` |  |
| `platform/workstation/inventory/probe_executables.ps1` | core | 1495 | 31 | `4dc43ca235bd` |  |
| `platform/workstation/inventory/probe_executables.py` | core | 2212 | 67 | `43c9b12420eb` |  |
| `platform/workstation/inventory/queries/npm_packages.sql` | schemas | 75 | 3 | `2a7f9262e3b1` |  |
| `platform/workstation/inventory/queries/os_version.sql` | schemas | 84 | 1 | `beb3b892af28` |  |
| `platform/workstation/inventory/queries/python_packages.sql` | schemas | 78 | 3 | `8c108ee331ca` |  |
| `platform/workstation/inventory/queries/running_executables.sql` | schemas | 74 | 4 | `47ff16e0ad72` |  |
| `platform/workstation/inventory/queries/system_identity.sql` | schemas | 95 | 1 | `bb0d41249dba` |  |
| `platform/workstation/inventory/queries/uptime.sql` | schemas | 65 | 1 | `c29815c0c423` |  |
| `platform/workstation/inventory/snapshots/2026-09-14-machine-tools.json` | config | 11106 | 389 | `9ef1a7ae856f` | 1 |
| `platform/workstation/inventory/sources.json` | config | 3445 | 127 | `b564087cd4df` | 1 |
| `platform/workstation/manifests/external-stack-v1.json` | config | 3484 | 39 | `6afd27850f8e` | 1 |
| `platform/workstation/mise.toml` | config | 1293 | 47 | `d8b3409c8bd7` |  |
| `platform/workstation/n8n/n8n.env` | other | 1086 | — | `f3ebb4d7c863` |  |
| `platform/workstation/n8n/ordivon-n8n-runners.container` | other | 640 | — | `71f0b91fcf47` |  |
| `platform/workstation/n8n/ordivon-n8n.container` | other | 706 | — | `aa3048800bd4` |  |
| `platform/workstation/n8n/ordivon-n8n.pod` | other | 357 | — | `bf9a787f3aee` |  |
| `platform/workstation/n8n/workflows/ordivon-distribution-adapter-smoke-v1.json` | config | 6063 | 175 | `55587b457c31` |  |
| `platform/workstation/n8n/workflows/ordivon-integration-smoke-v1.json` | config | 3497 | 78 | `700d2e82c9fd` |  |
| `platform/workstation/observability/README.md` | docs | 1590 | 30 | `dd7a67e1303b` |  |
| `platform/workstation/observability/gatus/config.yaml` | config | 3499 | 88 | `462b5b764a75` |  |
| `platform/workstation/observability/gatus/ordivon-gatus.service` | config | 834 | 33 | `af1c384d9f9d` |  |
| `platform/workstation/observability/grafana-datasources.yaml` | config | 787 | 45 | `2a61f1249b1d` |  |
| `platform/workstation/observability/loki.yaml` | config | 1147 | 48 | `32c6620a1fc7` |  |
| `platform/workstation/observability/netdata-v2.conf` | config | 146 | 3 | `599b4910e49b` |  |
| `platform/workstation/observability/node-exporter.conf` | config | 58 | 1 | `88ee4b1c0b1e` |  |
| `platform/workstation/observability/prometheus.conf` | config | 115 | 1 | `602dcf778a58` |  |
| `platform/workstation/observability/prometheus.yml` | config | 934 | 33 | `0cac4ba11390` |  |
| `platform/workstation/observability/tempo.yaml` | config | 413 | 25 | `fce889bc593e` |  |
| `platform/workstation/observability/vector-systemd.conf` | config | 459 | 13 | `e07c0874da68` |  |
| `platform/workstation/observability/vector.yaml` | config | 1795 | 85 | `49fc70c8d4b2` |  |
| `platform/workstation/policy/README.md` | docs | 530 | 7 | `67c1e2719679` |  |
| `platform/workstation/postgresql/ordivon-postgresql-backup.service` | config | 398 | 14 | `2734a5838a65` |  |
| `platform/workstation/postgresql/ordivon-postgresql-backup.timer` | config | 207 | — | `fe37acad196b` |  |
| `platform/workstation/postgresql/pgbackrest.conf` | config | 297 | 13 | `04b39fb6f11b` |  |
| `platform/workstation/postgresql/postgresql-pgdata.conf` | config | 349 | 7 | `99232a3f9a39` |  |
| `platform/workstation/providers/cloudflare/.gitignore` | other | 107 | — | `e974965f6f95` |  |
| `platform/workstation/providers/cloudflare/AGENTS.md` | docs | 796 | 15 | `ea421e882bbc` |  |
| `platform/workstation/providers/cloudflare/LICENSE` | other | 11358 | — | `c95bae1d1ce0` |  |
| `platform/workstation/providers/cloudflare/MIGRATION_PROVENANCE.md` | docs | 1230 | 17 | `a9328cf7f21d` |  |
| `platform/workstation/providers/cloudflare/README.md` | docs | 4747 | 86 | `228718f3fc6c` | 1 |
| `platform/workstation/providers/cloudflare/config/edge-policy.json` | config | 2108 | 102 | `80907310fde1` |  |
| `platform/workstation/providers/cloudflare/deploy/systemd/ordivon-edge-gc.service` | config | 511 | 21 | `301cd446f678` |  |
| `platform/workstation/providers/cloudflare/deploy/systemd/ordivon-edge-gc.timer` | config | 228 | — | `03c889a4bed7` |  |
| `platform/workstation/providers/cloudflare/docs/operations.md` | docs | 9738 | 239 | `638c91b9ee27` | 1 |
| `platform/workstation/providers/cloudflare/docs/release.md` | docs | 6053 | 121 | `efca0c551a06` | 1 |
| `platform/workstation/providers/cloudflare/docs/reliability.md` | docs | 6888 | 154 | `ffd3a34d0352` | 1 |
| `platform/workstation/providers/cloudflare/docs/security.md` | docs | 7406 | 135 | `a6a4e33994d3` | 1 |
| `platform/workstation/providers/cloudflare/package.json` | config | 1396 | 27 | `bf61aee0656e` |  |
| `platform/workstation/providers/cloudflare/pnpm-lock.yaml` | config | 50196 | 1574 | `070d8b2b8a2c` |  |
| `platform/workstation/providers/cloudflare/pnpm-workspace.yaml` | config | 371 | 14 | `f5f7c8e5578f` |  |
| `platform/workstation/providers/cloudflare/scripts/check-operations` | other | 552 | — | `76e220529f27` |  |
| `platform/workstation/providers/cloudflare/scripts/check-policy-config.py` | core | 1773 | 45 | `e3187559c6fb` |  |
| `platform/workstation/providers/cloudflare/scripts/configure-r2-lifecycle` | other | 95 | — | `ce66219dfc9c` |  |
| `platform/workstation/providers/cloudflare/scripts/configure_r2_lifecycle.py` | core | 5778 | 154 | `8761a9e9c07f` |  |
| `platform/workstation/providers/cloudflare/scripts/emit-contract-fixtures.ts` | core | 3902 | 144 | `8c895d0608a6` |  |
| `platform/workstation/providers/cloudflare/scripts/install-edge-client` | other | 167 | — | `2a3e2a35173e` |  |
| `platform/workstation/providers/cloudflare/scripts/install-edge-operations` | other | 2299 | — | `467cf9954908` |  |
| `platform/workstation/providers/cloudflare/scripts/ordivon_cloudflare_tofu_handoff.py` | core | 35605 | 865 | `ee1b7f5c625b` |  |
| `platform/workstation/providers/cloudflare/scripts/ordivon_edge_client.py` | core | 18681 | 556 | `961f48b6be62` |  |
| `platform/workstation/providers/cloudflare/scripts/ordivon_edge_gc.py` | core | 10367 | 297 | `f9e666c5fbb5` |  |
| `platform/workstation/providers/cloudflare/scripts/ordivon_edge_release.py` | core | 44105 | 1318 | `9ff2af1c379e` |  |
| `platform/workstation/providers/cloudflare/scripts/tsconfig.contracts.json` | config | 135 | 9 | `a7eb5457a638` |  |
| `platform/workstation/providers/cloudflare/scripts/wrangler-dry-run.mjs` | core | 2193 | 82 | `f130b453655d` |  |
| `platform/workstation/providers/cloudflare/src/artifacts.ts` | core | 974 | 27 | `55db16d3f686` |  |
| `platform/workstation/providers/cloudflare/src/auth.ts` | core | 5020 | 144 | `bea250c4b975` |  |
| `platform/workstation/providers/cloudflare/src/body.ts` | core | 1904 | 63 | `a8939a171a62` |  |
| `platform/workstation/providers/cloudflare/src/browser-manifest.ts` | core | 1940 | 56 | `49404336209e` |  |
| `platform/workstation/providers/cloudflare/src/browser-policy.ts` | core | 4123 | 138 | `3c1b6c7b607e` |  |
| `platform/workstation/providers/cloudflare/src/browser-run.ts` | core | 8878 | 281 | `79b2ed12bf56` |  |
| `platform/workstation/providers/cloudflare/src/cleanup.ts` | core | 2541 | 82 | `996d7d479edb` |  |
| `platform/workstation/providers/cloudflare/src/contracts.ts` | core | 4491 | 148 | `a16ed23a34b2` |  |
| `platform/workstation/providers/cloudflare/src/errors.ts` | core | 1070 | 43 | `7178cbdc1130` |  |
| `platform/workstation/providers/cloudflare/src/execution.ts` | core | 1061 | 36 | `2b98ea440c33` |  |
| `platform/workstation/providers/cloudflare/src/external-fetch.ts` | core | 6040 | 195 | `47f6626f906d` |  |
| `platform/workstation/providers/cloudflare/src/fetch-policy.ts` | core | 4837 | 160 | `da3e1f6d9c1f` |  |
| `platform/workstation/providers/cloudflare/src/http.ts` | core | 1180 | 40 | `bea8b3f773df` |  |
| `platform/workstation/providers/cloudflare/src/idempotency.ts` | core | 14196 | 490 | `73aad11ea2c7` |  |
| `platform/workstation/providers/cloudflare/src/index.ts` | core | 15046 | 549 | `04a44ffcd8df` |  |
| `platform/workstation/providers/cloudflare/src/observability.ts` | core | 2119 | 61 | `3490e670f492` |  |
| `platform/workstation/providers/cloudflare/src/policy.ts` | core | 1535 | 48 | `8d20dd5e59c0` |  |
| `platform/workstation/providers/cloudflare/src/receipts.ts` | core | 4704 | 135 | `e139a91b6828` |  |
| `platform/workstation/providers/cloudflare/src/version.ts` | core | 853 | 30 | `10515b7c8e80` |  |
| `platform/workstation/providers/cloudflare/test/client_test.py` | core | 9128 | 218 | `f06f860436d4` |  |
| `platform/workstation/providers/cloudflare/test/contracts.test.ts` | core | 9016 | 305 | `5d9bfa823d19` |  |
| `platform/workstation/providers/cloudflare/test/gc_test.py` | core | 4135 | 114 | `537e39fcaa50` |  |
| `platform/workstation/providers/cloudflare/test/handoff_tofu_test.py` | core | 20162 | 441 | `1ffbe20f9e73` |  |
| `platform/workstation/providers/cloudflare/test/helpers.ts` | core | 9057 | 274 | `ebc7f7463e6a` |  |
| `platform/workstation/providers/cloudflare/test/lifecycle_test.py` | core | 4018 | 119 | `f507bbddc912` |  |
| `platform/workstation/providers/cloudflare/test/release_controller_test.py` | core | 22419 | 549 | `b17a9c4d3ca2` |  |
| `platform/workstation/providers/cloudflare/test/transactions.test.ts` | core | 13160 | 414 | `8d8b35b28ebf` |  |
| `platform/workstation/providers/cloudflare/test/worker.test.ts` | core | 14944 | 438 | `64869b83815c` |  |
| `platform/workstation/providers/cloudflare/tsconfig.json` | config | 651 | 30 | `87842799f63c` |  |
| `platform/workstation/providers/cloudflare/wrangler.jsonc` | other | 1289 | — | `d310f8f2b837` |  |
| `platform/workstation/pyproject.toml` | config | 765 | 38 | `fd5f97fd23ae` |  |
| `platform/workstation/scripts/accept-n8n-distribution-adapter-smoke.sh` | core | 2232 | 35 | `ee764373f349` |  |
| `platform/workstation/scripts/converge-n8n-distribution-adapter-smoke.sh` | core | 2393 | 32 | `13741b1ad5cb` |  |
| `platform/workstation/scripts/converge-n8n-integration-smoke.sh` | core | 2601 | 76 | `9bd85ee9adde` |  |
| `platform/workstation/scripts/deploy-gatus` | other | 4854 | — | `e17e616459c9` |  |
| `platform/workstation/scripts/host_historical_projection.py` | core | 22384 | 463 | `7dab17dac833` |  |
| `platform/workstation/scripts/invoke-n8n-distribution-adapter-smoke.py` | core | 3009 | 41 | `4581b2f8ec7b` |  |
| `platform/workstation/scripts/invoke-n8n-integration-smoke.py` | core | 2090 | 64 | `ca60a35d4c77` |  |
| `platform/workstation/scripts/temporal-n8n-integration-smoke.py` | core | 3214 | 100 | `064fed5f7f5e` |  |
| `platform/workstation/scripts/temporal_green_smoke.py` | core | 2037 | 61 | `2628eac4f8f6` |  |
| `platform/workstation/scripts/temporal_nexus_smoke.py` | core | 3193 | 105 | `b9efc1dd79fb` |  |
| `platform/workstation/scripts/temporal_pgbackrest_restore_smoke.sh` | core | 3375 | 90 | `2693ba1475df` |  |
| `platform/workstation/scripts/test-integration-contracts.py` | core | 2187 | 34 | `7892d7799f20` |  |
| `platform/workstation/scripts/verify-n8n-rootless.sh` | core | 2005 | 52 | `58f38a0ff432` |  |
| `platform/workstation/systemd/ordivon-observability-heavy.target` | config | 247 | — | `bade2b075aff` |  |
| `platform/workstation/systemd/ordivon-update-discovery.service` | config | 556 | 15 | `6d452a2149f1` |  |
| `platform/workstation/systemd/ordivon-update-discovery.timer` | config | 217 | — | `735dc6f24839` |  |
| `platform/workstation/systemd/service-profiles/loki.service.d/20-ordivon-observability-heavy.conf` | config | 49 | 2 | `831a8280fa59` |  |
| `platform/workstation/systemd/service-profiles/netdata.service.d/20-ordivon-observability-heavy.conf` | config | 49 | 2 | `831a8280fa59` |  |
| `platform/workstation/systemd/service-profiles/vector.service.d/20-ordivon-observability-heavy.conf` | config | 49 | 2 | `831a8280fa59` |  |
| `platform/workstation/tempo/ordivon-tempo.container` | other | 684 | — | `1c8ae9d9ad89` |  |
| `platform/workstation/temporal/production.yaml` | config | 1956 | 84 | `5424694c0322` |  |
| `platform/workstation/temporal/temporal.service.j2` | other | 1119 | — | `c9641e68a86a` |  |
| `platform/workstation/tests/test_codex_cli_pnpm_contract.py` | tests | 3016 | 60 | `6a4a49fe3541` |  |
| `platform/workstation/tests/test_d_drive_compact_r3.py` | tests | 9851 | 238 | `955059422662` |  |
| `platform/workstation/tests/test_distribution_adapter_source_binding.py` | tests | 2211 | 58 | `7f3cf9fa46f8` |  |
| `platform/workstation/tests/test_equipment_binding_compat.py` | tests | 1635 | 31 | `56998456d77b` |  |
| `platform/workstation/tests/test_executable_probe.py` | tests | 2956 | 87 | `265b3d98f1f0` |  |
| `platform/workstation/tests/test_gateway_mcp_tofu.py` | tests | 2829 | 61 | `d3f3e4f0213c` |  |
| `platform/workstation/tests/test_gatus_deployment.py` | tests | 2486 | 56 | `74d409bc2ada` |  |
| `platform/workstation/tests/test_host_historical_projection.py` | tests | 1716 | 37 | `d2d5e440b541` |  |
| `platform/workstation/tests/test_host_substrate_authority.py` | tests | 5524 | 132 | `7aab5944580f` |  |
| `platform/workstation/tests/test_jev_consumer_secret_materializer.py` | tests | 862 | 21 | `f8abc715e430` |  |
| `platform/workstation/tests/test_jev_fastpath_provider.py` | tests | 2350 | 52 | `fe072b9342a6` |  |
| `platform/workstation/tests/test_machine_inventory_contract.py` | tests | 2263 | 50 | `6c2bb2c36ed9` |  |
| `platform/workstation/tests/test_node_manifest_unique_keys.py` | tests | 1692 | 49 | `c4372a42ed53` |  |
| `platform/workstation/tests/test_observability_prometheus.py` | tests | 976 | 23 | `71796b8b55ee` |  |
| `platform/workstation/tests/test_observability_traces.py` | tests | 2885 | 72 | `6e2052f1a22b` |  |
| `platform/workstation/tests/test_playwright_cli_binding.py` | tests | 2656 | 53 | `6fbf1f81d86d` |  |
| `platform/workstation/tests/test_provider_authority_validation.py` | tests | 1313 | 31 | `0e256ced3939` |  |
| `platform/workstation/tests/test_provider_linux_observers.py` | tests | 2048 | 70 | `8a482eafb349` |  |
| `platform/workstation/tests/test_provider_windows_wsl.py` | tests | 2502 | 57 | `04dadaa5f7e4` |  |
| `platform/workstation/tests/test_provider_windows_wsl_service.py` | tests | 1148 | 28 | `5b1b09a13493` |  |
| `platform/workstation/tests/test_runtime_provider_retirement.py` | tests | 1052 | 27 | `5283d45b89ac` |  |
| `platform/workstation/tests/test_service_profiles.py` | tests | 3298 | 68 | `777a9d0eff3d` |  |
| `platform/workstation/tests/test_temporal_pgbackrest_restore_smoke.py` | tests | 2045 | 57 | `7270abf0aa89` |  |
| `platform/workstation/tests/test_temporal_restore_scratch_safety.py` | tests | 3588 | 76 | `27b645fc1246` |  |
| `platform/workstation/tests/test_temporal_restore_stop_failure.py` | tests | 2705 | 62 | `4a643f5d8cb8` |  |
| `platform/workstation/tests/test_temporal_sdk_ops_contract.py` | tests | 1256 | 32 | `76e153726c5a` |  |
| `platform/workstation/tests/test_tofu_agent_birth_handoff.py` | tests | 2991 | 68 | `38bf1119ff73` |  |
| `platform/workstation/tests/test_tool_binding_projection.py` | tests | 2615 | 77 | `4e2448343083` |  |
| `platform/workstation/tests/test_update_candidate_report.py` | tests | 7991 | 211 | `f00a8f0f5102` |  |
| `platform/workstation/tests/test_windows_cloudflared_runtime_ingress.py` | tests | 2452 | 57 | `303f9c2631b4` |  |
| `platform/workstation/tests/test_windows_jev_fastpath_provider.py` | tests | 9969 | 221 | `5302f9227d06` |  |
| `platform/workstation/tests/test_windows_update_discovery_contract.py` | tests | 4476 | 112 | `e31e910a9a58` |  |
| `platform/workstation/tests/test_windows_user_git_bundle_consumer.py` | tests | 1968 | 50 | `b5a8c940406a` |  |
| `platform/workstation/tests/test_windows_workspace_environment_doctor.py` | tests | 4194 | 92 | `a625d8f8bd4f` |  |
| `platform/workstation/tests/test_workstation_agent_automation_carrier.py` | tests | 5286 | 92 | `47b6365d9e7a` |  |
| `platform/workstation/tests/test_workstation_consequences.py` | tests | 6032 | 136 | `3f28d5c2434f` |  |
| `platform/workstation/tests/test_workstation_input_authority_ingress.py` | tests | 17917 | 392 | `462aedc9705f` |  |
| `platform/workstation/tests/test_workstation_tool_binding.py` | tests | 2075 | 41 | `9b7e706527e2` |  |
| `platform/workstation/tests/test_wsl_cloudflare_canary_retirement.py` | tests | 895 | 21 | `40407a8dd4d5` |  |
| `platform/workstation/tests/test_wsl_sparse_guest_health.py` | tests | 935 | 24 | `28857e5dd15f` |  |
| `platform/workstation/tofu/README.md` | docs | 610 | 13 | `69594a774b64` |  |
| `platform/workstation/tofu/agent-birth-handoff/.gitignore` | other | 53 | — | `f5e680799657` |  |
| `platform/workstation/tofu/agent-birth-handoff/.terraform.lock.hcl` | other | 284 | — | `a2133078d430` |  |
| `platform/workstation/tofu/agent-birth-handoff/README.md` | docs | 2799 | 60 | `4dc53d2336bd` |  |
| `platform/workstation/tofu/agent-birth-handoff/main.tf` | other | 10900 | — | `c3a9bc56bf00` |  |
| `platform/workstation/tofu/agent-birth-handoff/outputs.tf` | other | 1569 | — | `337cf6dad77d` |  |
| `platform/workstation/tofu/agent-birth-handoff/tofurc` | other | 172 | — | `fa958f234b76` |  |
| `platform/workstation/tofu/agent-birth-handoff/variables.tf` | other | 149 | — | `bb52071177e2` |  |
| `platform/workstation/tofu/agent-birth-handoff/versions.tf` | other | 304 | — | `2d3d950e7d60` |  |
| `platform/workstation/tools/update_candidate_report.py` | core | 11525 | 320 | `043fad3c3c49` |  |
| `platform/workstation/uv.lock` | config | 37216 | — | `b0ec89ffd52b` |  |
| `platform/workstation/windows/install_update_discovery.ps1` | core | 2889 | 55 | `bcc2472e8cec` |  |
| `platform/workstation/windows/update_candidate_report.ps1` | core | 6306 | 183 | `4cb59591f897` |  |
| `platform/workstation/windows/user_git_bundle_checkout.ps1` | core | 6254 | 132 | `8e595c380d08` |  |
| `platform/workstation/windows/workspace_environment_doctor.ps1` | core | 7969 | 162 | `babd82f7077d` |  |
| `platform/workstation/workstation/README.md` | docs | 3929 | 32 | `277eaa72a2c2` |  |
| `platform/workstation/workstation/agent_automation_carrier.py` | core | 3078 | 70 | `6e9eaed89130` |  |
| `platform/workstation/workstation/equipment_binding.py` | core | 6484 | 137 | `412eb4967263` |  |
| `platform/workstation/workstation/input_authority_contract.py` | core | 6615 | 183 | `583af37cd169` |  |
| `platform/workstation/workstation/input_authority_ingress.py` | core | 24193 | 669 | `e6aaae6dd375` |  |
| `platform/workstation/workstation/nix/codex-cli/README.md` | docs | 549 | 10 | `1452b01a086e` |  |
| `platform/workstation/workstation/nix/codex-cli/package.json` | config | 268 | 10 | `6df116222d86` |  |
| `platform/workstation/workstation/nix/codex-cli/pnpm-lock.yaml` | config | 7199 | 243 | `32b597c94bcf` |  |
| `platform/workstation/workstation/nix/codex-cli/pnpm-workspace.yaml` | config | 188 | 2 | `970c1b094004` |  |
| `platform/workstation/workstation/nix/flake.lock` | config | 1291 | — | `049f1b193a78` |  |
| `platform/workstation/workstation/nix/flake.nix` | other | 742 | — | `1843cefad603` |  |
| `platform/workstation/workstation/nix/nix/home.nix` | other | 6047 | — | `10cd8e54d5a9` |  |
| `platform/workstation/workstation/playwright_cli_binding.py` | core | 5694 | 149 | `e8d2866b144a` |  |
| `platform/workstation/workstation/providers/README.md` | docs | 2486 | 52 | `2cc03ad0da7e` |  |
| `platform/workstation/workstation/providers/acceptance/authority-validation-r1.json` | config | 1229 | 33 | `2eb6e69d4d75` | 1 |
| `platform/workstation/workstation/providers/acceptance/windows-wsl-observer-r1.json` | config | 1404 | 36 | `1b737bd1f213` | 1 |
| `platform/workstation/workstation/providers/acceptance/windows-wsl-service-control-r1.json` | config | 1893 | 51 | `cde12921a182` | 1 |
| `platform/workstation/workstation/providers/authority_validation/AuthorityValidationProvider.ps1` | core | 3428 | 99 | `dba66abe2ca9` |  |
| `platform/workstation/workstation/providers/authority_validation/materialize.py` | core | 1951 | 54 | `e092cc39ba2f` |  |
| `platform/workstation/workstation/providers/d_drive_compact/DDriveCompactAuthorizeR4.ps1` | core | 4273 | 32 | `dcf5fafa1654` |  |
| `platform/workstation/workstation/providers/d_drive_compact/DDriveCompactRunR3.ps1` | core | 4472 | 45 | `e078f92a581f` |  |
| `platform/workstation/workstation/providers/d_drive_compact/DDriveOfflineCompactR3.ps1` | core | 14758 | 178 | `948751b48b84` |  |
| `platform/workstation/workstation/providers/d_drive_compact/d_drive_compact_gate_r3.py` | core | 21768 | 548 | `84740361da29` |  |
| `platform/workstation/workstation/providers/d_drive_compact/materialize.py` | core | 2158 | 41 | `1d8fb0a6e960` |  |
| `platform/workstation/workstation/providers/linux_service_observer.py` | core | 1308 | 49 | `10368f4c0cc3` |  |
| `platform/workstation/workstation/providers/runtime_control_provider.py` | core | 2017 | 75 | `5035a97a1224` |  |
| `platform/workstation/workstation/providers/windows_wsl/WindowsWslProvider.ps1` | core | 6549 | 177 | `04bbab7a2388` |  |
| `platform/workstation/workstation/providers/windows_wsl/materialize.py` | core | 2250 | 69 | `d1e8cbb6e337` |  |
| `platform/workstation/workstation/providers/windows_wsl_service/WindowsWslServiceControlProvider.ps1` | core | 2756 | 94 | `1f326b9f68a6` |  |
| `platform/workstation/workstation/providers/windows_wsl_service/materialize.py` | core | 1815 | 44 | `d25d71879cb4` |  |
| `platform/workstation/workstation/providers/wsl_sparse_guest_health.py` | core | 3340 | 88 | `890e6d26ed62` |  |
| `platform/workstation/workstation/software.toml` | config | 10193 | 273 | `a5ea56307f39` |  |
| `platform/workstation/workstation/tool_binding.py` | core | 13120 | 268 | `7f415c7dc4cf` |  |
| `platform/workstation/workstation/windows/cloudflared-runtime.dsc.yaml` | config | 929 | 25 | `f106b7b3a456` |  |
| `platform/workstation/workstation/windows/jev-fastpath-provider.toml` | config | 1185 | 21 | `2a8b081014de` |  |
| `platform/workstation/workstation/windows/jev_fastpath_provider.py` | core | 24984 | 635 | `ba1da708e35d` |  |
| `platform/workstation/workstation/windows/materialize-cloudflared-runtime-token.ps1` | core | 2633 | 67 | `4c37e5391f9d` |  |
| `platform/workstation/workstation/windows/materialize-jev-consumer-secrets.ps1` | core | 2047 | 60 | `2d2570a73fa0` |  |
| `platform/workstation/workstation/windows/materialize_jev_consumer_secrets.py` | core | 4057 | 109 | `91a4cfe1a657` |  |
| `platform/workstation/workstation/windows/workstation.dsc.yaml` | config | 872 | 34 | `09d211ae2b6b` |  |

### network — platform/network/（236 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `platform/network/.github/actionlint.yaml` | config | 48 | 3 | `0188694e9af0` |  |
| `platform/network/.gitignore` | other | 59 | — | `1643122ef953` |  |
| `platform/network/AGENTS.md` | docs | 862 | 15 | `0776c3e0db19` |  |
| `platform/network/README.md` | docs | 7743 | 161 | `a57fefe1173c` |  |
| `platform/network/STACK.md` | docs | 1639 | 32 | `b762ad1b8cb2` |  |
| `platform/network/Taskfile.yml` | config | 13409 | 285 | `67331343e612` |  |
| `platform/network/acceptance/README.md` | docs | 1175 | 22 | `bdfdda3a3aa2` |  |
| `platform/network/acceptance/connectivity/direct-chain.sh` | core | 4202 | 94 | `087beaee4520` |  |
| `platform/network/acceptance/connectivity/family-fallback.sh` | core | 3469 | 59 | `8ca86d8d82da` |  |
| `platform/network/acceptance/dns/upstream-resilience.sh` | core | 3551 | 82 | `7e61c171f433` |  |
| `platform/network/acceptance/egress/finance-lane-witness.py` | core | 7155 | 162 | `ce6ca8c570cd` |  |
| `platform/network/acceptance/egress/finance-public-data.py` | core | 9232 | 215 | `c1c4aa6e80b8` |  |
| `platform/network/acceptance/egress/live-carrier-witness.py` | core | 11388 | 250 | `0d17421a602e` |  |
| `platform/network/acceptance/fault/l4-toxiproxy.sh` | core | 1205 | 16 | `4c635bc751c2` |  |
| `platform/network/acceptance/full-ip/tun-quic.sh` | core | 3708 | 101 | `a2c8714efb94` |  |
| `platform/network/acceptance/lifecycle/cold-start.sh` | core | 3321 | 83 | `78dc938d07b0` |  |
| `platform/network/acceptance/lifecycle/process-recovery.sh` | core | 2089 | 65 | `026991ba7c12` |  |
| `platform/network/acceptance/observability/blackbox-prometheus.sh` | core | 4642 | 90 | `d0254da9ab37` |  |
| `platform/network/acceptance/observability/live-prometheus-ready.sh` | core | 665 | 19 | `06f47210cb4c` |  |
| `platform/network/acceptance/observability/prometheus-singbox-sample.sh` | core | 945 | 26 | `5cb9af443f77` |  |
| `platform/network/acceptance/protocol/divergence.sh` | core | 1637 | 41 | `82b1991cb397` |  |
| `platform/network/acceptance/topology/netns.sh` | core | 1247 | 24 | `20bc2f36f37f` |  |
| `platform/network/capabilities/README.md` | docs | 361 | 8 | `ae46cd4e8023` |  |
| `platform/network/capabilities/failover/Taskfile.yml` | config | 268 | 7 | `e001c6ac7d3d` |  |
| `platform/network/capabilities/failover/acceptance/priority-failover-smoke.sh` | core | 6672 | 192 | `f7740226a610` |  |
| `platform/network/capabilities/wireguard/Taskfile.yml` | config | 1517 | 28 | `259cab095963` |  |
| `platform/network/capabilities/wireguard/acceptance/userspace-lifecycle.sh` | core | 2422 | 105 | `448b4f13ecda` |  |
| `platform/network/capabilities/wireguard/external/wireguard-go.lock` | config | 280 | — | `6b92b267bfef` |  |
| `platform/network/config/blackbox/blackbox.yml` | config | 4261 | 138 | `138168d56adc` |  |
| `platform/network/config/prometheus/consumer.rules.yml` | config | 5129 | 88 | `2285a4754d66` |  |
| `platform/network/config/prometheus/consumers/claude.yml` | config | 579 | 21 | `3b88ba37049d` |  |
| `platform/network/config/prometheus/consumers/codex.yml` | config | 1118 | 40 | `e355906b930b` |  |
| `platform/network/config/prometheus/consumers/finance.yml` | config | 1140 | 40 | `5bffeeddd7fc` |  |
| `platform/network/config/prometheus/consumers/model-provider.yml` | config | 610 | 21 | `3e4c4e52a97c` |  |
| `platform/network/config/prometheus/consumers/supply-chain.yml` | config | 1099 | 40 | `35e1faf7c7f2` |  |
| `platform/network/config/prometheus/prometheus.yml` | config | 3529 | 140 | `2d3ff31c2d4a` |  |
| `platform/network/config/sing-box/direct.json` | config | 527 | 22 | `813df55b5589` |  |
| `platform/network/config/sysctl/90-network-v2-forwarding.conf` | config | 239 | 4 | `8f5d2ef3589a` |  |
| `platform/network/consumers/README.md` | docs | 1006 | 11 | `bb342edb906c` |  |
| `platform/network/consumers/browserless/README.md` | docs | 3603 | 35 | `8fcd905ef081` |  |
| `platform/network/consumers/browserless/Taskfile.yml` | config | 8801 | 117 | `b4084233b659` |  |
| `platform/network/consumers/browserless/acceptance/production-path.sh` | core | 3811 | 78 | `27cb303735b9` |  |
| `platform/network/consumers/browserless/acceptance/serial-browserless.sh` | core | 13582 | 289 | `e4d9810f1c11` |  |
| `platform/network/consumers/browserless/config/provider-carrier.json` | config | 906 | 50 | `b99e6face0c5` |  |
| `platform/network/consumers/browserless/production-cutover.sh` | core | 15523 | 277 | `c007ea77ba05` |  |
| `platform/network/consumers/browserless/provider-switch.sh` | core | 7491 | 150 | `4721513af904` |  |
| `platform/network/consumers/browserless/systemd/network-v2-browserless-dns.service` | config | 733 | 18 | `5b9d063190ab` |  |
| `platform/network/consumers/browserless/systemd/network-v2-browserless-legacy-provider.target` | config | 608 | — | `c412d19ed9f7` |  |
| `platform/network/consumers/browserless/systemd/network-v2-browserless-provider-carrier.service` | config | 748 | 20 | `d9219cec0d20` |  |
| `platform/network/consumers/browserless/systemd/network-v2-browserless-wireguard.service` | config | 781 | 18 | `1cb16e934a8a` |  |
| `platform/network/consumers/chat-ingress/Taskfile.yml` | config | 4125 | 56 | `8a1f6f76c3c9` |  |
| `platform/network/consumers/chat-ingress/config/egress.json` | config | 401 | 13 | `e9a470f38af0` | 1 |
| `platform/network/consumers/chat-ingress/config/sing-box.json` | config | 777 | 46 | `b4f6d75d96b6` |  |
| `platform/network/consumers/chat-ingress/ready.sh` | core | 1306 | 23 | `d525cc1c2517` |  |
| `platform/network/consumers/chat-ingress/systemd/network-v2-chat-ingress-proxy.service` | config | 657 | 19 | `14854a26ac4e` |  |
| `platform/network/consumers/chat-ingress/systemd/network-v2-chat-ingress-relay.service` | config | 844 | 17 | `a697b15c02c9` |  |
| `platform/network/consumers/chat-ingress/systemd/network-v2-chat-ingress.target` | config | 333 | — | `2fc9396e783e` |  |
| `platform/network/consumers/claude/README.md` | docs | 5684 | 95 | `a76b01dbc1bc` |  |
| `platform/network/consumers/claude/Taskfile.yml` | config | 5931 | 77 | `b47e1fec3424` |  |
| `platform/network/consumers/claude/config/authority.json` | config | 517 | 20 | `167763b0269c` | 1 |
| `platform/network/consumers/claude/config/sing-box.json` | config | 687 | 19 | `a027fd6b8264` |  |
| `platform/network/consumers/claude/ready.sh` | core | 5224 | 110 | `c71463acef0b` |  |
| `platform/network/consumers/claude/systemd/network-v2-claude-client-bridge.service` | config | 938 | 18 | `bcd1f0c18738` |  |
| `platform/network/consumers/claude/systemd/network-v2-claude-client-netns.service` | config | 1389 | 28 | `4dd6913ff430` |  |
| `platform/network/consumers/claude/systemd/network-v2-claude-client.target` | config | 357 | — | `e3c1a45af724` |  |
| `platform/network/consumers/claude/systemd/network-v2-claude-proxy.service` | config | 662 | 19 | `c17b80184522` |  |
| `platform/network/consumers/claude/systemd/network-v2-claude-relay.service` | config | 809 | 17 | `93cc251f5522` |  |
| `platform/network/consumers/claude/systemd/network-v2-claude.target` | config | 319 | — | `56361de9f266` |  |
| `platform/network/consumers/codex/PACKAGE_TOKEN_EVIDENCE.md` | docs | 2087 | 34 | `9ebeb7299b8d` |  |
| `platform/network/consumers/codex/PROGRAM_COVERAGE.md` | docs | 3128 | 65 | `b61baaa89a2c` |  |
| `platform/network/consumers/codex/README.md` | docs | 10922 | 186 | `106b033c06db` |  |
| `platform/network/consumers/codex/Taskfile.yml` | config | 1185 | 20 | `3c9aac8307d2` |  |
| `platform/network/consumers/codex/config/sing-box.json` | config | 919 | 50 | `10900aa8778d` |  |
| `platform/network/consumers/codex/ready.sh` | core | 2434 | 56 | `22b4636ae501` |  |
| `platform/network/consumers/codex/systemd/network-v2-codex-proxy.service` | config | 587 | 18 | `1cc4415cb701` |  |
| `platform/network/consumers/codex/systemd/network-v2-codex-relay.service` | config | 803 | 17 | `2d95696e3d53` |  |
| `platform/network/consumers/codex/systemd/network-v2-codex.target` | config | 307 | — | `e029b79c16f8` |  |
| `platform/network/consumers/codex/windows_exit_differential.py` | core | 4631 | 105 | `64d842f113d3` |  |
| `platform/network/consumers/codex/windows_package_program_coverage.py` | core | 7088 | 168 | `0a249a44a40b` |  |
| `platform/network/consumers/codex/windows_package_token_evidence.py` | core | 9226 | 219 | `1f4ae2ab46c0` |  |
| `platform/network/consumers/codex/windows_process_egress.py` | core | 6666 | 159 | `15bef0875c60` |  |
| `platform/network/consumers/codex/windows_wfp_evidence.py` | core | 7924 | 193 | `b9f3f29a3909` |  |
| `platform/network/consumers/developer-egress/README.md` | docs | 2752 | 51 | `ce7325ac916c` |  |
| `platform/network/consumers/developer-egress/github_release_mise.py` | core | 8627 | 217 | `6cfddb016e1c` |  |
| `platform/network/consumers/developer-egress/profile.sh` | core | 7669 | 142 | `b432232161c8` |  |
| `platform/network/consumers/discord/README.md` | docs | 268 | 5 | `7c2ede63ba44` |  |
| `platform/network/consumers/discord/Taskfile.yml` | config | 1117 | 20 | `9d13fc667906` |  |
| `platform/network/consumers/discord/config/authority.json` | config | 503 | 24 | `d3f3c1d24991` | 1 |
| `platform/network/consumers/discord/config/egress.json` | config | 850 | 47 | `3caf975de23b` |  |
| `platform/network/consumers/discord/ready.sh` | core | 2248 | 55 | `aa56a1241d3d` |  |
| `platform/network/consumers/discord/systemd/network-v2-discord-egress.service` | config | 515 | 20 | `1b86c83a35a4` |  |
| `platform/network/consumers/discord/systemd/network-v2-discord.target` | config | 179 | — | `da7aad26e14b` |  |
| `platform/network/consumers/finance/README.md` | docs | 4286 | 64 | `d2ba181c33a7` |  |
| `platform/network/consumers/finance/Taskfile.yml` | config | 4408 | 69 | `181caf00cc42` |  |
| `platform/network/consumers/finance/config/binance-spot-public-rest-authority.json` | config | 1255 | 38 | `175447f70800` | 1 |
| `platform/network/consumers/finance/config/binance-spot-public-ws-authority.json` | config | 1253 | 38 | `bf6d76d85d04` | 1 |
| `platform/network/consumers/finance/config/binance-usdm-rest-authority.json` | config | 1235 | 38 | `07f7275fa8b6` | 1 |
| `platform/network/consumers/finance/config/binance-usdm-ws-authority.json` | config | 1232 | 38 | `ce316314dd35` | 1 |
| `platform/network/consumers/finance/config/binance-wallet-rest-authority.json` | config | 1234 | 38 | `2f24d1d808b5` | 1 |
| `platform/network/consumers/finance/config/egress.json` | config | 3494 | 163 | `23f59f0f598f` |  |
| `platform/network/consumers/finance/config/fred-public-csv-authority.json` | config | 1105 | 30 | `da233f8f04c0` | 1 |
| `platform/network/consumers/finance/config/okx-rest-authority.json` | config | 1230 | 38 | `b75033fb7627` | 1 |
| `platform/network/consumers/finance/config/okx-ws-authority.json` | config | 1224 | 38 | `fa0e2d844aa8` | 1 |
| `platform/network/consumers/finance/config/us-treasury-rest-authority.json` | config | 1146 | 30 | `82ecc49f7e15` | 1 |
| `platform/network/consumers/finance/ready.sh` | core | 3819 | 87 | `f5a7b92c18db` |  |
| `platform/network/consumers/finance/systemd/network-v2-finance-egress.service` | config | 590 | 22 | `ad504b153086` |  |
| `platform/network/consumers/finance/systemd/network-v2-finance.target` | config | 182 | — | `990c95cff23c` |  |
| `platform/network/consumers/mobile-tailnet-exit/README.md` | docs | 2606 | 40 | `2a30e9527e09` |  |
| `platform/network/consumers/mobile-tailnet-exit/Taskfile.yml` | config | 1083 | 18 | `6787d7e8ec0a` |  |
| `platform/network/consumers/mobile-tailnet-exit/ready.py` | core | 4438 | 130 | `96196fe9bacf` |  |
| `platform/network/consumers/mobile-tailnet-exit/run.sh` | core | 2397 | 90 | `2e5ccdf8cb3d` |  |
| `platform/network/consumers/mobile-tailnet-exit/systemd/network-v2-mobile-tailnet-exit.service` | config | 981 | 28 | `76f80bf1caa2` |  |
| `platform/network/consumers/model-provider/README.md` | docs | 297 | 6 | `00a486baeeb0` |  |
| `platform/network/consumers/model-provider/Taskfile.yml` | config | 1271 | 20 | `32bde3d052da` |  |
| `platform/network/consumers/model-provider/config/authority.json` | config | 576 | 26 | `a5facf34b669` | 1 |
| `platform/network/consumers/model-provider/config/egress.json` | config | 902 | 45 | `c1ed3f633674` |  |
| `platform/network/consumers/model-provider/ready.sh` | core | 3120 | 75 | `c3c147ce1208` |  |
| `platform/network/consumers/model-provider/systemd/network-v2-model-provider-egress.service` | config | 531 | 20 | `04c7f7e238b3` |  |
| `platform/network/consumers/model-provider/systemd/network-v2-model-provider.target` | config | 208 | — | `1c04a75377f1` |  |
| `platform/network/consumers/supply-chain/README.md` | docs | 3261 | 44 | `1485df649d1a` |  |
| `platform/network/consumers/supply-chain/Taskfile.yml` | config | 5871 | 79 | `391ae4956f33` |  |
| `platform/network/consumers/supply-chain/acceptance/docker-rebind-smoke.sh` | core | 1538 | 28 | `5aa4af14bb9a` |  |
| `platform/network/consumers/supply-chain/config/authority.json` | config | 708 | 30 | `0d01a4dacf18` | 1 |
| `platform/network/consumers/supply-chain/config/egress.json` | config | 1090 | 55 | `c5fa529080f3` |  |
| `platform/network/consumers/supply-chain/ready.sh` | core | 2913 | 54 | `d67a54fc5229` |  |
| `platform/network/consumers/supply-chain/systemd/docker.service.d/ordivon-network-v2-supply-chain-proxy.conf` | config | 194 | 4 | `af00c8d23cb9` |  |
| `platform/network/consumers/supply-chain/systemd/network-v2-supply-chain-egress.service` | config | 607 | 22 | `86bfcb383a83` |  |
| `platform/network/consumers/supply-chain/systemd/network-v2-supply-chain.target` | config | 198 | — | `4258a5011219` |  |
| `platform/network/consumers/windows-real-chrome/README.md` | docs | 2403 | 42 | `21574ae6f8d2` |  |
| `platform/network/consumers/windows-real-chrome/Taskfile.yml` | config | 1622 | 21 | `824de01dca50` |  |
| `platform/network/consumers/windows-real-chrome/config/authority.json` | config | 519 | 24 | `fdc45e07a5bc` | 1 |
| `platform/network/consumers/windows-real-chrome/config/sing-box.json` | config | 702 | 14 | `c6157a6c004b` |  |
| `platform/network/consumers/windows-real-chrome/ready.sh` | core | 1458 | 26 | `ccaccf39a672` |  |
| `platform/network/consumers/windows-real-chrome/systemd/network-v2-windows-real-chrome-proxy.service` | config | 642 | 18 | `75aac567d167` |  |
| `platform/network/consumers/windows-real-chrome/systemd/network-v2-windows-real-chrome-relay.service` | config | 871 | 17 | `d456515cd38d` |  |
| `platform/network/consumers/windows-real-chrome/systemd/network-v2-windows-real-chrome.target` | config | 382 | — | `566bab4b365a` |  |
| `platform/network/consumers/x-reality/README.md` | docs | 1721 | 21 | `6c7c6bd36a9b` |  |
| `platform/network/consumers/x-reality/Taskfile.yml` | config | 3884 | 61 | `bd76efe9b573` |  |
| `platform/network/consumers/x-reality/config/authority.json` | config | 635 | 25 | `a7a673e5b62b` | 1 |
| `platform/network/consumers/x-reality/config/egress.json` | config | 754 | 44 | `41d330f3681d` |  |
| `platform/network/consumers/x-reality/ready.sh` | core | 1402 | 32 | `74464f2eb501` |  |
| `platform/network/consumers/x-reality/systemd/network-v2-x-reality-egress.service` | config | 523 | 18 | `edbfb73c43be` |  |
| `platform/network/consumers/x-reality/systemd/network-v2-x-reality.target` | config | 193 | — | `175228f441d4` |  |
| `platform/network/docs/ACCEPTANCE_MATRIX.md` | docs | 4550 | 92 | `5a6be0127a3a` |  |
| `platform/network/docs/AGENT_GUIDE.md` | docs | 18148 | 239 | `e38ae9fa1331` |  |
| `platform/network/docs/ARCHITECTURE.md` | docs | 10261 | 182 | `43682f300dc1` |  |
| `platform/network/docs/DECISION_MATRIX.md` | docs | 5645 | 90 | `7ac27914b4ec` |  |
| `platform/network/docs/HUMAN_GUIDE.md` | docs | 12773 | 169 | `0048d46f020e` |  |
| `platform/network/evidence/capability-matrix.json` | evidence | 1410 | 47 | `6ca09fe9dd54` | 1 |
| `platform/network/evidence/current-capabilities.json` | evidence | 1721 | 55 | `8fe14cbf42a1` | 2 |
| `platform/network/evidence/reference-linux-20260912.json` | evidence | 2355 | 47 | `5bc098008bb1` | 1 |
| `platform/network/formal/control_plane_independence.py` | core | 13711 | 302 | `02c44d942ccd` |  |
| `platform/network/formal/core_convergence_refinement.py` | core | 5468 | 119 | `27c591b7cb1b` |  |
| `platform/network/formal/dns_cache_state.py` | core | 9840 | 238 | `0d241a23e47a` |  |
| `platform/network/formal/egress_policy_refinement.py` | core | 18277 | 372 | `31a1070949eb` |  |
| `platform/network/formal/fixtures/control-plane-source-bindings.json` | config | 641 | 22 | `15b7a354da5a` | 1 |
| `platform/network/formal/shared_egress_alias_refinement.py` | core | 7754 | 160 | `f76ab7ec3963` |  |
| `platform/network/mise.toml` | config | 3886 | 74 | `9d90e05cc007` |  |
| `platform/network/planning/execution-program-r1.md` | docs | 13343 | 117 | `6883f9f8837e` |  |
| `platform/network/planning/lego-plan-r1.json` | config | 31590 | 541 | `abe75d5693b8` | 1 |
| `platform/network/providers/README.md` | docs | 228 | 3 | `ab62e021aa4c` |  |
| `platform/network/providers/gluetun/README.md` | docs | 6032 | 109 | `068c8a96956b` |  |
| `platform/network/providers/gluetun/Taskfile.yml` | config | 3569 | 48 | `205aa9c0d7ea` |  |
| `platform/network/providers/gluetun/config/carrier-adapter.json` | config | 637 | 36 | `813ab83e1789` |  |
| `platform/network/providers/gluetun/identity-exclusive.sh` | core | 1954 | 46 | `cd3b5aa6105d` |  |
| `platform/network/providers/gluetun/native_profile.py` | core | 6089 | 159 | `971eba4b2ca9` |  |
| `platform/network/providers/gluetun/quadlet/network-v2-gluetun-owned.container` | other | 1323 | — | `74eb00ebc6b8` |  |
| `platform/network/providers/gluetun/quadlet/network-v2-gluetun-owned.network` | other | 220 | — | `dba3ead91336` |  |
| `platform/network/providers/gluetun/systemd/network-v2-gluetun-owned-adapter.service` | config | 846 | 22 | `e9decaf71aaf` |  |
| `platform/network/providers/gluetun/systemd/network-v2-gluetun-owned-reconcile.service` | config | 906 | 16 | `2abbc6c1a3c6` |  |
| `platform/network/providers/gluetun/systemd/network-v2-gluetun-owned-reconcile.timer` | config | 238 | — | `ab7efab981b7` |  |
| `platform/network/providers/gluetun/systemd/network-v2-gluetun-owned.target` | config | 473 | — | `202bab7c2246` |  |
| `platform/network/providers/surfshark/README.md` | docs | 1832 | 31 | `57f46367efc1` |  |
| `platform/network/providers/surfshark/Taskfile.yml` | config | 5179 | 98 | `1973792e9e75` |  |
| `platform/network/providers/surfshark/acceptance/carrier-smoke.sh` | core | 4154 | 109 | `053343094084` |  |
| `platform/network/providers/surfshark/config/carrier.json` | config | 977 | 53 | `76e181d87b29` |  |
| `platform/network/providers/surfshark/external/gluetun-servers.lock` | config | 288 | — | `0963f741bf09` |  |
| `platform/network/providers/zte-u30pro/README.md` | docs | 2061 | 42 | `e1a8d1fa9f0c` |  |
| `platform/network/providers/zte-u30pro/Taskfile.yml` | config | 550 | 12 | `3ca4099654f4` |  |
| `platform/network/providers/zte-u30pro/observe.py` | core | 6881 | 146 | `3476d002c3b7` |  |
| `platform/network/reference/linux/README.md` | docs | 1556 | 33 | `9fbb65aa4043` |  |
| `platform/network/reference/linux/Taskfile.yml` | config | 1531 | 42 | `a883ce4169d5` |  |
| `platform/network/reference/linux/containerlab-smoke.sh` | core | 652 | 15 | `01451d691a5a` |  |
| `platform/network/reference/linux/containerlab/reference.clab.yml` | config | 198 | 11 | `db534733ca3e` |  |
| `platform/network/reference/linux/netem-smoke.sh` | core | 1155 | 18 | `9e0a9726fbee` |  |
| `platform/network/reference/linux/preflight.sh` | core | 888 | 22 | `54199223863e` |  |
| `platform/network/reference/linux/wireguard-kernel-smoke.sh` | core | 1987 | 29 | `093416e3dc88` |  |
| `platform/network/reference/linux/wireguard-userspace-smoke.sh` | core | 3238 | 101 | `8fc765159a65` |  |
| `platform/network/reference/linux/workflows/network-reference-linux.yml` | config | 774 | 25 | `bd5815e7767c` |  |
| `platform/network/scripts/capability-report.py` | core | 7438 | 164 | `75adda998f79` |  |
| `platform/network/scripts/monitoring-sourcecut-preflight.py` | core | 16048 | 336 | `0c2e85a8bf27` |  |
| `platform/network/substrates/shared-egress/README.md` | docs | 8523 | 148 | `2027bbcc3b32` |  |
| `platform/network/substrates/shared-egress/Taskfile.yml` | config | 8820 | 115 | `2c52b6fa6f39` |  |
| `platform/network/substrates/shared-egress/carrier-ready.sh` | core | 3014 | 76 | `151c8022a38c` |  |
| `platform/network/substrates/shared-egress/forward.py` | core | 4231 | 119 | `d2d89f966ecc` |  |
| `platform/network/substrates/shared-egress/netns.py` | core | 5804 | 141 | `e2bb92aa45f5` |  |
| `platform/network/substrates/shared-egress/systemd/network-v2-browserless-forward.service` | config | 889 | 18 | `83e5e4e6ec05` |  |
| `platform/network/substrates/shared-egress/systemd/network-v2-browserless-netns.service` | config | 859 | 17 | `566066caccce` |  |
| `platform/network/substrates/shared-egress/systemd/network-v2-browserless.target` | config | 490 | — | `de943f407c74` |  |
| `platform/network/systemd/network-v2-blackbox.service` | config | 492 | 20 | `9b094608ae7b` |  |
| `platform/network/systemd/network-v2-dnsproxy.service` | config | 508 | 19 | `3257e2d24e79` |  |
| `platform/network/systemd/network-v2-prometheus.service` | config | 650 | 22 | `eaeba85ec95b` |  |
| `platform/network/systemd/network-v2-r0.target` | config | 291 | — | `8a23a1f7b91a` |  |
| `platform/network/systemd/network-v2-singbox.service` | config | 563 | 22 | `acd07fb2edfa` |  |
| `platform/network/tests/test_blackbox_ip_family_contract.py` | tests | 4535 | 132 | `5c72f50eeb09` |  |
| `platform/network/tests/test_blackbox_scrape_budget_contract.py` | tests | 1521 | 38 | `8a550172432a` |  |
| `platform/network/tests/test_browserless_serial_restoration_contract.py` | tests | 3241 | 88 | `3b6ef09c7faa` |  |
| `platform/network/tests/test_capability_report_contract.py` | tests | 4498 | 111 | `ec5a1bb2f59a` |  |
| `platform/network/tests/test_chat_ingress_consumer.py` | tests | 5255 | 132 | `a679e4e33dcb` |  |
| `platform/network/tests/test_claude_egress_readiness_consumer.py` | tests | 10066 | 281 | `6cf9f8b0a482` |  |
| `platform/network/tests/test_claude_loaded_policy_cdc.py` | tests | 1825 | 48 | `8ffcb0b981bb` |  |
| `platform/network/tests/test_codex_cdn_ready_effects.py` | tests | 2471 | 81 | `f71df9efa42a` |  |
| `platform/network/tests/test_codex_mobile_tailnet_sourcecut.py` | tests | 5190 | 129 | `8c5c55884a8a` |  |
| `platform/network/tests/test_codex_windows_exit_differential.py` | tests | 4057 | 115 | `d99f85a1cddb` |  |
| `platform/network/tests/test_codex_windows_package_program_coverage.py` | tests | 4022 | 116 | `2bcedfa208ad` |  |
| `platform/network/tests/test_codex_windows_package_token_evidence.py` | tests | 2503 | 73 | `e8b20c609af2` |  |
| `platform/network/tests/test_codex_windows_process_egress.py` | tests | 7066 | 191 | `d120b2d9d6ab` |  |
| `platform/network/tests/test_codex_windows_wfp_evidence.py` | tests | 4548 | 117 | `b435cbb11715` |  |
| `platform/network/tests/test_developer_egress_profile.py` | tests | 30824 | 780 | `76e406396727` |  |
| `platform/network/tests/test_egress_routing_behavior.py` | tests | 9314 | 225 | `a156a4ab3a28` |  |
| `platform/network/tests/test_existing_lego_declaration_closure.py` | tests | 2541 | 63 | `0ba9ea709ab0` |  |
| `platform/network/tests/test_finance_public_data_business.py` | tests | 4318 | 115 | `2ca6f4953557` |  |
| `platform/network/tests/test_finance_readiness_deadline_cegar.py` | tests | 4157 | 107 | `215ae726bffb` |  |
| `platform/network/tests/test_github_release_mise.py` | tests | 5256 | 137 | `e34a6b683cfc` |  |
| `platform/network/tests/test_gluetun_native_provider.py` | tests | 3140 | 75 | `ac7a75b83442` |  |
| `platform/network/tests/test_gluetun_owned_reconcile_contract.py` | tests | 1280 | 23 | `fd655baba0f7` |  |
| `platform/network/tests/test_live_carrier_observer_continuity.py` | tests | 2438 | 86 | `f12e122bacf6` |  |
| `platform/network/tests/test_monitoring_precommit.py` | tests | 15867 | 386 | `3aaad2e95ac4` |  |
| `platform/network/tests/test_prometheus_singbox_witness.py` | tests | 6393 | 193 | `6a668583c435` |  |
| `platform/network/tests/test_readiness_shared_budget.py` | tests | 7390 | 206 | `c58f535ed321` |  |
| `platform/network/tests/test_shared_forward_lifecycle.py` | tests | 8539 | 204 | `9c9ee13f7520` |  |
| `platform/network/tests/test_shared_netns_lifecycle.py` | tests | 5268 | 127 | `87ffab8c9839` |  |
| `platform/network/tests/test_shared_provider_carrier.py` | tests | 22341 | 436 | `76bc64fa276b` |  |
| `platform/network/tests/test_supply_chain_consumer.py` | tests | 3096 | 68 | `42276531a446` |  |
| `platform/network/tests/test_x_reality_consumer.py` | tests | 4306 | 109 | `ffdee7284614` |  |
| `platform/network/tests/test_zte_u30pro_observer.py` | tests | 3088 | 88 | `9021d0944fcc` |  |

### artifact — capabilities/artifact/（425 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `capabilities/artifact/.gitignore` | other | 69 | — | `9142b6abaa86` |  |
| `capabilities/artifact/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `capabilities/artifact/MIGRATION_PROVENANCE.md` | docs | 1494 | 13 | `a68e8a81c9d6` |  |
| `capabilities/artifact/README.md` | docs | 20051 | 223 | `d6d9d9d82da6` |  |
| `capabilities/artifact/artifact-delivery/artifact-python-runtime-v1.lock.json` | config | 1797 | 37 | `7fd3a3edae5e` | 1 |
| `capabilities/artifact/artifact-delivery/build-capability-bindings-v1.json` | config | 4234 | 94 | `c416fbaf283f` | 1 |
| `capabilities/artifact/artifact-delivery/cad-toolchain-r1.lock.json` | config | 1377 | 27 | `d8cb094acc1d` | 1 |
| `capabilities/artifact/artifact-delivery/capability-bindings-v1.json` | config | 9034 | 241 | `31de5899c760` | 1 |
| `capabilities/artifact/artifact-delivery/consumer-acceptance/game-godot-production-smoke-linux-elf-r1.json` | config | 5197 | 105 | `e4544ce87c9d` | 1 |
| `capabilities/artifact/artifact-delivery/consumer-acceptance/game-station-zero-aseprite-horizontal-sheet-r1.json` | config | 6069 | 133 | `da0c50bfb6ed` | 1 |
| `capabilities/artifact/artifact-delivery/consumer-acceptance/game-station-zero-ogg-vorbis-r1.json` | config | 5622 | 110 | `8edfc8c79723` | 1 |
| `capabilities/artifact/artifact-delivery/consumer-acceptance/game-station-zero-still-image-r1.json` | config | 3159 | 83 | `cc965367b1b7` | 1 |
| `capabilities/artifact/artifact-delivery/consumer-acceptance/game-station-zero-svg-static-r1.json` | config | 5789 | 163 | `985a295d075f` | 1 |
| `capabilities/artifact/artifact-delivery/consumer-acceptance/game-station-zero-tiled-tmj-r1.json` | config | 4362 | 111 | `d2348f7f2797` | 1 |
| `capabilities/artifact/artifact-delivery/consumer-acceptance/game-veilwild-glb-material-scene-r1.json` | config | 3266 | 81 | `9410bd9757d6` | 1 |
| `capabilities/artifact/artifact-delivery/consumer-acceptance/game-veilwild-glb-skinned-animation-r1.json` | config | 3427 | 89 | `1d856434a5d0` | 1 |
| `capabilities/artifact/artifact-delivery/consumer-acceptance/game-veilwild-wave-pcm16-r1.json` | config | 3534 | 87 | `a334723c6315` | 1 |
| `capabilities/artifact/artifact-delivery/examples/document-r1.json` | config | 1016 | 26 | `a7fd567d7231` |  |
| `capabilities/artifact/artifact-delivery/examples/pdf-accessible-r1.json` | config | 861 | 23 | `decb7bc5a71c` |  |
| `capabilities/artifact/artifact-delivery/examples/pdf-fixed-r1.json` | config | 789 | 22 | `7e5464cf7d16` |  |
| `capabilities/artifact/artifact-delivery/examples/pdu-sdu-presentation-r1.json` | config | 2255 | 93 | `a47be4b7d609` |  |
| `capabilities/artifact/artifact-delivery/examples/presentation-local-development-r1.json` | config | 2115 | 76 | `ade7f3ffc0e6` |  |
| `capabilities/artifact/artifact-delivery/examples/presentation-local-development-request-r1.json` | config | 1180 | 25 | `98d77f744cd5` | 1 |
| `capabilities/artifact/artifact-delivery/examples/presentation-local-development-source-r1.json` | config | 2546 | 95 | `385b16c6f199` | 1 |
| `capabilities/artifact/artifact-delivery/examples/presentation-native-smoke-request-r1.json` | config | 935 | 23 | `be320c25221d` | 1 |
| `capabilities/artifact/artifact-delivery/examples/presentation-native-smoke-source-r1.json` | config | 2176 | 72 | `11622f07b1d7` | 1 |
| `capabilities/artifact/artifact-delivery/examples/presentation-ultrawide-34x10-r1.json` | config | 2338 | 93 | `56cf5879e529` |  |
| `capabilities/artifact/artifact-delivery/examples/spreadsheet-r1.json` | config | 876 | 24 | `d9fea8e20691` |  |
| `capabilities/artifact/artifact-delivery/examples/web-r1.json` | config | 988 | 27 | `a31a76e6ddba` |  |
| `capabilities/artifact/artifact-delivery/examples/web-smoke-request-r1.json` | config | 836 | 23 | `f9870360ee52` | 1 |
| `capabilities/artifact/artifact-delivery/examples/web-smoke-source-r1.html` | other | 422 | — | `9fcb20d6ab25` |  |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-acceptance-lineage-r1.json` | config | 4577 | 91 | `ae93e1186883` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-acceptance-r2.json` | config | 5788 | 122 | `04b1baa82c01` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-deck-migration-evidence-r1.json` | config | 8648 | 224 | `7bb6a2723cae` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-deck-reference-map-r1.json` | config | 3655 | 105 | `a883a9e42bde` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-deck-semantic-overlay-r1.json` | config | 49756 | 1858 | `5ed264937da8` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-determinism-evidence-r1.json` | config | 4796 | 97 | `9fb348ab93e3` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-opc-member-projection-r2.json` | config | 2324 | 66 | `731c667823cc` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-runtime-input-set-r1.json` | config | 2984 | 65 | `9f3784e57ba9` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-runtime-package-input-set-r2.json` | config | 1148 | 25 | `a8b00ee07b45` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-slide01-migration-evidence-r1.json` | config | 2066 | 40 | `ceb9ba535d09` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-slide01-reference-map-r1.json` | config | 1335 | 29 | `4dd27859defb` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-slide01-semantic-overlay-r1.json` | config | 4834 | 163 | `9e258e1ce5ad` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-r1-font-repair.json` | config | 2093 | 43 | `bdcb8ca5d4f8` | 1 |
| `capabilities/artifact/artifact-delivery/golden/pdu-sdu-r1.manifest.json` | config | 6527 | 124 | `05609b054e2b` |  |
| `capabilities/artifact/artifact-delivery/mise.toml` | config | 74 | 5 | `ce054b6aaf79` |  |
| `capabilities/artifact/artifact-delivery/node/package.json` | config | 548 | 20 | `97ff3186cc50` |  |
| `capabilities/artifact/artifact-delivery/node/pnpm-lock.yaml` | config | 32147 | 863 | `19fe8a4d2074` |  |
| `capabilities/artifact/artifact-delivery/node/pnpm-workspace.yaml` | config | 32 | 2 | `644a280ae7c8` |  |
| `capabilities/artifact/artifact-delivery/node/probe.mjs` | core | 3914 | 93 | `7a1d02e294ed` |  |
| `capabilities/artifact/artifact-delivery/node/verify_ogg_vorbis.mjs` | core | 3063 | 66 | `625d68271de3` |  |
| `capabilities/artifact/artifact-delivery/node/verify_svg_static.mjs` | core | 2266 | 12 | `295075d21af5` |  |
| `capabilities/artifact/artifact-delivery/opc-member-projection-v1.schema.json` | schemas | 1571 | 42 | `62dc90f28b3e` |  |
| `capabilities/artifact/artifact-delivery/openxml-assurance-fault-taxonomy-v1.json` | config | 2258 | 62 | `d3487de4b70c` | 1 |
| `capabilities/artifact/artifact-delivery/openxml-assurance-method-v1.json` | config | 3040 | 72 | `7cf020c17e80` | 1 |
| `capabilities/artifact/artifact-delivery/openxml-external-evidence-r1.json` | config | 4267 | 108 | `d6a768bbeed2` | 1 |
| `capabilities/artifact/artifact-delivery/openxml-nix/flake.lock` | config | 634 | — | `125de19e7c11` |  |
| `capabilities/artifact/artifact-delivery/openxml-nix/flake.nix` | other | 403 | — | `a903e4af076a` |  |
| `capabilities/artifact/artifact-delivery/openxml-runtime-v1.lock.json` | config | 1986 | 50 | `af9a733369b7` | 1 |
| `capabilities/artifact/artifact-delivery/openxml-validator/ArtifactOpenXmlValidator.csproj` | other | 398 | — | `afdc96204d9b` |  |
| `capabilities/artifact/artifact-delivery/openxml-validator/Program.cs` | core | 3011 | 85 | `e39adcb8ac7d` |  |
| `capabilities/artifact/artifact-delivery/policy/release.rego` | core | 483 | 23 | `0af8b4bfb79b` |  |
| `capabilities/artifact/artifact-delivery/ppt-master-provider-v1.lock.json` | config | 694 | 15 | `59447b22e1cb` | 1 |
| `capabilities/artifact/artifact-delivery/presentation-semantic-svg-source-v1.schema.json` | schemas | 2256 | 54 | `bdd8d6c9cd76` |  |
| `capabilities/artifact/artifact-delivery/presentation-source-v1.schema.json` | schemas | 7686 | 340 | `3b51bf194a77` |  |
| `capabilities/artifact/artifact-delivery/profile-v1.schema.json` | schemas | 5728 | 166 | `0b20a8f87279` |  |
| `capabilities/artifact/artifact-delivery/profile-v2.shadow.schema.json` | schemas | 5742 | 275 | `5e9f77c7dbd8` |  |
| `capabilities/artifact/artifact-delivery/python-uv/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `capabilities/artifact/artifact-delivery/python-uv/pyproject.toml` | config | 599 | 26 | `60091c8a3909` |  |
| `capabilities/artifact/artifact-delivery/python-uv/uv.lock` | config | 43202 | — | `6713ec63628e` |  |
| `capabilities/artifact/artifact-delivery/r2-mailbox-v1.schema.json` | schemas | 1550 | 72 | `03cd6adefda8` |  |
| `capabilities/artifact/artifact-delivery/request-v1.schema.json` | schemas | 2436 | 69 | `9dc6b17349a7` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/audio-flac-pcm16-local-r1.json` | config | 2024 | 42 | `175de2b8bfb8` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/audio-ogg-vorbis-local-r1.json` | config | 3678 | 84 | `f1209059526a` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/audio-wave-pcm16-local-r1.json` | config | 2149 | 52 | `4ea543345258` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/cad-step-solid-local-r1.json` | config | 1826 | 31 | `e45766f50a71` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/dataset-parquet-flat-local-r1.json` | config | 1886 | 41 | `fededb2eeefc` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/design-2d-aseprite-local-r1.json` | config | 2478 | 55 | `828a47f6cd95` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/design-2d-tiled-tmj-local-r1.json` | config | 1736 | 46 | `e1a9132fb35a` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/design-3d-glb-material-scene-local-r1.json` | config | 2176 | 50 | `1692381138b1` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/design-3d-glb-skinned-animation-local-r1.json` | config | 2182 | 50 | `9c34b81a82ef` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/design-3d-glb-static-mesh-local-r1.json` | config | 2118 | 45 | `bd55ee05a6ca` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/eda-kicad-pcb-local-r1.json` | config | 1113 | 24 | `b34f0b6ac589` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/eda-spice-transient-local-r1.json` | config | 943 | 15 | `a9f874bebcf0` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/geospatial-geopackage-point-local-r1.json` | config | 2271 | 46 | `25e1c9987262` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/message-internet-text-local-r1.json` | config | 1397 | 31 | `34aa3bf3f320` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/moving-image-matroska-ffv1-local-r1.json` | config | 2400 | 43 | `c4e4630fc697` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/software-release-linux-elf-executable-local-r1.json` | config | 1763 | 41 | `995b4ce1b411` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/software-release-oci-image-local-r1.json` | config | 3321 | 56 | `d627bb7f168a` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/still-image-png-srgb-local-r1.json` | config | 1836 | 47 | `738098ee19c8` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/still-image-svg-static-local-r1.json` | config | 3324 | 82 | `b9212f4786c0` |  |
| `capabilities/artifact/artifact-delivery/shadow-bindings/web-archive-warc-response-local-r1.json` | config | 1770 | 37 | `96d4034f3c6c` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/audio-flac-contract-v1.schema.json` | schemas | 932 | 25 | `14c83f23057c` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/audio-flac-pcm16-smoke-r1.json` | config | 457 | 13 | `ce1937415837` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/audio-ogg-vorbis-contract-v1.schema.json` | schemas | 918 | 24 | `d34599c2ba13` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/audio-wave-pcm16-contract-v1.schema.json` | schemas | 933 | 25 | `2e42b34523b0` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/audio-wave-pcm16-game-smoke-r1.json` | config | 313 | 12 | `e6995a6b9588` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/cad-step-solid-contract-v1.schema.json` | schemas | 1784 | 94 | `f4f4e7775310` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/dataset-contract-v1.schema.json` | schemas | 1173 | 35 | `55d3247b777c` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/dataset-parquet-flat-smoke-r1.json` | config | 554 | 14 | `cff99d653c31` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/design-2d-aseprite-sheet-contract-v1.schema.json` | schemas | 1403 | 30 | `304f81f676e7` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/design-2d-tiled-tmj-contract-v1.schema.json` | schemas | 1341 | 30 | `475eaa064a20` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/design-3d-glb-contract-v1.schema.json` | schemas | 1203 | 27 | `9785851d8980` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/design-3d-glb-material-scene-contract-v1.schema.json` | schemas | 6421 | 295 | `aecec1c9b6df` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/design-3d-glb-material-scene-game-smoke-r1.json` | config | 1432 | 65 | `fa0f232af86b` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/design-3d-glb-skinned-animation-contract-v1.schema.json` | schemas | 6427 | 295 | `7621e0cad095` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/design-3d-glb-skinned-animation-game-smoke-r1.json` | config | 1960 | 88 | `4393ba14f8de` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/design-3d-glb-static-mesh-smoke-r1.json` | config | 374 | 15 | `84e89e968f1b` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/eda-kicad-pcb-contract-v1.schema.json` | schemas | 1472 | 41 | `8507dd696f62` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/eda-spice-transient-measure-contract-v1.schema.json` | schemas | 808 | 23 | `2784b4761398` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/game-station-zero-expression-aseprite-sheet-r1.json` | config | 772 | 18 | `c71c060f3682` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/game-station-zero-ogg-vorbis-r1/aftermath.json` | config | 391 | 12 | `3ee5651ee34f` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/game-station-zero-ogg-vorbis-r1/commit.json` | config | 387 | 12 | `fea6d868d17d` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/game-station-zero-ogg-vorbis-r1/plan-ready.json` | config | 392 | 12 | `0f5e5666d492` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/game-station-zero-specialists-aseprite-sheet-r1.json` | config | 782 | 18 | `5177f83fadc6` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/game-station-zero-tiled-tmj-r1.json` | config | 595 | 18 | `b6a8501fbe10` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/geospatial-geopackage-point-smoke-r1.json` | config | 680 | 23 | `44ae64878963` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/geospatial-vector-contract-v1.schema.json` | schemas | 2262 | 62 | `451653bd1921` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/message-internet-text-contract-v1.schema.json` | schemas | 1262 | 36 | `98b13b9f260e` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/message-internet-text-smoke-r1.json` | config | 565 | 14 | `2a437c57dd47` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/moving-image-ffv1-contract-v1.schema.json` | schemas | 1445 | 37 | `d2280229c8f0` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/moving-image-matroska-ffv1-smoke-r1.json` | config | 614 | 17 | `973d0912694d` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/software-release-linux-elf-contract-v1.schema.json` | schemas | 3093 | 147 | `e44cac8a9f47` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/software-release-linux-elf-game-godot-smoke-r1.json` | config | 1086 | 29 | `0d4ec42c2e9a` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/software-release-oci-contract-v1.schema.json` | schemas | 2740 | 79 | `59c41b38be83` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/software-release-oci-image-smoke-r1.json` | config | 964 | 33 | `47a44e330657` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/web-archive-warc-response-contract-v1.schema.json` | schemas | 1089 | 26 | `d45d798347d0` |  |
| `capabilities/artifact/artifact-delivery/shadow-contracts/web-archive-warc-response-smoke-r1.json` | config | 527 | 14 | `04de0d5a9788` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/audio-flac-pcm16-r1.json` | config | 2812 | 71 | `9f76c2867e86` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/audio-ogg-vorbis-r1.json` | config | 3260 | 51 | `11d8df24266f` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/audio-wave-pcm16-r1.json` | config | 2414 | 46 | `3420d6e580ef` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/dataset-parquet-flat-r1.json` | config | 2421 | 72 | `447a7d273860` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/design-2d-aseprite-horizontal-sheet-r1.json` | config | 2751 | 47 | `46bd86160893` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/design-2d-tiled-tmj-object-map-r1.json` | config | 2742 | 50 | `12c00ace4983` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/design-3d-glb-material-scene-r1.json` | config | 2500 | 74 | `7a9c2375b64f` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/design-3d-glb-skinned-animation-r1.json` | config | 2724 | 76 | `ccfde3093aaf` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/design-3d-glb-static-mesh-r1.json` | config | 2534 | 56 | `d26a7f310105` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/design-3d-step-solid-r1.json` | config | 2207 | 59 | `1adbd0a46d21` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/eda-kicad-pcb-gerber-r1.json` | config | 2118 | 43 | `b33fb96f156e` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/eda-spice-transient-measure-r1.json` | config | 1771 | 28 | `f87b7408b979` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/geospatial-geopackage-point-r1.json` | config | 3001 | 73 | `faa37988b8b6` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/message-internet-text-r1.json` | config | 2318 | 54 | `5939308deb4e` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/moving-image-matroska-ffv1-v3-r1.json` | config | 3511 | 77 | `8c9437698810` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/software-release-linux-elf-executable-r1.json` | config | 2977 | 63 | `bd2998fab97f` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/software-release-oci-image-r1.json` | config | 3630 | 54 | `793491f8c7dc` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/still-image-png-srgb-r1.json` | config | 2169 | 55 | `879709b64576` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/still-image-svg-static-r1.json` | config | 2639 | 39 | `23d614606ae4` |  |
| `capabilities/artifact/artifact-delivery/shadow-profiles/web-archive-warc-response-r1.json` | config | 1998 | 50 | `4c8e63ac2edb` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/audio-flac-pcm16-r1-v2.json` | config | 3507 | 117 | `b3fbf1d76b1f` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/audio-ogg-vorbis-r1-v2.json` | config | 3949 | 100 | `d6082289083c` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/audio-wave-pcm16-r1-v2.json` | config | 3089 | 92 | `36cad5be83d2` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/dataset-parquet-flat-r1-v2.json` | config | 2982 | 96 | `0a8560cefb02` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/design-2d-aseprite-horizontal-sheet-r1-v2.json` | config | 3336 | 87 | `284f7333b139` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/design-2d-tiled-tmj-object-map-r1-v2.json` | config | 3376 | 98 | `9852ae811fc6` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/design-3d-glb-material-scene-r1-v2.json` | config | 2948 | 95 | `d665df89577f` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/design-3d-glb-skinned-animation-r1-v2.json` | config | 3174 | 97 | `b8b76f2cb8ab` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/design-3d-glb-static-mesh-r1-v2.json` | config | 3098 | 95 | `f9dfe8b3e43b` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/design-3d-step-solid-r1-v2.json` | config | 2661 | 80 | `8d0f5a005846` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/document-r1-v2.json` | config | 2644 | 103 | `62225db571a9` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/eda-kicad-pcb-gerber-r1-v2.json` | config | 2713 | 86 | `69ce758dcb60` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/eda-spice-transient-measure-r1-v2.json` | config | 2346 | 76 | `f6f3e03264de` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/geospatial-geopackage-point-r1-v2.json` | config | 3483 | 97 | `296d80c933cf` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/message-internet-text-r1-v2.json` | config | 3116 | 112 | `fb89af3563ed` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/moving-image-matroska-ffv1-v3-r1-v2.json` | config | 3982 | 101 | `db3bd84caddf` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/pdf-accessible-r1-v2.json` | config | 2108 | 88 | `1363cc727010` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/pdf-fixed-r1-v2.json` | config | 1928 | 81 | `9f95922b3140` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/pdu-sdu-presentation-r1-v2.json` | config | 3752 | 145 | `c2bc333b7ee7` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/presentation-local-development-r1-v2.json` | config | 3524 | 127 | `ccac5dd0428e` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/presentation-ultrawide-34x10-r1-v2.json` | config | 3835 | 145 | `c2f3171b1a1a` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/software-release-linux-elf-executable-r1-v2.json` | config | 3494 | 85 | `40ad66d62e5e` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/software-release-oci-image-r1-v2.json` | config | 4345 | 105 | `5f50452f3860` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/spreadsheet-r1-v2.json` | config | 2289 | 89 | `6636a2a855b3` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/still-image-png-srgb-r1-v2.json` | config | 2824 | 95 | `833743589a66` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/still-image-svg-static-r1-v2.json` | config | 3508 | 112 | `6626826a1744` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/web-archive-warc-response-r1-v2.json` | config | 2638 | 93 | `f214642543d8` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/examples/web-r1-v2.json` | config | 2303 | 96 | `f6540f64651b` |  |
| `capabilities/artifact/artifact-delivery/shadow-v2/profile-v2-mapping-manifest-r1.json` | config | 15076 | 302 | `ddd5bdf6f1d9` | 1 |
| `capabilities/artifact/artifact-delivery/sigstore-local-signing-config-v1.json` | config | 148 | 7 | `04d748f6caff` |  |
| `capabilities/artifact/artifact-delivery/taxonomy-v1.json` | config | 15479 | 555 | `96295a7ab174` | 1 |
| `capabilities/artifact/artifact-delivery/toolchain-r1.lock.json` | config | 1333 | 36 | `48ed1301a31d` |  |
| `capabilities/artifact/artifact-delivery/toolchain-v1.lock.json` | config | 4188 | 96 | `ae94e4c5bed3` | 1 |
| `capabilities/artifact/artifact-delivery/toolchain-v1.plan.json` | config | 6218 | 78 | `3a694272e20a` | 1 |
| `capabilities/artifact/artifact-delivery/verification/request-v1.schema.json` | schemas | 1939 | 51 | `c53e2f3aa1bf` |  |
| `capabilities/artifact/artifact-delivery/vsa-trust-policy-v1.schema.json` | schemas | 2275 | 67 | `530ce56a04f8` |  |
| `capabilities/artifact/artifact_capabilities/__init__.py` | core | 47 | 1 | `d0c1fb154d02` |  |
| `capabilities/artifact/artifact_capabilities/dispatch.py` | core | 1205 | 34 | `462ac8f8ae2d` |  |
| `capabilities/artifact/artifact_capabilities/document.py` | core | 2265 | 64 | `07a6c0c60cf6` |  |
| `capabilities/artifact/artifact_capabilities/passthrough.py` | core | 683 | 20 | `c425c45736c0` |  |
| `capabilities/artifact/artifact_capabilities/presentation/__init__.py` | core | 1035 | 31 | `75eaccbe7847` |  |
| `capabilities/artifact/artifact_capabilities/presentation/admission.py` | core | 2040 | 50 | `22de8a5abf6b` |  |
| `capabilities/artifact/artifact_capabilities/presentation/canonicalization.py` | core | 12596 | 250 | `cc04ea0ccbb5` |  |
| `capabilities/artifact/artifact_capabilities/presentation/common.py` | core | 12576 | 264 | `e6346a277ee7` |  |
| `capabilities/artifact/artifact_capabilities/presentation/ppt_master.py` | core | 10950 | 244 | `af28354f6a7f` |  |
| `capabilities/artifact/artifact_capabilities/presentation/python_pptx.py` | core | 11252 | 213 | `87604ad362eb` |  |
| `capabilities/artifact/artifact_capabilities/presentation/reference_projection.py` | core | 14777 | 321 | `72ecffb89949` |  |
| `capabilities/artifact/artifact_capabilities/publication/__init__.py` | core | 1497 | 52 | `167fc595bd3a` |  |
| `capabilities/artifact/artifact_capabilities/publication/attestation.py` | core | 2342 | 65 | `95817532ba46` |  |
| `capabilities/artifact/artifact_capabilities/publication/contract.py` | core | 12639 | 321 | `fdf285d5125e` |  |
| `capabilities/artifact/artifact_capabilities/publication/geometry.py` | core | 3026 | 91 | `51a483976cc2` |  |
| `capabilities/artifact/artifact_capabilities/publication/inventory.py` | core | 2293 | 69 | `7c553f9335bd` |  |
| `capabilities/artifact/artifact_capabilities/publication/observer_task.py` | core | 4615 | 133 | `ee3b628cb8f5` |  |
| `capabilities/artifact/artifact_capabilities/publication/perceptual.py` | core | 13136 | 326 | `29fe0888ed92` |  |
| `capabilities/artifact/artifact_capabilities/publication/probe.py` | core | 4183 | 132 | `e808f82d0826` |  |
| `capabilities/artifact/artifact_capabilities/publication/provider_adapter.py` | core | 10882 | 265 | `e807658a31a7` |  |
| `capabilities/artifact/artifact_capabilities/publication/semantic_layout.py` | core | 2701 | 81 | `79501d6b89b0` |  |
| `capabilities/artifact/artifact_capabilities/publication/visual.py` | core | 8793 | 247 | `33e8a2a729b9` |  |
| `capabilities/artifact/artifact_core/__init__.py` | core | 497 | 17 | `8f6392fe2984` |  |
| `capabilities/artifact/artifact_core/admission.py` | core | 5440 | 112 | `9a993c4ea8cd` |  |
| `capabilities/artifact/artifact_core/bindings.py` | core | 4181 | 96 | `893807d2f539` |  |
| `capabilities/artifact/artifact_core/build_bindings.py` | core | 2786 | 65 | `a21b8f5d97e2` |  |
| `capabilities/artifact/artifact_core/build_planning.py` | core | 2906 | 58 | `0fa0dbb60414` |  |
| `capabilities/artifact/artifact_core/contracts.py` | core | 2264 | 77 | `e78bc59de4bd` |  |
| `capabilities/artifact/artifact_core/input_snapshot.py` | core | 2348 | 63 | `04f6ccae792d` |  |
| `capabilities/artifact/artifact_core/json_validation.py` | core | 3311 | 97 | `3899080c3786` |  |
| `capabilities/artifact/artifact_core/profile_refinement.py` | core | 3180 | 88 | `e78c5f0f5f21` |  |
| `capabilities/artifact/artifact_core/profile_v1.py` | core | 777 | 23 | `4ec94f19b0c7` |  |
| `capabilities/artifact/artifact_core/profiles.py` | core | 6191 | 146 | `2d58ee55a7a5` |  |
| `capabilities/artifact/artifact_evidence/__init__.py` | core | 154 | 5 | `8b1549b34c4a` |  |
| `capabilities/artifact/artifact_evidence/delivery.py` | core | 8699 | 158 | `caeccf9bf8cc` |  |
| `capabilities/artifact/artifact_evidence/snapshot.py` | core | 677 | 24 | `d350196e74d3` |  |
| `capabilities/artifact/artifact_operations/__init__.py` | core | 666 | 24 | `6a8f8b2ea128` |  |
| `capabilities/artifact/artifact_operations/contract.py` | core | 4558 | 109 | `f6518c721905` |  |
| `capabilities/artifact/artifact_operations/executor.py` | core | 1181 | 34 | `ff80a172dbba` |  |
| `capabilities/artifact/artifact_operations/providers/__init__.py` | core | 172 | 7 | `d815791f7cad` |  |
| `capabilities/artifact/artifact_operations/providers/common.py` | core | 209 | 10 | `058d31ed64a0` |  |
| `capabilities/artifact/artifact_operations/providers/direct_python.py` | core | 24357 | 606 | `8a946b181261` |  |
| `capabilities/artifact/artifact_operations/providers/oci_toolchain.py` | core | 3450 | 101 | `1e9ed2110611` |  |
| `capabilities/artifact/artifact_operations/receipt.py` | core | 8335 | 200 | `76cab6bd67ac` |  |
| `capabilities/artifact/artifact_trust/__init__.py` | core | 59 | 1 | `edcb98ffbdd0` |  |
| `capabilities/artifact/artifact_trust/cosign_toolchain.py` | core | 11347 | 286 | `4f0a5cecf020` |  |
| `capabilities/artifact/artifact_trust/provenance.py` | core | 3561 | 90 | `1ee450f12467` |  |
| `capabilities/artifact/artifact_trust/sigstore_bundle.py` | core | 3947 | 90 | `45320cd752a3` |  |
| `capabilities/artifact/artifact_trust/trust_policy.py` | core | 7375 | 135 | `023374ceb103` |  |
| `capabilities/artifact/artifact_trust/verification_summary.py` | core | 5968 | 125 | `2297ea8b9f35` |  |
| `capabilities/artifact/artifact_trust/vsa.py` | core | 13751 | 321 | `c61e1d3e14e7` |  |
| `capabilities/artifact/artifact_verification/__init__.py` | core | 204 | 8 | `2da778ea48cb` |  |
| `capabilities/artifact/artifact_verification/claim_coverage.py` | core | 5180 | 128 | `14c93806303b` |  |
| `capabilities/artifact/artifact_verification/evidence.py` | core | 1716 | 56 | `18712a67dfa0` |  |
| `capabilities/artifact/artifact_verification/formal/verify_claim_coverage.py` | core | 7011 | 174 | `0da31f5c16c5` |  |
| `capabilities/artifact/artifact_verification/formal/verify_native_identity.py` | core | 3926 | 108 | `9e13070e2317` |  |
| `capabilities/artifact/artifact_verification/formal/verify_profile_refinement.py` | core | 3985 | 105 | `8dc10363d0fe` |  |
| `capabilities/artifact/artifact_verification/native_identity.py` | core | 3187 | 83 | `4ffd15f51d76` |  |
| `capabilities/artifact/artifact_verification/stage.py` | core | 14032 | 378 | `072e2abcc0e2` |  |
| `capabilities/artifact/artifact_verification/tool_identity.py` | core | 3099 | 77 | `d4cf65e17217` |  |
| `capabilities/artifact/artifact_verifiers/__init__.py` | core | 53 | 1 | `e3a24705d383` |  |
| `capabilities/artifact/artifact_verifiers/document/__init__.py` | core | 272 | 8 | `8f08e5a8a043` |  |
| `capabilities/artifact/artifact_verifiers/document/dependencies.py` | core | 5488 | 147 | `d1ac0b1013a1` |  |
| `capabilities/artifact/artifact_verifiers/document/semantics.py` | core | 8420 | 230 | `0edace005d2d` |  |
| `capabilities/artifact/artifact_verifiers/document/toolchain.py` | core | 698 | 20 | `4886048e003a` |  |
| `capabilities/artifact/artifact_verifiers/openxml/__init__.py` | core | 241 | 8 | `591b01f6e9f6` |  |
| `capabilities/artifact/artifact_verifiers/openxml/toolchain.py` | core | 383 | 13 | `71906041d193` |  |
| `capabilities/artifact/artifact_verifiers/openxml/validator.py` | core | 1497 | 53 | `d0962a77462c` |  |
| `capabilities/artifact/artifact_verifiers/pdf/__init__.py` | core | 316 | 11 | `7dbc61779065` |  |
| `capabilities/artifact/artifact_verifiers/pdf/conformance.py` | core | 2447 | 74 | `997fffe27b93` |  |
| `capabilities/artifact/artifact_verifiers/pdf/structural.py` | core | 1234 | 43 | `3d0ce3173929` |  |
| `capabilities/artifact/artifact_verifiers/pdf/toolchain.py` | core | 660 | 22 | `dd8d94e4d1b7` |  |
| `capabilities/artifact/artifact_verifiers/presentation/__init__.py` | core | 381 | 12 | `4c78351727c7` |  |
| `capabilities/artifact/artifact_verifiers/presentation/gate.py` | core | 5360 | 168 | `60c3a4ede3c1` |  |
| `capabilities/artifact/artifact_verifiers/presentation/inspection.py` | core | 9547 | 239 | `6cb56030ce71` |  |
| `capabilities/artifact/artifact_verifiers/presentation/semantics.py` | core | 3779 | 98 | `829d48e5a760` |  |
| `capabilities/artifact/artifact_verifiers/web/__init__.py` | core | 400 | 19 | `3c05ce82a610` |  |
| `capabilities/artifact/artifact_verifiers/web/browser.py` | core | 2121 | 73 | `c741afcec9d9` |  |
| `capabilities/artifact/artifact_verifiers/web/conformance.py` | core | 2076 | 67 | `a275fccc5981` |  |
| `capabilities/artifact/artifact_verifiers/web/node/verify_html.mjs` | core | 3580 | 105 | `8a0e29d3a7b0` |  |
| `capabilities/artifact/artifact_verifiers/web/toolchain.py` | core | 1217 | 39 | `590ed38794d7` |  |
| `capabilities/artifact/config/artifact-r2-mailbox-r1.json` | config | 915 | 33 | `b09e0ac2f1ba` | 1 |
| `capabilities/artifact/config/zot/local-registry-r1.json` | config | 342 | 20 | `5ca8131f6096` |  |
| `capabilities/artifact/docs/ARTIFACT_CAD_ADMISSION_BOUNDARY_R1.md` | docs | 1556 | 26 | `b54a6a755b55` |  |
| `capabilities/artifact/docs/ARTIFACT_CAPABILITY_DECOMPOSITION_WAVE_A15_R1.md` | docs | 7307 | 231 | `30e023929683` |  |
| `capabilities/artifact/docs/ARTIFACT_CLAIM_COVERAGE_FORMAL_R1.md` | docs | 8575 | 104 | `08aeb2e37ddb` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_AUDIO_OGG_VORBIS_R1.md` | docs | 2131 | 32 | `35ff3108672c` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_AUDIO_R1.md` | docs | 5468 | 161 | `58f38c842b00` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_AUDIO_WAVE_PCM16_R1.md` | docs | 2044 | 27 | `24137c3d8f25` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_DATASET_R1.md` | docs | 8226 | 204 | `b920894817c7` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_DESIGN_2D_ASEPRITE_R1.md` | docs | 2786 | 28 | `4dc688cd1972` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_DESIGN_2D_TILED_R1.md` | docs | 2288 | 29 | `78a303e4a928` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_DESIGN_3D_R1.md` | docs | 7423 | 194 | `011fddebbdfc` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_EDA_R1.md` | docs | 2090 | 30 | `cd89a78180c9` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_GEOSPATIAL_R1.md` | docs | 7180 | 184 | `c4ac3bb05338` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_MESSAGE_R1.md` | docs | 3457 | 102 | `8b3917d084a8` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_MOVING_IMAGE_R1.md` | docs | 5917 | 164 | `972f8a922a51` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_SOFTWARE_RELEASE_ELF_R1.md` | docs | 2743 | 57 | `8479d267cf6d` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_SOFTWARE_RELEASE_R1.md` | docs | 7080 | 203 | `0a3de7814a59` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_STILL_IMAGE_R1.md` | docs | 7368 | 139 | `12f42cb060f8` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_STILL_IMAGE_SVG_R1.md` | docs | 1725 | 23 | `c508eb0700cf` |  |
| `capabilities/artifact/docs/ARTIFACT_FAMILY_WEB_ARCHIVE_R1.md` | docs | 2411 | 62 | `5090405f3b9c` |  |
| `capabilities/artifact/docs/ARTIFACT_PROFILE_AUTHORITY_REFINEMENT_R1.md` | docs | 3743 | 69 | `9ceedf1aa6c4` |  |
| `capabilities/artifact/docs/ARTIFACT_R2_S1B_CLAIM_RESULTS_PRESSURE_R1.md` | docs | 3156 | 82 | `4036cc986f01` |  |
| `capabilities/artifact/docs/ARTIFACT_R2_S1_EVALUATION_PRESSURE_R1.md` | docs | 4761 | 140 | `8d6953a9d304` |  |
| `capabilities/artifact/docs/ARTIFACT_REDECOMPOSITION_R1.md` | docs | 15159 | 432 | `53bd26466141` |  |
| `capabilities/artifact/docs/ARTIFACT_VERIFICATION_SERVICE_R1.md` | docs | 4126 | 61 | `6f9a5998664d` |  |
| `capabilities/artifact/docs/SOURCE_AUTHORITY_ACCEPTANCE_20260912.md` | docs | 8596 | 140 | `245f2a04dd6a` |  |
| `capabilities/artifact/docs/artifact-build-delivery-e2e-authoring-orchestration-v1.md` | docs | 19101 | 210 | `b56e7337f205` |  |
| `capabilities/artifact/docs/artifact-build-delivery-e2e-toolchain-v1.md` | docs | 11831 | 60 | `5c2adca8f7c6` |  |
| `capabilities/artifact/docs/artifact-build-delivery-e2e-v1.md` | docs | 6773 | 59 | `d41cfcf56e52` |  |
| `capabilities/artifact/mise.toml` | config | 3249 | 42 | `2d29c0485e1a` |  |
| `capabilities/artifact/planning/claim-results-adapter-pressure-r1.json` | config | 1694 | 46 | `65cf6eaf87d4` | 1 |
| `capabilities/artifact/planning/evaluation-model-pressure-r1.json` | config | 15208 | 398 | `f63c711d6896` | 1 |
| `capabilities/artifact/planning/evidence-standing-pressure-r1.json` | config | 11793 | 315 | `eef21438632d` | 1 |
| `capabilities/artifact/planning/lego-plan-r2.json` | config | 19695 | 579 | `75417ebee36b` | 2 |
| `capabilities/artifact/planning/prototypes/claim_results_adapter_r1.py` | core | 6462 | 196 | `7fffcd720a82` |  |
| `capabilities/artifact/planning/prototypes/evidence_observation_r1.py` | core | 12596 | 298 | `002b4bc32159` |  |
| `capabilities/artifact/planning/prototypes/standing_decision_r1.py` | core | 5146 | 139 | `95c7b3ed3c3e` |  |
| `capabilities/artifact/planning/prototypes/verifier_plugin_contract_r2.py` | core | 2719 | 61 | `b941ab4e0b4f` |  |
| `capabilities/artifact/planning/standing-decision-pressure-r1.json` | config | 2496 | 47 | `cbadb2695494` | 1 |
| `capabilities/artifact/planning/verifier-plugin-result-r2-candidate.schema.json` | schemas | 3738 | 171 | `24e2f3e342c9` |  |
| `capabilities/artifact/pyproject.toml` | config | 1101 | 50 | `1c5a799657c2` |  |
| `capabilities/artifact/scripts/artifact_agent_surface.py` | core | 20933 | 390 | `637eea6f38f0` |  |
| `capabilities/artifact/scripts/artifact_aseprite.py` | core | 8164 | 68 | `97327dd1b2f6` |  |
| `capabilities/artifact/scripts/artifact_audio.py` | core | 15836 | 294 | `107881b392e1` |  |
| `capabilities/artifact/scripts/artifact_cad_step.py` | core | 8830 | 104 | `6a63cf523520` |  |
| `capabilities/artifact/scripts/artifact_dataset.py` | core | 16376 | 309 | `815772088be2` |  |
| `capabilities/artifact/scripts/artifact_deliver_html.py` | core | 10242 | 239 | `23adafc70d71` |  |
| `capabilities/artifact/scripts/artifact_delivery_toolchain_doctor.py` | core | 29423 | 641 | `229514854808` |  |
| `capabilities/artifact/scripts/artifact_design3d.py` | core | 14581 | 135 | `91473aa713b8` |  |
| `capabilities/artifact/scripts/artifact_eda.py` | core | 10273 | 201 | `dd9b5faf0091` |  |
| `capabilities/artifact/scripts/artifact_geospatial.py` | core | 21023 | 352 | `73f88be4bedc` |  |
| `capabilities/artifact/scripts/artifact_message.py` | core | 8549 | 95 | `89626081cc60` |  |
| `capabilities/artifact/scripts/artifact_moving_image.py` | core | 16483 | 241 | `ba6ad7795644` |  |
| `capabilities/artifact/scripts/artifact_oci_package.py` | core | 26047 | 637 | `c58f9a1efa6b` |  |
| `capabilities/artifact/scripts/artifact_ogg_vorbis.py` | core | 13715 | 132 | `e28b7d2c1996` |  |
| `capabilities/artifact/scripts/artifact_openxml_dotnet_wrapper.py` | core | 933 | 19 | `1c83d32b0a76` |  |
| `capabilities/artifact/scripts/artifact_openxml_environment.py` | core | 16232 | 218 | `3557efb98af0` |  |
| `capabilities/artifact/scripts/artifact_openxml_external_evidence.py` | core | 10993 | 227 | `0a3c8466668b` |  |
| `capabilities/artifact/scripts/artifact_openxml_validator_wrapper.py` | core | 1963 | 41 | `21fe2d57f50e` |  |
| `capabilities/artifact/scripts/artifact_profile_v2.py` | core | 10954 | 250 | `a44a9f3f7172` |  |
| `capabilities/artifact/scripts/artifact_python_environment.py` | core | 13559 | 209 | `4e4fdbd152f2` |  |
| `capabilities/artifact/scripts/artifact_python_wrapper.py` | core | 4059 | 67 | `4d08a173aa9b` |  |
| `capabilities/artifact/scripts/artifact_r2_mailbox.py` | core | 23779 | 520 | `3bf2c1d6b402` |  |
| `capabilities/artifact/scripts/artifact_registry_doctor.py` | core | 9667 | 213 | `2456c2e10cb9` |  |
| `capabilities/artifact/scripts/artifact_software_release.py` | core | 15957 | 218 | `3e10b500be79` |  |
| `capabilities/artifact/scripts/artifact_software_release_elf.py` | core | 9095 | 84 | `dd9881527b79` |  |
| `capabilities/artifact/scripts/artifact_spice.py` | core | 7340 | 147 | `20277c51a2f6` |  |
| `capabilities/artifact/scripts/artifact_still_image.py` | core | 13974 | 281 | `0e2860621f32` |  |
| `capabilities/artifact/scripts/artifact_svg.py` | core | 9638 | 94 | `7591d485ce1d` |  |
| `capabilities/artifact/scripts/artifact_temporal_deploy.py` | core | 4286 | 76 | `19466ba16339` |  |
| `capabilities/artifact/scripts/artifact_temporal_launch.py` | core | 2606 | 37 | `99937744e8b8` |  |
| `capabilities/artifact/scripts/artifact_temporal_support.py` | core | 3056 | 85 | `6d5ec7f6dfd0` |  |
| `capabilities/artifact/scripts/artifact_temporal_worker.py` | core | 668 | 15 | `26661e66fb2e` |  |
| `capabilities/artifact/scripts/artifact_temporal_workflow.py` | core | 5846 | 63 | `0e1a962b5225` |  |
| `capabilities/artifact/scripts/artifact_tiled.py` | core | 10403 | 101 | `d0d1628c49c4` |  |
| `capabilities/artifact/scripts/artifact_verify.py` | core | 17236 | 342 | `cfb70a4d29d8` |  |
| `capabilities/artifact/scripts/artifact_wave.py` | core | 11621 | 130 | `1b2dc9f93521` |  |
| `capabilities/artifact/scripts/artifact_web_archive.py` | core | 7016 | 77 | `6b50a834a284` |  |
| `capabilities/artifact/scripts/cad_step_inspect.cpp` | other | 2471 | — | `923d8f71f529` |  |
| `capabilities/artifact/scripts/powerpoint_render_worker.ps1` | core | 8421 | 178 | `b35c5255d703` |  |
| `capabilities/artifact/scripts/publication_carrier_verify.py` | core | 1430 | 42 | `ad873153780e` |  |
| `capabilities/artifact/scripts/publication_perceptual_probe.py` | core | 5427 | 146 | `731bc43ab566` |  |
| `capabilities/artifact/scripts/publication_perceptual_provider_exec.py` | core | 3400 | 98 | `cf5c50b3877a` |  |
| `capabilities/artifact/scripts/publication_perceptual_verify.py` | core | 2673 | 69 | `80adf5a420e8` |  |
| `capabilities/artifact/systemd/ordivon-artifact-temporal-worker.service` | config | 1254 | 36 | `f7306bf4ffa1` |  |
| `capabilities/artifact/systemd/ordivon-artifact-v2-zot-r1.container` | other | 597 | — | `b8070d738ff8` |  |
| `capabilities/artifact/tests/fixtures/cad/block-through-hole-contract.json` | tests | 373 | 21 | `2e4fd7277aa9` | 1 |
| `capabilities/artifact/tests/fixtures/cad/block-through-hole.step` | tests | 8298 | — | `69f28ed1740b` |  |
| `capabilities/artifact/tests/test_artifact_agent_surface.py` | tests | 6439 | 109 | `1ae07e111b1f` |  |
| `capabilities/artifact/tests/test_artifact_aseprite.py` | tests | 3918 | 41 | `2aab78e701b6` |  |
| `capabilities/artifact/tests/test_artifact_audio.py` | tests | 11345 | 205 | `59ef2d9579b5` |  |
| `capabilities/artifact/tests/test_artifact_binding_authority.py` | tests | 7055 | 149 | `037a4e4e7faf` |  |
| `capabilities/artifact/tests/test_artifact_cad_step.py` | tests | 2037 | 23 | `2bd9a1daffb3` |  |
| `capabilities/artifact/tests/test_artifact_claim_results_adapter_r1.py` | tests | 13165 | 327 | `e86aac0b9ef5` |  |
| `capabilities/artifact/tests/test_artifact_consumer_acceptance.py` | tests | 14198 | 297 | `62bf4dd028d6` |  |
| `capabilities/artifact/tests/test_artifact_core_registry.py` | tests | 4655 | 95 | `9c4d9334321f` |  |
| `capabilities/artifact/tests/test_artifact_dataset.py` | tests | 5687 | 118 | `c94d4a3f4462` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a10.py` | tests | 2231 | 62 | `0c71db2b111f` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a11.py` | tests | 1908 | 47 | `735dba95c636` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a12.py` | tests | 4089 | 96 | `2dc758ed1370` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a13.py` | tests | 4137 | 98 | `6d8711d86bd0` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a15.py` | tests | 2941 | 72 | `0ad89b327b50` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a2.py` | tests | 5476 | 115 | `e171c51d239d` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a3.py` | tests | 3296 | 82 | `99eac73cf800` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a4.py` | tests | 1844 | 41 | `cceb1315ddcd` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a5.py` | tests | 2469 | 58 | `27cdfb26d6fb` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a6.py` | tests | 2410 | 60 | `33a81e5bb062` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a7.py` | tests | 2006 | 51 | `1d7d4de8c9a2` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a8.py` | tests | 1551 | 45 | `f913c591baf3` |  |
| `capabilities/artifact/tests/test_artifact_decomposition_a9.py` | tests | 2136 | 55 | `1c60ee146eeb` |  |
| `capabilities/artifact/tests/test_artifact_deliver_html.py` | tests | 6295 | 151 | `5f98de9276d5` |  |
| `capabilities/artifact/tests/test_artifact_delivery.py` | tests | 121114 | 2125 | `12fc23c0bdc3` |  |
| `capabilities/artifact/tests/test_artifact_delivery_toolchain_doctor.py` | tests | 1903 | 47 | `cb600bf2ab4d` |  |
| `capabilities/artifact/tests/test_artifact_design3d.py` | tests | 5530 | 70 | `6d25a8e121af` |  |
| `capabilities/artifact/tests/test_artifact_development_fixture.py` | tests | 2060 | 37 | `9fccfba55f3c` |  |
| `capabilities/artifact/tests/test_artifact_eda.py` | tests | 4103 | 72 | `ab5b8125e6d0` |  |
| `capabilities/artifact/tests/test_artifact_evaluation_pressure_r1.py` | tests | 4274 | 109 | `93b32bdcb8b6` |  |
| `capabilities/artifact/tests/test_artifact_evidence_observation_lossless_r1.py` | tests | 14725 | 354 | `9d961bcf2afb` |  |
| `capabilities/artifact/tests/test_artifact_evidence_standing_pressure_r1.py` | tests | 3337 | 82 | `d126c9962611` |  |
| `capabilities/artifact/tests/test_artifact_geospatial.py` | tests | 6586 | 116 | `d473c7676d6c` |  |
| `capabilities/artifact/tests/test_artifact_input_snapshot.py` | tests | 8608 | 168 | `384f42bb1bde` |  |
| `capabilities/artifact/tests/test_artifact_legacy_digest_consumers.py` | tests | 2754 | 81 | `03448d3fcae4` |  |
| `capabilities/artifact/tests/test_artifact_message.py` | tests | 3245 | 35 | `a2cb91ca131d` |  |
| `capabilities/artifact/tests/test_artifact_moving_image.py` | tests | 7673 | 121 | `2d579a189bf2` |  |
| `capabilities/artifact/tests/test_artifact_native_identity.py` | tests | 8845 | 195 | `a7e8553fee20` |  |
| `capabilities/artifact/tests/test_artifact_oci_package.py` | tests | 10902 | 206 | `a079467144f7` |  |
| `capabilities/artifact/tests/test_artifact_oci_toolchain.py` | tests | 3673 | 96 | `1c7ec8f2c02b` |  |
| `capabilities/artifact/tests/test_artifact_ogg_vorbis.py` | tests | 3403 | 43 | `c525da358622` |  |
| `capabilities/artifact/tests/test_artifact_opc_projection.py` | tests | 13303 | 245 | `9f09ca7bfcdc` |  |
| `capabilities/artifact/tests/test_artifact_openxml_assurance.py` | tests | 6271 | 71 | `ace8dfb9f7f0` |  |
| `capabilities/artifact/tests/test_artifact_openxml_environment.py` | tests | 11163 | 186 | `713a0de9f7aa` |  |
| `capabilities/artifact/tests/test_artifact_openxml_external_evidence.py` | tests | 3068 | 83 | `02d5278d8cc5` |  |
| `capabilities/artifact/tests/test_artifact_operation_receipt_contract_r1.py` | tests | 4548 | 122 | `e2a5b0775093` |  |
| `capabilities/artifact/tests/test_artifact_profile_authority.py` | tests | 8576 | 173 | `8c4a587487a7` |  |
| `capabilities/artifact/tests/test_artifact_profile_v2.py` | tests | 18120 | 261 | `c42eff798d9a` |  |
| `capabilities/artifact/tests/test_artifact_publication_carrier_r1.py` | tests | 8736 | 221 | `669f8a0a9515` |  |
| `capabilities/artifact/tests/test_artifact_publication_geometry_semantic_r1.py` | tests | 2279 | 57 | `f4b62ee31a0a` |  |
| `capabilities/artifact/tests/test_artifact_publication_observer_task_r1.py` | tests | 5462 | 120 | `e092b1533e3e` |  |
| `capabilities/artifact/tests/test_artifact_publication_perceptual_r1.py` | tests | 18833 | 486 | `e364b2a3ab06` |  |
| `capabilities/artifact/tests/test_artifact_publication_provider_adapter_r1.py` | tests | 20896 | 495 | `743fa8c49499` |  |
| `capabilities/artifact/tests/test_artifact_python_currentness_contract.py` | tests | 2110 | 61 | `fbf9063e90a7` |  |
| `capabilities/artifact/tests/test_artifact_python_environment.py` | tests | 9998 | 155 | `429d0f32a8f4` |  |
| `capabilities/artifact/tests/test_artifact_r2_mailbox.py` | tests | 14364 | 171 | `c09628050c3d` |  |
| `capabilities/artifact/tests/test_artifact_redecomposition_r1.py` | tests | 7551 | 161 | `4ae3873411fb` |  |
| `capabilities/artifact/tests/test_artifact_registry_doctor.py` | tests | 803 | 21 | `c0eeb03377ef` |  |
| `capabilities/artifact/tests/test_artifact_software_release.py` | tests | 8779 | 101 | `d548868ef346` |  |
| `capabilities/artifact/tests/test_artifact_software_release_elf.py` | tests | 5743 | 87 | `d01be87e95fc` |  |
| `capabilities/artifact/tests/test_artifact_spice.py` | tests | 2691 | 52 | `6934b2e39a28` |  |
| `capabilities/artifact/tests/test_artifact_stage_missing_validator.py` | tests | 2234 | 47 | `533dde8b4b96` |  |
| `capabilities/artifact/tests/test_artifact_standing_decision_pressure_r1.py` | tests | 8272 | 222 | `67bd89338c78` |  |
| `capabilities/artifact/tests/test_artifact_still_image.py` | tests | 3792 | 84 | `17ba9e17000f` |  |
| `capabilities/artifact/tests/test_artifact_svg.py` | tests | 3040 | 32 | `3da57e6385cc` |  |
| `capabilities/artifact/tests/test_artifact_temporal_contract.py` | tests | 14361 | 167 | `40293d7efbac` |  |
| `capabilities/artifact/tests/test_artifact_tiled.py` | tests | 4341 | 45 | `c372be6f5b53` |  |
| `capabilities/artifact/tests/test_artifact_tool_identity.py` | tests | 2613 | 60 | `c72995b8fbb0` |  |
| `capabilities/artifact/tests/test_artifact_verify.py` | tests | 29503 | 520 | `0f135b0dc9a4` |  |
| `capabilities/artifact/tests/test_artifact_wave.py` | tests | 3552 | 47 | `4c2f2beeeb9b` |  |
| `capabilities/artifact/tests/test_artifact_web_archive.py` | tests | 3926 | 48 | `aa0564f9cd6a` |  |
| `capabilities/artifact/uv.lock` | config | 54805 | — | `ad14d9a13610` |  |

### distribution — capabilities/distribution/（30 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `capabilities/distribution/.gitignore` | other | 26 | — | `472f568478bf` |  |
| `capabilities/distribution/README.md` | docs | 3244 | 64 | `e8f433b9af3a` |  |
| `capabilities/distribution/adapters/openapi-generator.json` | config | 498 | 9 | `114698658c6b` | 1 |
| `capabilities/distribution/adapters/postiz.json` | config | 573 | 11 | `0048af8523eb` | 1 |
| `capabilities/distribution/adapters/rclone.json` | config | 458 | 10 | `40de1448a05f` | 1 |
| `capabilities/distribution/docs/R8-DURABLE-INTEGRATION-PORT.md` | docs | 1512 | 22 | `cbb205a0976f` |  |
| `capabilities/distribution/evidence/r1-validation-20260911.json` | evidence | 1504 | 24 | `247c8fe13604` | 1 |
| `capabilities/distribution/evidence/r10-game-steam-free-preflight-20260913.json` | evidence | 3491 | 86 | `e642488a643b` | 1 |
| `capabilities/distribution/evidence/r2-github-public-read-envelope.json` | evidence | 1349 | 37 | `07388f5a897c` | 2 |
| `capabilities/distribution/evidence/r2-github-public-read-source.json` | evidence | 1015 | 27 | `eb648e137450` | 1 |
| `capabilities/distribution/evidence/r2-validation-20260911.json` | evidence | 2085 | 46 | `d42ffc8ca872` | 1 |
| `capabilities/distribution/evidence/r3-github-create-issue-intent.json` | evidence | 604 | 18 | `73f760400d2b` | 2 |
| `capabilities/distribution/evidence/r3-validation-20260911.json` | evidence | 3403 | 64 | `a00f67521120` | 1 |
| `capabilities/distribution/evidence/r4-github-create-issue-approval-request.json` | evidence | 531 | 12 | `1d73d28d1636` | 1 |
| `capabilities/distribution/evidence/r4-validation-20260912.json` | evidence | 3278 | 59 | `20f296f4c51b` | 1 |
| `capabilities/distribution/evidence/r5-carrier-coverage-20260912.json` | evidence | 3071 | 68 | `d5de57e8e6e2` | 1 |
| `capabilities/distribution/evidence/r6-validation-20260912.json` | evidence | 1999 | 43 | `a225863db0c6` | 1 |
| `capabilities/distribution/evidence/r7-artifact-development-publication-intent.json` | evidence | 890 | 24 | `9ad725105c95` | 2 |
| `capabilities/distribution/evidence/r7-validation-20260912.json` | evidence | 1441 | 23 | `56cc907d3ed9` | 1 |
| `capabilities/distribution/evidence/r8-validation-20260912.json` | evidence | 1731 | 36 | `91d73f8dd582` | 1 |
| `capabilities/distribution/evidence/r9-write-admission-20260912.json` | evidence | 713 | 18 | `9e35ca2ba383` | 1 |
| `capabilities/distribution/external-lock.json` | config | 2031 | 56 | `6b2d5dc4e5a3` | 1 |
| `capabilities/distribution/mise.toml` | config | 160 | 9 | `13ef9770824c` |  |
| `capabilities/distribution/scripts/test-external-carriers.sh` | core | 278 | 8 | `93f4de900b09` |  |
| `capabilities/distribution/scripts/test-github-provider-readback.sh` | core | 909 | 17 | `92973aab1457` |  |
| `capabilities/distribution/scripts/test-openapi-generator.sh` | core | 579 | 13 | `6c1c156f3803` |  |
| `capabilities/distribution/scripts/test-postiz-surface.sh` | core | 595 | 20 | `44083c7a9913` |  |
| `capabilities/distribution/scripts/test-rclone.sh` | core | 515 | 12 | `428bd23525cb` |  |
| `capabilities/distribution/scripts/test-structure.sh` | core | 931 | 21 | `f740764e5b83` |  |
| `capabilities/distribution/tests/fixtures/provider-openapi.yaml` | tests | 647 | 27 | `7d7bd70c7998` |  |

### media — capabilities/media/（553 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `capabilities/media/.env.example` | other | 284 | — | `d8daa2688fa5` |  |
| `capabilities/media/.gitignore` | other | 390 | — | `f85f289822c8` |  |
| `capabilities/media/.node-version` | other | 7 | — | `5ac3fee983df` |  |
| `capabilities/media/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `capabilities/media/AGENTS.md` | docs | 18365 | 242 | `889ab84ce05c` |  |
| `capabilities/media/LICENSE` | other | 11357 | — | `c71d239df917` |  |
| `capabilities/media/MEDIA.md` | docs | 5212 | 73 | `5fc52277750f` |  |
| `capabilities/media/README.md` | docs | 18554 | 277 | `dc6d2fb95ef4` |  |
| `capabilities/media/STUDIO.md` | docs | 11442 | 162 | `6459f9e333d8` |  |
| `capabilities/media/apps/motion-remotion/package.json` | config | 1058 | 25 | `5221e4f54b1b` |  |
| `capabilities/media/apps/motion-remotion/remotion.config.ts` | core | 2077 | 58 | `83131edf051c` |  |
| `capabilities/media/apps/motion-remotion/src/exact-close-composition.tsx` | core | 4044 | 66 | `79b1451e22cf` |  |
| `capabilities/media/apps/motion-remotion/src/game-station-zero-affect-expression.tsx` | core | 6726 | 86 | `3573c7db5d01` |  |
| `capabilities/media/apps/motion-remotion/src/index.ts` | core | 117 | 4 | `e0331fa6d5d8` |  |
| `capabilities/media/apps/motion-remotion/src/request-replay-composition.tsx` | core | 4709 | 85 | `397275d1e34f` |  |
| `capabilities/media/apps/motion-remotion/src/root.tsx` | core | 1802 | 22 | `5f336cf78e74` |  |
| `capabilities/media/apps/motion-remotion/src/runtime-demo-receipt.ts` | core | 1870 | 74 | `d36582d81c12` |  |
| `capabilities/media/apps/motion-remotion/src/runtime-flow-composition.tsx` | core | 1942 | 49 | `115605d6d95a` |  |
| `capabilities/media/apps/motion-remotion/src/runtime-introduction-master-composition.tsx` | core | 12463 | 212 | `213a0b58fa49` |  |
| `capabilities/media/apps/motion-remotion/src/runtime-response-loss-expression.tsx` | core | 6829 | 86 | `eddb4bf31267` |  |
| `capabilities/media/apps/motion-remotion/src/security-ae0-epistemic-expression.tsx` | core | 9665 | 117 | `008a55166456` |  |
| `capabilities/media/apps/motion-remotion/tsconfig.json` | config | 179 | 7 | `02ded6d69886` |  |
| `capabilities/media/apps/preview/index.html` | other | 357 | — | `5011e1f480e4` |  |
| `capabilities/media/apps/preview/package.json` | config | 476 | 22 | `f9c34958e93f` |  |
| `capabilities/media/apps/preview/src/app.tsx` | core | 3646 | 96 | `38e7562a9c2c` |  |
| `capabilities/media/apps/preview/src/main.tsx` | core | 337 | 14 | `5b62b0c8e8ef` |  |
| `capabilities/media/apps/preview/src/styles.css` | other | 4194 | — | `15bb3bb284f5` |  |
| `capabilities/media/apps/preview/vite.config.ts` | core | 192 | 11 | `aa752f015da9` |  |
| `capabilities/media/artifacts/creative-archive/historical-works-r2-source-complete.json` | config | 212310 | 5638 | `57f28aedbf07` |  |
| `capabilities/media/artifacts/creative-library/catalog-v1.json` | config | 1676103 | 44243 | `56bc6240f46d` | 1 |
| `capabilities/media/artifacts/creative-library/derived/cad-cross-work-derived-preview-r1.json` | config | 1753 | 27 | `a181e83bb0f1` | 1 |
| `capabilities/media/artifacts/creative-library/derived/game--look-away-garden.png` | media | 105469 | — | `f9ac2b3fb7ad` |  |
| `capabilities/media/artifacts/creative-library/derived/game--seen-not-approved-pcb.svg` | media | 16061 | — | `9f0e08b90665` |  |
| `capabilities/media/artifacts/creative-library/derived/game--signal-garden-evidence-petals.png` | media | 226028 | — | `b9adf5f2942c` |  |
| `capabilities/media/artifacts/creative-library/derived/game--three-color-night-shift.png` | media | 180106 | — | `d0fbfcb6a57c` |  |
| `capabilities/media/artifacts/creative-library/derived/godot-derived-previews-r1.json` | config | 14071 | 184 | `e534edfabc00` | 1 |
| `capabilities/media/artifacts/creative-library/derived/kicad-derived-preview-r1.json` | config | 2172 | 38 | `67928b015307` | 1 |
| `capabilities/media/artifacts/creative-library/derived/manifest-v1.json` | config | 2860 | 55 | `89ff8a7a4acf` | 1 |
| `capabilities/media/artifacts/creative-library/derived/media--alignment-field.png` | media | 87528 | — | `f2e652a2cd1a` |  |
| `capabilities/media/artifacts/creative-library/derived/workstation--signal-garden-cam-encoder.png` | media | 143734 | — | `014c0da6e1e1` |  |
| `capabilities/media/artifacts/creative-library/evidence/acceptance-r1.json` | evidence | 2964 | 59 | `6ba8a1f3e327` | 1 |
| `capabilities/media/artifacts/creative-library/evidence/acceptance-r2.json` | evidence | 3858 | 81 | `0954c9fb0a6e` | 1 |
| `capabilities/media/artifacts/creative-library/evidence/friction-glb-presentation-kind-r1.json` | evidence | 1197 | 15 | `3ae2a613aed6` | 1 |
| `capabilities/media/artifacts/creative-library/evidence/home.png` | media | 183624 | — | `e87c8f0a31a4` |  |
| `capabilities/media/creative-library/README.md` | docs | 5003 | 95 | `0e069c823c79` |  |
| `capabilities/media/creative-library/SOURCE_BOUNDARY.json` | config | 1062 | 31 | `ef72fd4c0d28` | 1 |
| `capabilities/media/creative-library/web/app.js` | core | 7936 | 99 | `5396b1fdf06f` |  |
| `capabilities/media/creative-library/web/index.html` | other | 2339 | — | `26458af14003` |  |
| `capabilities/media/creative-library/web/styles.css` | other | 8096 | — | `51d11ee801a5` |  |
| `capabilities/media/docs/artifact-perception.md` | docs | 8374 | 163 | `958542c004e8` |  |
| `capabilities/media/docs/authority.md` | docs | 5113 | 54 | `e4d9d63e4c82` |  |
| `capabilities/media/docs/capability-reference.md` | docs | 9896 | 93 | `da3fca8e1445` |  |
| `capabilities/media/docs/creative-capability-core.md` | docs | 5130 | 84 | `4477ed54e70a` |  |
| `capabilities/media/docs/directory-audit.md` | docs | 30154 | 363 | `2427ed5f4bee` |  |
| `capabilities/media/docs/fast-inner-loop.md` | docs | 5534 | 103 | `de9f400643f4` |  |
| `capabilities/media/docs/human-guide.md` | docs | 15958 | 244 | `bdf5bb4c286a` |  |
| `capabilities/media/docs/media-model.md` | docs | 7226 | 148 | `b2768d3c9560` |  |
| `capabilities/media/docs/production-cognition.md` | docs | 3094 | 65 | `c30aab4c5ca8` |  |
| `capabilities/media/docs/resolve-compatibility/resolve-free-21.0.3.7.json` | config | 3063 | 102 | `99a668e92b1f` | 1 |
| `capabilities/media/docs/resolve-compatibility/resolve-free-21.0.3.7.md` | docs | 3576 | 74 | `90cf524aa56a` |  |
| `capabilities/media/docs/resolve-compatibility/runtime-introduction-assembly-conform-21.0.3.7.json` | config | 2712 | 57 | `bdb7f1afbcfe` | 1 |
| `capabilities/media/docs/resolve-native.md` | docs | 11745 | 173 | `faffcd43542e` |  |
| `capabilities/media/docs/review-consumption.md` | docs | 4960 | 129 | `c75664e4a5d1` |  |
| `capabilities/media/docs/storage-layout.md` | docs | 6499 | 121 | `daa40b8c0a11` |  |
| `capabilities/media/docs/technical-baseline.md` | docs | 6138 | 102 | `f5416e7d9eb1` |  |
| `capabilities/media/formal/CreativeLibraryAcceptance.lean` | core | 2698 | 81 | `14234e414f59` |  |
| `capabilities/media/formal/LoudnessProfileSafety.smt2` | other | 1647 | — | `ebe50eb887e2` |  |
| `capabilities/media/formal/MediaNativeProcessingAdmission.lean` | core | 4104 | 114 | `b45f34ada10f` |  |
| `capabilities/media/formal/ProductionDependencyImpact.lean` | core | 3476 | 105 | `5768a50d7dd3` |  |
| `capabilities/media/formal/ProductionOutputByteIdentity.lean` | core | 2111 | 58 | `06053a75329a` |  |
| `capabilities/media/formal/README.md` | docs | 12042 | 217 | `d7c4d4a93291` |  |
| `capabilities/media/mise.toml` | config | 647 | 25 | `4c0f9527e5cf` |  |
| `capabilities/media/package.json` | config | 8169 | 71 | `315af114d0f4` |  |
| `capabilities/media/packages/identity/package.json` | config | 230 | 11 | `e539d6089215` |  |
| `capabilities/media/packages/identity/scripts/build-tokens.ts` | core | 4066 | 87 | `0132cec75da1` |  |
| `capabilities/media/packages/identity/tokens/baseline.tokens.json` | config | 2403 | 43 | `2924a4e29d2f` |  |
| `capabilities/media/packages/visuals/package.json` | config | 261 | 15 | `34c4c181a9c0` |  |
| `capabilities/media/packages/visuals/src/index.ts` | core | 105 | 1 | `5a0455022671` |  |
| `capabilities/media/packages/visuals/src/runtime-flow.tsx` | core | 3390 | 84 | `2ba883af857c` |  |
| `capabilities/media/planning/lego-plan-r1.json` | config | 73714 | 1671 | `9a274bc9644d` | 1 |
| `capabilities/media/play/media-ecology-20260830/README.md` | docs | 2478 | 37 | `f55d4532bec9` |  |
| `capabilities/media/play/media-ecology-20260830/board-snapshot.json` | config | 4311 | 65 | `ddcb39e85a7f` | 1 |
| `capabilities/media/play/media-ecology-20260830/browser-check.py` | core | 3360 | 98 | `16433164499a` |  |
| `capabilities/media/play/media-ecology-20260830/build.py` | core | 13465 | 284 | `2c402ac1714e` |  |
| `capabilities/media/play/media-ecology-20260830/daily-cabinet.collection.json` | config | 3617 | 98 | `7af5c1e669ca` | 1 |
| `capabilities/media/play/media-ecology-20260830/projection.json` | config | 7894 | 189 | `582679e669c3` | 1 |
| `capabilities/media/pnpm-lock.yaml` | config | 120271 | 3559 | `f8b67152cae0` |  |
| `capabilities/media/pnpm-workspace.yaml` | config | 134 | 9 | `5e53bd366271` |  |
| `capabilities/media/processing/README.md` | docs | 3768 | 68 | `384a08460b31` |  |
| `capabilities/media/processing/bin/otiotool-pinned.sh` | core | 178 | 4 | `c57b825d6fc1` |  |
| `capabilities/media/processing/bin/probe-audio.sh` | core | 5156 | 123 | `e133c6f16508` |  |
| `capabilities/media/processing/bin/probe-av.sh` | core | 4125 | 89 | `4175dc512982` |  |
| `capabilities/media/processing/bin/probe-otio.sh` | core | 5200 | 114 | `af451d9351de` |  |
| `capabilities/media/processing/bin/probe-timed-text.sh` | core | 5046 | 119 | `aa242fe20a99` |  |
| `capabilities/media/processing/bin/ttconv-pinned.sh` | core | 163 | 4 | `ad7f3a93d5f3` |  |
| `capabilities/media/processing/profiles/audio-program-48k-mono-lufs23.json` | config | 420 | 19 | `b84daa8b4dbb` | 1 |
| `capabilities/media/processing/profiles/av-sdr-web-1080p30-noaudio.json` | config | 416 | 20 | `f64cd28a359d` | 1 |
| `capabilities/media/processing/profiles/otio-runtime-introduction-v2.json` | config | 430 | 14 | `f13a21117a97` | 1 |
| `capabilities/media/processing/profiles/timed-text-runtime-introduction-en.json` | config | 282 | 11 | `475dcd4456d1` | 1 |
| `capabilities/media/processing/tests/audio-smoke.sh` | tests | 2428 | 49 | `8d0c36907c90` |  |
| `capabilities/media/processing/tests/otio-smoke.sh` | tests | 2846 | 69 | `96c7c20bf3dc` |  |
| `capabilities/media/processing/tests/smoke.sh` | tests | 1517 | 38 | `d133b720a629` |  |
| `capabilities/media/processing/tests/test_processing_tool_resolution.py` | tests | 3364 | 84 | `8135ec32b911` |  |
| `capabilities/media/processing/tests/timedtext-smoke.sh` | tests | 2839 | 76 | `c36fdd27de66` |  |
| `capabilities/media/productions/archive-archipelago-001/README.md` | docs | 2497 | 25 | `b46ce0f5aae8` |  |
| `capabilities/media/productions/archive-archipelago-001/build.sh` | core | 837 | 14 | `2090ec9091be` |  |
| `capabilities/media/productions/archive-archipelago-001/build_interactive.py` | core | 635 | 14 | `81a396e6308a` |  |
| `capabilities/media/productions/archive-archipelago-001/claims.json` | config | 1826 | 38 | `a9434e7ca740` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/artifact-browser-matrix-r2.json` | evidence | 1632 | 43 | `e96fe55c1b2b` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/artifact-browser-matrix-r3.json` | evidence | 1632 | 43 | `bd82c5ca1a14` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/artifact-browser-matrix-r4.json` | evidence | 1632 | 43 | `c2ea8b62fa10` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/artifact-vnu-r2.json` | evidence | 967 | 23 | `f8fc91408b78` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/artifact-vnu-r3.json` | evidence | 967 | 23 | `bfd8e02a9552` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/artifact-vnu-r4.json` | evidence | 967 | 23 | `3b19f97d6902` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/chromium-console-keyboard-r3.json` | evidence | 63 | 3 | `4867b51a8296` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/chromium-console-mobile-r2.json` | evidence | 63 | 3 | `4867b51a8296` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/chromium-console-r2.json` | evidence | 63 | 3 | `4867b51a8296` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/chromium-console-touch-r4.json` | evidence | 63 | 3 | `4867b51a8296` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/chromium-final-console-r2.json` | evidence | 63 | 3 | `4867b51a8296` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/chromium-final-interaction-r2.json` | evidence | 191 | 3 | `55c4652cf1d7` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/chromium-interaction-r2.json` | evidence | 214 | 3 | `5ebc6e2ff170` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/chromium-mobile-pan-r2.json` | evidence | 212 | 3 | `546014933579` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/collaboration-polish-r2.json` | evidence | 3314 | 57 | `50e3a0ea653a` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/consumption-evidence.json` | evidence | 5549 | 96 | `c2148ea4ff77` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/friction-gpkg-determinism.json` | evidence | 1746 | 24 | `9b5faa643e6b` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/friction-interactive-accessibility.json` | evidence | 2080 | 27 | `f05799bc7bdf` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/friction-interactive-html-conformance.json` | evidence | 1766 | 27 | `6e36fe2725f1` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/friction-interactive-keyboard-focus.json` | evidence | 2380 | 29 | `1bf56ced020c` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/friction-interactive-mobile-density.json` | evidence | 1914 | 24 | `1ad8d56963ef` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/friction-interactive-svg-append.json` | evidence | 1896 | 27 | `1e7ad4077fd2` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/friction-interactive-touch-targets.json` | evidence | 2693 | 29 | `600778b4065b` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/friction-playwright-config-cli.json` | evidence | 2175 | 24 | `9457a8014697` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/friction-production-schema.json` | schemas | 1814 | 24 | `2022d9b42636` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/friction.json` | evidence | 2013 | 28 | `daf65523cef4` | 1 |
| `capabilities/media/productions/archive-archipelago-001/evidence/keyboard-focus-baseline-r3.json` | evidence | 99 | 3 | `3ebcfff386b5` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/keyboard-focus-verified-r3.json` | evidence | 205 | 3 | `a738c2c8751f` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/touch-accessibility-gates-r4.json` | evidence | 853 | 3 | `f240873211cf` |  |
| `capabilities/media/productions/archive-archipelago-001/evidence/touch-target-baseline-r4.json` | evidence | 633 | 3 | `1cf848777acd` |  |
| `capabilities/media/productions/archive-archipelago-001/generate.py` | core | 12530 | 171 | `a127bf1fa748` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/app.js` | core | 7060 | 13 | `60c3994df00b` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/archive-archipelago-001.html` | other | 142059 | — | `54e8269a1125` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/chromium-desktop-final-r2.png` | media | 402598 | — | `30916d0d57b6` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/chromium-keyboard-search-r3.png` | media | 443332 | — | `48766d596752` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/chromium-mobile-final-r2.png` | media | 233596 | — | `276040efe2da` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/chromium-mobile-r2.png` | media | 229250 | — | `14325c082fac` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/chromium-mobile-r2b.png` | media | 199087 | — | `82788f3eb575` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/chromium-mobile-search-r3.png` | media | 276123 | — | `1741b3b76ded` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/chromium-touch-r4-final.png` | media | 194428 | — | `f03d091f0e5f` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/data.js` | core | 124784 | 1 | `7cccfb0ea46c` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/index.html` | other | 3725 | — | `dcfb9857f90c` |  |
| `capabilities/media/productions/archive-archipelago-001/interactive/styles.css` | other | 6539 | — | `e3d438348ef5` |  |
| `capabilities/media/productions/archive-archipelago-001/production.json` | config | 3838 | 101 | `11f63664c0df` | 1 |
| `capabilities/media/productions/archive-archipelago-001/render/archive-archipelago-001.gpkg` | other | 229376 | — | `e000c6000126` |  |
| `capabilities/media/productions/archive-archipelago-001/render/archive-archipelago-001.png` | media | 186172 | — | `2f0a7c9d6b8c` |  |
| `capabilities/media/productions/archive-archipelago-001/render/archive-archipelago-001.svg` | media | 60199 | — | `eff192e20aaa` |  |
| `capabilities/media/productions/archive-archipelago-001/render/build-manifest.json` | config | 886 | 30 | `50db6c639160` | 1 |
| `capabilities/media/productions/archive-archipelago-001/render/owners.geojson` | other | 1023 | — | `2072d99b66cd` |  |
| `capabilities/media/productions/archive-archipelago-001/render/relations.geojson` | other | 19598 | — | `0bff7fcf5b31` |  |
| `capabilities/media/productions/archive-archipelago-001/render/works.geojson` | other | 193336 | — | `ab4e78f3514b` |  |
| `capabilities/media/productions/archive-archipelago-001/source/creative-library-catalog-v1.json` | config | 1312552 | 35557 | `d020043de763` | 1 |
| `capabilities/media/productions/archive-archipelago-001/source/workstation-revision.txt` | other | 41 | 1 | `067f7f7a230d` |  |
| `capabilities/media/productions/browser-perception-note/claims.json` | config | 2063 | 30 | `2d750524ad71` | 1 |
| `capabilities/media/productions/browser-perception-note/cognition.md` | docs | 5372 | 70 | `fa11139bb281` |  |
| `capabilities/media/productions/browser-perception-note/evidence/browser-review.receipt.json` | evidence | 2353 | 52 | `b224a7993e1c` | 1 |
| `capabilities/media/productions/browser-perception-note/production.json` | config | 1238 | 39 | `334d0ae589af` | 1 |
| `capabilities/media/productions/browser-perception-note/story.mdx` | docs | 5336 | 78 | `f6ef709cd0b9` |  |
| `capabilities/media/productions/convergence-object-001/README.md` | docs | 1508 | 26 | `e6076052e34f` |  |
| `capabilities/media/productions/convergence-object-001/build.py` | core | 6752 | 169 | `85a8d6dcc949` |  |
| `capabilities/media/productions/convergence-object-001/claims.json` | config | 1776 | 42 | `fb0bdbc48c24` | 1 |
| `capabilities/media/productions/convergence-object-001/consumption-evidence.json` | config | 1800 | 32 | `ffbdd47d033d` | 1 |
| `capabilities/media/productions/convergence-object-001/friction-blender-backup-carriers.json` | config | 1740 | 26 | `9bcf1b7fdba7` | 1 |
| `capabilities/media/productions/convergence-object-001/friction-blender-engine.json` | config | 1383 | 26 | `4cbe89ad2690` | 1 |
| `capabilities/media/productions/convergence-object-001/friction-headless-audio.json` | config | 1557 | 26 | `286030d6e5b7` | 1 |
| `capabilities/media/productions/convergence-object-001/friction-production-3d-kind.json` | config | 1740 | 26 | `ea59e3644141` | 1 |
| `capabilities/media/productions/convergence-object-001/production.json` | config | 1435 | 51 | `d8f219556be9` | 1 |
| `capabilities/media/productions/convergence-object-001/render/convergence-object-001.glb` | media | 1407184 | — | `8b3ad5e31662` |  |
| `capabilities/media/productions/convergence-object-001/render/convergence-object-001.png` | media | 1271283 | — | `9c987354341c` |  |
| `capabilities/media/productions/convergence-object-001/roundtrip-receipt.json` | config | 1177 | 47 | `36ac342ca484` | 1 |
| `capabilities/media/productions/convergence-object-001/source/convergence-object-001-roundtrip.blend` | media | 640528 | — | `47bfbacbf438` |  |
| `capabilities/media/productions/convergence-object-001/source/convergence-object-001.blend` | media | 272566 | — | `bc8cc9e0e2d9` |  |
| `capabilities/media/productions/convergence-object-001/verify_import.py` | core | 2632 | 62 | `a0305511296b` |  |
| `capabilities/media/productions/convergence-sonic-ident/README.md` | docs | 2855 | 60 | `077a07822cc4` |  |
| `capabilities/media/productions/convergence-sonic-ident/claims.json` | config | 1175 | 29 | `8114b108662a` | 1 |
| `capabilities/media/productions/convergence-sonic-ident/consumption-evidence.json` | config | 1333 | 38 | `d7b2de4fc96f` | 1 |
| `capabilities/media/productions/convergence-sonic-ident/friction-validation-env.json` | config | 1553 | 27 | `7dd05dad38c2` | 1 |
| `capabilities/media/productions/convergence-sonic-ident/friction.json` | config | 1549 | 27 | `412e833b6216` | 1 |
| `capabilities/media/productions/convergence-sonic-ident/generate.py` | core | 3285 | 106 | `b7ad8b444311` |  |
| `capabilities/media/productions/convergence-sonic-ident/operation-lineage.json` | config | 2163 | 87 | `7be8a80d6e41` | 1 |
| `capabilities/media/productions/convergence-sonic-ident/production.json` | config | 2275 | 74 | `ddb059f3662a` | 1 |
| `capabilities/media/productions/convergence-sonic-ident/render/convergence-archive.flac` | other | 439084 | — | `f29436571afc` |  |
| `capabilities/media/productions/convergence-sonic-ident/render/convergence-delivery.ogg` | media | 42367 | — | `0d61a9e5791d` |  |
| `capabilities/media/productions/convergence-sonic-ident/render/convergence-master.wav` | media | 1382480 | — | `8579aab3edc7` |  |
| `capabilities/media/productions/convergence-sonic-ident/render/convergence-source.wav` | media | 921644 | — | `7b739776af6c` |  |
| `capabilities/media/productions/convergence-sonic-ident/render/convergence-waveform.png` | media | 12873 | — | `c853c96a1a0f` |  |
| `capabilities/media/productions/fishing-fable-lego-study-r1/claims.json` | config | 2280 | 55 | `7485698e6b90` | 1 |
| `capabilities/media/productions/fishing-fable-lego-study-r1/formal-writing-contracts-r1.md` | docs | 10100 | 109 | `372f7bed920b` |  |
| `capabilities/media/productions/fishing-fable-lego-study-r1/production.json` | config | 1380 | 40 | `a617f8ae65ca` | 1 |
| `capabilities/media/productions/fishing-fable-lego-study-r1/story-archival-reconstruction.md` | docs | 16787 | 295 | `b3c18d635a5d` |  |
| `capabilities/media/productions/fishing-fable-lego-study-r1/writing-issue-census-r1.md` | docs | 7749 | 44 | `08acd47de003` |  |
| `capabilities/media/productions/fishing-fable-lego-study-r1/writing-lego-research-dossier-r1.md` | docs | 18499 | 203 | `ef2a1ac016dd` |  |
| `capabilities/media/productions/friction-loop-field-zine/README.md` | docs | 528 | 11 | `b94195b9c499` |  |
| `capabilities/media/productions/friction-loop-field-zine/claims.json` | config | 1524 | 28 | `0bb62388b93e` | 1 |
| `capabilities/media/productions/friction-loop-field-zine/consumption-evidence.json` | config | 1631 | 34 | `2f32b71f7eee` | 1 |
| `capabilities/media/productions/friction-loop-field-zine/friction-typst-authoring.json` | config | 1764 | 28 | `020947a2bc6e` | 1 |
| `capabilities/media/productions/friction-loop-field-zine/friction-typst-markup.json` | config | 2143 | 31 | `ec120502ed83` | 1 |
| `capabilities/media/productions/friction-loop-field-zine/inspect/contact-sheet.png` | media | 686829 | — | `311217924df2` |  |
| `capabilities/media/productions/friction-loop-field-zine/production.json` | config | 1342 | 40 | `289e9405f023` | 1 |
| `capabilities/media/productions/friction-loop-field-zine/render/make-things-find-friction-field-note-001.pdf` | media | 91412 | — | `5da906509f9b` |  |
| `capabilities/media/productions/friction-loop-field-zine/source.typ` | other | 6675 | — | `9d71c37f81d7` |  |
| `capabilities/media/productions/live-relay-001/.gitattributes` | other | 233 | — | `39eef13ee9c3` |  |
| `capabilities/media/productions/live-relay-001/README.md` | docs | 3214 | 27 | `50ffcf26827b` |  |
| `capabilities/media/productions/live-relay-001/artifact-evidence/moving-image-contract.json` | config | 714 | 17 | `9452a6b71856` |  |
| `capabilities/media/productions/live-relay-001/artifact-evidence/moving-image-verification.json` | config | 3850 | 100 | `6646d0d98467` | 1 |
| `capabilities/media/productions/live-relay-001/artifact-evidence/verifier/ffprobe.json` | config | 2601 | 81 | `3686b63948cd` |  |
| `capabilities/media/productions/live-relay-001/artifact-evidence/verifier/mediaconch-implementation.xml` | other | 142424 | — | `453385a3b8db` |  |
| `capabilities/media/productions/live-relay-001/artifact-evidence/verifier/mediainfo.xml` | other | 3066 | — | `ea9f296dd446` |  |
| `capabilities/media/productions/live-relay-001/claims.json` | config | 3213 | 68 | `8c22454ef0c8` | 1 |
| `capabilities/media/productions/live-relay-001/consumption-evidence.json` | config | 3740 | 85 | `6f345ce94de7` | 1 |
| `capabilities/media/productions/live-relay-001/evidence/final-qc/contact-sheet.png` | media | 797634 | — | `0fa98d56226d` |  |
| `capabilities/media/productions/live-relay-001/evidence/final-qc/ffprobe.json` | evidence | 4828 | 145 | `9ee6eb1be942` |  |
| `capabilities/media/productions/live-relay-001/evidence/final-qc/summary.json` | evidence | 2000 | 76 | `f433d8e3dadb` | 1 |
| `capabilities/media/productions/live-relay-001/evidence/friction-controller-pre-finally-r1.json` | evidence | 4483 | 43 | `407644c70090` | 1 |
| `capabilities/media/productions/live-relay-001/evidence/obs-session-final.json` | evidence | 11271 | 261 | `75b42c947a34` | 1 |
| `capabilities/media/productions/live-relay-001/manifest.sha256` | other | 399 | — | `881050bbd9b6` |  |
| `capabilities/media/productions/live-relay-001/production.json` | config | 2906 | 90 | `79048f2cb8ca` | 1 |
| `capabilities/media/productions/live-relay-001/program/00-signal.png` | media | 128470 | — | `5eaf99ddf468` |  |
| `capabilities/media/productions/live-relay-001/program/01-archive.png` | media | 896957 | — | `694bd842b236` |  |
| `capabilities/media/productions/live-relay-001/program/02-object.png` | media | 2640380 | — | `c943637be824` |  |
| `capabilities/media/productions/live-relay-001/program/03-constellation.png` | media | 177564 | — | `d05aa8c518ab` |  |
| `capabilities/media/productions/live-relay-001/render/live-relay-001-master.mkv` | media | 41512896 | — | `05763a34936d` |  |
| `capabilities/media/productions/live-relay-001/render/live-relay-001-poster.png` | media | 148270 | — | `2ea8fabed997` |  |
| `capabilities/media/productions/live-relay-001/render/live-relay-001-source.mp4` | media | 16481768 | — | `d78adcac0988` |  |
| `capabilities/media/productions/live-relay-001/run-live-relay.ps1` | core | 15095 | 264 | `4901198cdde3` |  |
| `capabilities/media/productions/live-relay-001/source/archive-archipelago-001.png` | media | 186172 | — | `2f0a7c9d6b8c` |  |
| `capabilities/media/productions/live-relay-001/source/convergence-object-001.png` | media | 1271283 | — | `9c987354341c` |  |
| `capabilities/media/productions/live-relay-001/source/provenance.json` | config | 2050 | 40 | `376046c5384d` | 1 |
| `capabilities/media/productions/live-relay-001/source/source-manifest.json` | config | 1029 | 27 | `fcc3416f79f7` | 1 |
| `capabilities/media/productions/live-relay-001/source/system-constellation-field-crop.png` | media | 57784 | — | `952598905e99` |  |
| `capabilities/media/productions/live-relay-001/source/system-constellation-poster-001.png` | media | 246182 | — | `40bfdb7fc295` |  |
| `capabilities/media/productions/mhs-hardware-boundary/claims.json` | config | 4950 | 107 | `14cc12752adf` | 1 |
| `capabilities/media/productions/mhs-hardware-boundary/cognition.md` | docs | 6073 | 42 | `d3309f5eb906` |  |
| `capabilities/media/productions/mhs-hardware-boundary/evidence/fresh-consumer-v1-carrier-failure.json` | evidence | 765 | 16 | `a97e76b94f22` | 1 |
| `capabilities/media/productions/mhs-hardware-boundary/evidence/fresh-consumer-v2-freeform.json` | evidence | 2159 | 64 | `51a23a291b77` | 1 |
| `capabilities/media/productions/mhs-hardware-boundary/evidence/owner-disposition.json` | evidence | 1730 | 36 | `435ca21380ae` | 1 |
| `capabilities/media/productions/mhs-hardware-boundary/evidence/revised-firstpass-v1.json` | evidence | 2168 | 65 | `c4ccf6916d76` | 1 |
| `capabilities/media/productions/mhs-hardware-boundary/evidence/revised-owner-audit.json` | evidence | 1058 | 23 | `a35c989c6260` | 1 |
| `capabilities/media/productions/mhs-hardware-boundary/production.json` | config | 1449 | 41 | `b8391cba0217` | 1 |
| `capabilities/media/productions/mhs-hardware-boundary/story.mdx` | docs | 11499 | 130 | `32cef398e3a5` |  |
| `capabilities/media/productions/ordivon-book-v0/book.mdx` | docs | 169921 | 5711 | `14e5e15b9223` |  |
| `capabilities/media/productions/ordivon-book-v0/chapter-02.mdx` | docs | 17062 | 475 | `af70e8b0f8a3` |  |
| `capabilities/media/productions/ordivon-book-v0/chapter-03.mdx` | docs | 19077 | 593 | `bcf33947a2ae` |  |
| `capabilities/media/productions/ordivon-book-v0/chapter-04.mdx` | docs | 22971 | 769 | `38cbcb4e3f0b` |  |
| `capabilities/media/productions/ordivon-book-v0/chapter-05.mdx` | docs | 24547 | 707 | `7ae8104ffc6b` |  |
| `capabilities/media/productions/ordivon-book-v0/chapter-06.mdx` | docs | 28661 | 1155 | `063a401e225f` |  |
| `capabilities/media/productions/ordivon-book-v0/chapter-07.mdx` | docs | 40698 | 1629 | `3675074fada8` |  |
| `capabilities/media/productions/ordivon-book-v0/claims.json` | config | 53833 | 1062 | `f0dcf8b1888f` | 1 |
| `capabilities/media/productions/ordivon-book-v0/cognition.md` | docs | 30147 | 470 | `dd51738f4bdd` |  |
| `capabilities/media/productions/ordivon-book-v0/constitution.md` | docs | 8692 | 186 | `0a4622f054fe` |  |
| `capabilities/media/productions/ordivon-book-v0/consumption-audit.md` | docs | 37505 | 778 | `2116bf2ee5ca` |  |
| `capabilities/media/productions/ordivon-book-v0/external-methods.md` | docs | 32978 | 266 | `99ec96f38a49` |  |
| `capabilities/media/productions/ordivon-book-v0/future-horizon-laboratory.mdx` | docs | 44909 | 1858 | `22ba47ac9c66` |  |
| `capabilities/media/productions/ordivon-book-v0/portable/portable-pdf.receipt.json` | config | 2965 | 85 | `a1c55ec4ac5b` | 1 |
| `capabilities/media/productions/ordivon-book-v0/portable/render_pdf.py` | core | 9208 | 232 | `0ce81d8bfa32` |  |
| `capabilities/media/productions/ordivon-book-v0/production.json` | config | 8782 | 226 | `fe8552c4ccbc` | 1 |
| `capabilities/media/productions/ordivon-book-v0/source-map.md` | docs | 57682 | 799 | `652e094d01cf` |  |
| `capabilities/media/productions/ordivon-book-v0/story.mdx` | docs | 16126 | 346 | `bb1a14412b98` |  |
| `capabilities/media/productions/ordivon-system-constellation-atlas/README.md` | docs | 1771 | 34 | `7afd8b53dce0` |  |
| `capabilities/media/productions/ordivon-system-constellation-atlas/claims.json` | config | 1954 | 42 | `f901cb0c5e8d` | 1 |
| `capabilities/media/productions/ordivon-system-constellation-atlas/consumption-evidence.json` | config | 1974 | 47 | `ceadbf4c7c54` | 1 |
| `capabilities/media/productions/ordivon-system-constellation-atlas/friction.json` | config | 1863 | 28 | `8c8a1cc706ec` | 1 |
| `capabilities/media/productions/ordivon-system-constellation-atlas/generate.py` | core | 9100 | 220 | `d7c9178434b2` |  |
| `capabilities/media/productions/ordivon-system-constellation-atlas/manifest.sha256` | other | 990 | — | `55b913c68f20` |  |
| `capabilities/media/productions/ordivon-system-constellation-atlas/production.json` | config | 2021 | 65 | `227e80ed8c94` | 1 |
| `capabilities/media/productions/ordivon-system-constellation-atlas/render/ordivon-system-constellation.gpkg` | other | 106496 | — | `9429fd06b37d` |  |
| `capabilities/media/productions/ordivon-system-constellation-atlas/render/ordivon-system-constellation.png` | media | 161559 | — | `b13d7497e569` |  |
| `capabilities/media/productions/ordivon-system-constellation-atlas/render/ordivon-system-constellation.svg` | media | 9645 | — | `51abed191124` |  |
| `capabilities/media/productions/ordivon-system-constellation-atlas/source/repositories.geojson` | other | 8212 | — | `00878f16cd66` |  |
| `capabilities/media/productions/ordivon-system-constellation-atlas/source/repositories.json` | config | 4506 | 154 | `1a21fdd60cc0` | 1 |
| `capabilities/media/productions/runtime-introduction/README.md` | docs | 6628 | 99 | `a10b59958cf0` |  |
| `capabilities/media/productions/runtime-introduction/assets.json` | config | 16054 | 516 | `ffff3d43d50d` | 1 |
| `capabilities/media/productions/runtime-introduction/claims.json` | config | 3255 | 65 | `60a562c01e2f` | 1 |
| `capabilities/media/productions/runtime-introduction/cognition.md` | docs | 5517 | 45 | `f6343abcfdb7` |  |
| `capabilities/media/productions/runtime-introduction/evidence/media-v2-audio-declaration-parity-r6.json` | evidence | 1484 | 41 | `3b7b0f4eb63f` | 1 |
| `capabilities/media/productions/runtime-introduction/evidence/media-v2-picture-lineage-recheck-r7.json` | evidence | 2563 | 59 | `5eadc7291332` | 1 |
| `capabilities/media/productions/runtime-introduction/evidence/narration-rate-pressure-20260824.json` | evidence | 3078 | 78 | `ff815e19cc32` | 1 |
| `capabilities/media/productions/runtime-introduction/evidence/narration-sapi.receipt.json` | evidence | 2184 | 88 | `4c07fa62a534` | 1 |
| `capabilities/media/productions/runtime-introduction/evidence/r2-replica.receipt.json` | evidence | 2841 | 69 | `4a8af8f36961` | 1 |
| `capabilities/media/productions/runtime-introduction/evidence/runtime-demo.receipt.json` | evidence | 5583 | 187 | `c612500db231` | 1 |
| `capabilities/media/productions/runtime-introduction/history/cognition-through-p4.md` | docs | 14625 | 132 | `522cf33fef12` |  |
| `capabilities/media/productions/runtime-introduction/plan.md` | docs | 5584 | 112 | `4e63b472b1ec` |  |
| `capabilities/media/productions/runtime-introduction/production.json` | config | 2751 | 101 | `73f9bd3f593b` | 1 |
| `capabilities/media/productions/runtime-introduction/script/narration.en.md` | docs | 1160 | 19 | `dc4b61c3a07a` |  |
| `capabilities/media/productions/runtime-introduction/script/narration.zh.md` | docs | 1282 | 19 | `0dbf5ab4a0de` |  |
| `capabilities/media/productions/runtime-introduction/story.mdx` | docs | 1403 | 27 | `a05ab77acc14` |  |
| `capabilities/media/productions/runtime-introduction/timed-text/narration.en.json` | config | 2501 | 20 | `a6d515aa8e2a` | 1 |
| `capabilities/media/productions/runtime-introduction/timed-text/standard/README.md` | docs | 598 | 7 | `ae3c62221ca8` |  |
| `capabilities/media/productions/runtime-introduction/timed-text/standard/narration.en.srt` | other | 1389 | — | `e9d517c8bdf3` |  |
| `capabilities/media/productions/runtime-introduction/timed-text/standard/narration.en.ttml` | other | 2554 | — | `b30e5f65c5fc` |  |
| `capabilities/media/productions/runtime-introduction/timed-text/standard/narration.en.vtt` | other | 1733 | — | `8673c412f578` |  |
| `capabilities/media/productions/runtime-introduction/timeline/README.md` | docs | 2323 | 49 | `708e95738977` |  |
| `capabilities/media/productions/runtime-introduction/timeline/assembly.v0.otio` | other | 40857 | — | `5e678803084d` |  |
| `capabilities/media/productions/runtime-introduction/timeline/assembly.v1.otio` | other | 2850 | — | `1bc22d433167` |  |
| `capabilities/media/productions/runtime-introduction/timeline/assembly.v2.otio` | other | 5226 | — | `67602b51cbaf` |  |
| `capabilities/media/productions/site-social-card/README.md` | docs | 670 | 12 | `da36e32347e0` |  |
| `capabilities/media/productions/site-social-card/assets.json` | config | 1616 | 64 | `c8b128f26467` | 1 |
| `capabilities/media/productions/site-social-card/claims.json` | config | 2015 | 65 | `45da1d369f60` | 1 |
| `capabilities/media/productions/site-social-card/cognition.md` | docs | 5083 | 57 | `acee2d4b177d` |  |
| `capabilities/media/productions/site-social-card/output/opengraph-image.png` | media | 110038 | — | `9a67bb6fc7f2` |  |
| `capabilities/media/productions/site-social-card/production.json` | config | 1180 | 41 | `603f95a436f3` | 1 |
| `capabilities/media/productions/site-social-card/source/opengraph-image.svg` | media | 3311 | — | `08e7436bb09b` |  |
| `capabilities/media/productions/studio-expression-card/README.md` | docs | 750 | 12 | `efab36bcee8c` |  |
| `capabilities/media/productions/studio-expression-card/assets.json` | config | 1688 | 64 | `02e8580c9b9d` | 1 |
| `capabilities/media/productions/studio-expression-card/claims.json` | config | 2283 | 66 | `f014cb27b7aa` | 1 |
| `capabilities/media/productions/studio-expression-card/cognition.md` | docs | 3344 | 57 | `72edb8a4b3c9` |  |
| `capabilities/media/productions/studio-expression-card/output/card.png` | media | 115196 | — | `fc19d4cf2798` |  |
| `capabilities/media/productions/studio-expression-card/production.json` | config | 1192 | 41 | `dd4fd502ca63` | 1 |
| `capabilities/media/productions/studio-expression-card/source/card.svg` | media | 4532 | — | `a8ed35e9f9e4` |  |
| `capabilities/media/pyproject.toml` | config | 610 | 31 | `019f7e8b5dd5` |  |
| `capabilities/media/research/equipment/PROVIDER-FIRST-PF0.md` | research | 5511 | 120 | `6446eb4d76a0` |  |
| `capabilities/media/research/equipment/README.md` | research | 5020 | 102 | `bbbcbf37e5f8` |  |
| `capabilities/media/research/equipment/equipment-world.json` | research | 23225 | 742 | `e1d81028d423` | 1 |
| `capabilities/media/research/equipment/evidence/af0-af9-agent-first-friction-20260816.json` | evidence | 6900 | 158 | `09b8d4e2e4a4` | 1 |
| `capabilities/media/research/equipment/evidence/e0-e7-20260813.json` | evidence | 7476 | 132 | `e05f15ae9fb2` | 1 |
| `capabilities/media/research/equipment/evidence/e5-hardware-20260813.json` | evidence | 1241 | 23 | `74332c265741` | 1 |
| `capabilities/media/research/equipment/evidence/e8-capability-expansion-20260814.json` | evidence | 8094 | 161 | `3e106058571c` | 1 |
| `capabilities/media/research/equipment/experiments/af4_blender_exit0_fault.py` | research | 234 | 4 | `8b7638e60e7b` |  |
| `capabilities/media/research/equipment/experiments/af8_blender_micro.py` | research | 1911 | 65 | `be4a5f77c313` |  |
| `capabilities/media/research/equipment/experiments/af8_deterministic_still.svg` | media | 492 | — | `f2e7254bc80c` |  |
| `capabilities/media/research/equipment/experiments/e0-e7-equipment-world.md` | research | 10903 | 261 | `1d914954fb53` |  |
| `capabilities/media/research/equipment/experiments/e8-capability-expansion-consumption.md` | research | 7163 | 83 | `2747d00fb109` |  |
| `capabilities/media/research/equipment/sources.json` | research | 3839 | 26 | `e19012d358d1` | 1 |
| `capabilities/media/research/expression/README.md` | research | 13047 | 168 | `8f1cf5daa2a2` |  |
| `capabilities/media/research/expression/aesthetic-model.md` | research | 5676 | 110 | `9334c9e8b4d5` |  |
| `capabilities/media/research/expression/context.json` | research | 12209 | 305 | `c20930dcef7a` | 1 |
| `capabilities/media/research/expression/creative-system.md` | research | 12726 | 211 | `a0b0c1f15007` |  |
| `capabilities/media/research/expression/cultural-observatory.md` | research | 11060 | 210 | `7367722c0f5b` |  |
| `capabilities/media/research/expression/evidence-map.md` | research | 12757 | 173 | `9327a7804aa8` |  |
| `capabilities/media/research/expression/evidence/m7-foundational-media-20260813.json` | evidence | 3928 | 76 | `300cdd820efb` | 1 |
| `capabilities/media/research/expression/evidence/mhs-agent-hardware-boundary-20260829.md` | evidence | 8046 | 98 | `ab6a492d81b8` |  |
| `capabilities/media/research/expression/evidence/r0-r3-cultural-observatory-20260811.json` | evidence | 4152 | 88 | `55fc9057309c` | 1 |
| `capabilities/media/research/expression/evidence/r4-rich-perception-20260811.json` | evidence | 4288 | 92 | `96d28aefe126` | 1 |
| `capabilities/media/research/expression/evidence/r5-grounded-meaning-20260811.json` | evidence | 6928 | 111 | `d81d544660ec` | 1 |
| `capabilities/media/research/expression/evidence/r6-creative-alpha-20260811.json` | evidence | 27269 | 682 | `0e2a0ab86b08` | 1 |
| `capabilities/media/research/expression/experiments/a31-runtime-response-loss.md` | research | 10199 | 211 | `ce9a0a4d6390` |  |
| `capabilities/media/research/expression/experiments/a32-adversarial-epistemics.md` | research | 11123 | 224 | `91652db3bf0a` |  |
| `capabilities/media/research/expression/experiments/a32-security-ae0-evidence.json` | research | 1832 | 42 | `213d79ce264f` | 1 |
| `capabilities/media/research/expression/experiments/a33-station-zero-affect-evidence.json` | research | 2690 | 97 | `22ecc5f6dea1` | 1 |
| `capabilities/media/research/expression/experiments/a33-station-zero-affect.md` | research | 11140 | 205 | `ce7ddc2ce54a` |  |
| `capabilities/media/research/expression/experiments/m7-foundational-media.md` | research | 10421 | 186 | `57bca044ce48` |  |
| `capabilities/media/research/expression/experiments/r0-r3-cultural-observatory.md` | research | 8586 | 160 | `0c216f2b5750` |  |
| `capabilities/media/research/expression/experiments/r4-rich-perception.md` | research | 12642 | 283 | `03afda26879e` |  |
| `capabilities/media/research/expression/experiments/r5-grounded-meaning.md` | research | 17242 | 424 | `078539d371f6` |  |
| `capabilities/media/research/expression/experiments/r6-creative-alpha.md` | research | 14879 | 317 | `6ffd71415cef` |  |
| `capabilities/media/research/expression/foundations/README.md` | research | 1689 | 21 | `2b4a2827232a` |  |
| `capabilities/media/research/expression/foundations/media-deep-foundations-mf0-mf9-closeout-and-domain-coverage-handoff-20260818.md` | research | 47947 | 1759 | `5f8352cb2ddd` |  |
| `capabilities/media/research/expression/foundations/media-foundations-mf0-mf7-closeout-20260817.md` | research | 16361 | 659 | `4f41e8a1ded9` |  |
| `capabilities/media/research/expression/foundations/media-foundations-mf2h-20260817.md` | research | 28006 | 546 | `6232f2ad7bd6` |  |
| `capabilities/media/research/expression/foundations/media-foundations-mf2i-20260817.md` | research | 31898 | 494 | `7e1a6ab19775` |  |
| `capabilities/media/research/expression/foundations/media-foundations-mf3i-20260817.md` | research | 61076 | 1851 | `4d2f2d8c761e` |  |
| `capabilities/media/research/expression/foundations/media-foundations-mf4k-20260817.md` | research | 53705 | 1621 | `d796d8938d68` |  |
| `capabilities/media/research/expression/foundations/media-foundations-mf5i-20260817.md` | research | 39890 | 1335 | `e525dd14b795` |  |
| `capabilities/media/research/expression/foundations/media-foundations-mf6f-20260817.md` | research | 40167 | 1313 | `9409605d7bcf` |  |
| `capabilities/media/research/expression/foundations/media-foundations-mf7h-20260817.md` | research | 47374 | 1743 | `31bf6fd5f218` |  |
| `capabilities/media/research/expression/foundations/media-foundations-mf8-agency-v1-20260818.md` | research | 14278 | 552 | `083783abf86b` |  |
| `capabilities/media/research/expression/foundations/media-foundations-mf9-experience-v1-20260818.md` | research | 12333 | 497 | `44ab6631769c` |  |
| `capabilities/media/research/expression/foundations/media-round-c-through-d-e-fresh-continent-final-closeout-20260818.md` | research | 16231 | 636 | `a46330aeb35b` |  |
| `capabilities/media/research/expression/foundations/media-round-d-a-infrastructural-environmental-elemental-mediation-boundary-test-20260818.md` | research | 52757 | 2214 | `886bbe0a2a82` |  |
| `capabilities/media/research/expression/foundations/media-round-d-b-operative-executable-mediation-reducibility-20260818.md` | research | 48753 | 2148 | `008323226f0e` |  |
| `capabilities/media/research/expression/foundations/media-round-d-c-interface-affordance-action-coupling-reducibility-20260818.md` | research | 49218 | 2138 | `bee6fa7e463a` |  |
| `capabilities/media/research/expression/foundations/media-round-d-d-mediated-presence-telepresence-teleaction-embodiment-reducibility-20260818.md` | research | 55960 | 2286 | `7b1c224f3251` |  |
| `capabilities/media/research/expression/foundations/media-round-d-e-datafication-legibility-metricization-reducibility-20260818.md` | research | 48740 | 2245 | `a4c13b5d0160` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-fresh-unknown-continent-rescan-round-c-20260818.md` | research | 32045 | 1305 | `76113308a873` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-a-communication-reducibility-20260818.md` | research | 28852 | 1023 | `4e1717c22686` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-b-encounter-exposure-reducibility-20260818.md` | research | 28857 | 1245 | `e5eb4a668f79` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-c-convention-protocol-interoperability-reducibility-20260818.md` | research | 30791 | 1119 | `72838eeac424` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-d-publicness-addressability-publication-reducibility-20260818.md` | research | 31677 | 1225 | `7173d70c8479` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-e-artifact-work-edition-performance-generative-identity-reducibility-20260818.md` | research | 38113 | 1405 | `bcfc3c917ad1` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-f-selection-gatekeeping-visibility-allocation-reducibility-20260818.md` | research | 36264 | 1587 | `81e210e561f5` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-g-meaning-pragmatics-context-preservation-reducibility-20260818.md` | research | 38282 | 1454 | `b51bc70fdf11` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-h-inscription-fixation-materialization-reducibility-20260818.md` | research | 43288 | 1838 | `d39eb18d7890` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-i-authorship-creation-attribution-reducibility-20260818.md` | research | 40832 | 1743 | `bc85e145d590` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-j-archive-preservation-responsibility-reducibility-20260818.md` | research | 52072 | 2058 | `ef20f1565cd4` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-k-audience-public-formation-reducibility-20260818.md` | research | 51638 | 2072 | `cb85c7c6d0e0` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-l-reflexive-mediation-ecology-reducibility-20260818.md` | research | 49749 | 2082 | `502448d3432e` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-round-b-m-translation-remediation-reducibility-20260818.md` | research | 51633 | 2265 | `a99d6904a83d` |  |
| `capabilities/media/research/expression/foundations/media-whole-domain-unexplored-space-search-round-a-20260818.md` | research | 28392 | 562 | `64b00fe31acd` |  |
| `capabilities/media/research/expression/knowledge-model.md` | research | 6975 | 146 | `b5a5eda1c00a` |  |
| `capabilities/media/research/expression/m7-foundational-media-program.md` | research | 20071 | 454 | `69bda2f7e882` |  |
| `capabilities/media/research/expression/m7-world-model-audit.md` | research | 10306 | 226 | `9879971397ff` |  |
| `capabilities/media/research/expression/media-topology.md` | research | 14141 | 218 | `ea54e7b650ec` |  |
| `capabilities/media/research/expression/media-world-model.json` | research | 3344 | 39 | `4014026e5825` | 1 |
| `capabilities/media/research/expression/profiles/README.md` | research | 4119 | 39 | `4805c1a08da9` |  |
| `capabilities/media/research/expression/profiles/audio.md` | research | 7021 | 126 | `92278d5efe44` |  |
| `capabilities/media/research/expression/profiles/index.json` | research | 3408 | 113 | `8c2657ea4d37` | 1 |
| `capabilities/media/research/expression/profiles/interactive.md` | research | 2629 | 50 | `f5471f8340d9` |  |
| `capabilities/media/research/expression/profiles/motion-video.md` | research | 6742 | 131 | `478a5f24ed97` |  |
| `capabilities/media/research/expression/profiles/still-visual.md` | research | 2845 | 51 | `e2a3e2b5360a` |  |
| `capabilities/media/research/expression/profiles/writing.md` | research | 6668 | 125 | `8eb984f77763` |  |
| `capabilities/media/research/expression/protocol.md` | research | 5015 | 133 | `61961a1dd145` |  |
| `capabilities/media/research/expression/sources.json` | research | 5353 | 180 | `49c2321f622e` | 1 |
| `capabilities/media/research/media/README.md` | research | 3026 | 39 | `913321749a29` |  |
| `capabilities/media/research/media/authority/CURRENT.json` | research | 395 | 8 | `9c3ae2b4988e` | 1 |
| `capabilities/media/research/media/authority/MEDIA-OWNER-PUBLICATION-ACCEPTANCE-20260819.json` | research | 1284 | 21 | `2c702d8a05d0` | 1 |
| `capabilities/media/research/media/authority/publications/e26649a077eacfd0964e0d6ace7a3454d27c60ebcc96251dbb9b1861d867823e.json` | evidence | 25176 | 721 | `e26649a077ea` | 1 |
| `capabilities/media/research/media/bridges/README.md` | research | 2275 | 30 | `e9982fa63dc2` |  |
| `capabilities/media/research/media/core/FOUNDATION-FAMILIES.md` | research | 707 | 24 | `a1e73c2c8784` |  |
| `capabilities/media/research/media/core/README.md` | research | 2000 | 26 | `294dff42414a` |  |
| `capabilities/media/research/media/coverage/README.md` | research | 1882 | 23 | `1df4fdc1cd71` |  |
| `capabilities/media/research/media/creative-delivery-bridges.json` | research | 2941 | 40 | `46cb19c6e974` | 1 |
| `capabilities/media/research/media/derived/DATAFICATION-LEGIBILITY-METRICIZATION.md` | research | 1537 | 36 | `8a954a845f23` |  |
| `capabilities/media/research/media/derived/README.md` | research | 1126 | 11 | `deb6e17c8399` |  |
| `capabilities/media/research/media/derived/ROUND-B-PROFILES.md` | research | 3042 | 117 | `eca78f11b0ee` |  |
| `capabilities/media/research/media/derived/ROUND-D-PROFILES.md` | research | 2157 | 50 | `adc6065a0387` |  |
| `capabilities/media/research/media/engineering-consumption/OMPC-CONFORMANCE-v0.md` | research | 8280 | 142 | `6ea815fd026d` |  |
| `capabilities/media/research/media/engineering-consumption/OMPC-v0.md` | research | 7813 | 146 | `22207a922b20` |  |
| `capabilities/media/research/media/engineering-consumption/README.md` | research | 2959 | 32 | `8f9b804c86b2` |  |
| `capabilities/media/research/media/engineering-consumption/fixtures/finance-qb6-metric-legibility-dogfood.md` | research | 5531 | 135 | `639cb6a4fc5a` |  |
| `capabilities/media/research/media/engineering-consumption/fixtures/finance-qb6-metric-legibility-lineage.json` | research | 4323 | 72 | `3f78d45411ab` | 0 |
| `capabilities/media/research/media/engineering-consumption/fixtures/host-task-rev3-agent.json` | research | 2977 | 68 | `12769040b9df` | 0 |
| `capabilities/media/research/media/engineering-consumption/fixtures/host-task-rev3-dogfood.md` | research | 4131 | 66 | `05875fc32678` |  |
| `capabilities/media/research/media/engineering-consumption/fixtures/host-task-rev3-human.md` | research | 2486 | 49 | `d892eb3d9457` |  |
| `capabilities/media/research/media/engineering-consumption/fixtures/studio-expression-card-dogfood.md` | research | 6443 | 164 | `40ebfc86eaba` |  |
| `capabilities/media/research/media/engineering-consumption/fixtures/studio-expression-card-lineage.json` | research | 3884 | 88 | `c537839c04b9` | 0 |
| `capabilities/media/research/media/engineering-consumption/fixtures/web-m7-trajectory-dogfood.md` | research | 3540 | 73 | `43f88eaf8b55` |  |
| `capabilities/media/research/media/engineering-consumption/fixtures/web-m7-trajectory-lineage.json` | research | 2127 | 44 | `05985889daa0` | 0 |
| `capabilities/media/research/media/evidence/README.md` | evidence | 1825 | 40 | `4ac4be9e5290` |  |
| `capabilities/media/research/media/history/README.md` | research | 2054 | 36 | `e48cdfc58f18` |  |
| `capabilities/media/research/media/negative/README.md` | research | 1883 | 49 | `265da6955111` |  |
| `capabilities/media/schemas/asset.schema.json` | schemas | 2780 | 93 | `504eb78cc530` |  |
| `capabilities/media/schemas/claims.schema.json` | schemas | 1693 | 57 | `f0330fffef6c` |  |
| `capabilities/media/schemas/operation-lineage.schema.json` | schemas | 2326 | 109 | `6619c2f32579` |  |
| `capabilities/media/schemas/production.schema.json` | schemas | 7246 | 294 | `f79ff86d16ef` |  |
| `capabilities/media/schemas/runtime-demo-receipt.schema.json` | schemas | 6842 | 218 | `91c6166f5294` |  |
| `capabilities/media/schemas/timed-text.schema.json` | schemas | 1813 | 57 | `1611667e3c5a` |  |
| `capabilities/media/scripts/build-creative-index.py` | core | 1209 | 34 | `3cd12ef8f9d6` |  |
| `capabilities/media/scripts/build_sapi_narration.py` | core | 5494 | 161 | `d045dc227012` |  |
| `capabilities/media/scripts/creative_library.py` | core | 29515 | 613 | `7a3191aa972b` |  |
| `capabilities/media/scripts/materialize-python.py` | core | 2607 | 65 | `96bf9b0e697a` |  |
| `capabilities/media/scripts/owner-environment` | other | 2518 | — | `e376784c342a` |  |
| `capabilities/media/scripts/produce-internet-message.py` | core | 1499 | 25 | `70290d5cec83` |  |
| `capabilities/media/scripts/produce-parquet.py` | core | 1096 | 23 | `8b515062deb8` |  |
| `capabilities/media/scripts/produce-warc-response.py` | core | 1608 | 32 | `d209d9021fad` |  |
| `capabilities/media/scripts/require-js-deps.mjs` | core | 1636 | 35 | `ad98fb1d4acb` |  |
| `capabilities/media/scripts/require-python-deps.py` | core | 2457 | 62 | `7452523fdf59` |  |
| `capabilities/media/scripts/resolve-native-produce.py` | core | 14027 | 264 | `39f700fc9521` |  |
| `capabilities/media/scripts/run-e6-equipment-dogfood.py` | core | 11203 | 198 | `985b74518c7c` |  |
| `capabilities/media/scripts/run-e7-equipment-economics.py` | core | 14594 | 202 | `fd7c9ee48fe7` |  |
| `capabilities/media/scripts/run-m7-foundational-media.py` | core | 13670 | 275 | `cd020cf6053c` |  |
| `capabilities/media/scripts/run-r4-article-experiment.py` | core | 2358 | 57 | `1c6d76bd574e` |  |
| `capabilities/media/scripts/run-r4-media-experiment.py` | core | 12895 | 332 | `e7f64fe065aa` |  |
| `capabilities/media/scripts/run-r5-grounded-meaning.py` | core | 2698 | 59 | `f77ae6db7c11` |  |
| `capabilities/media/scripts/run-r6-creative-alpha.py` | core | 7978 | 106 | `4e5ceb40448e` |  |
| `capabilities/media/scripts/run-r6-creative-validity.py` | core | 7114 | 164 | `adffdb491408` |  |
| `capabilities/media/scripts/studio-agent-surface.py` | core | 1160 | 35 | `05fa7edb05ab` |  |
| `capabilities/media/scripts/synthesize-sapi-cues.ps1` | core | 789 | 26 | `f628838741dc` |  |
| `capabilities/media/src/ordivon_studio/__init__.py` | core | 61 | 3 | `51d498f9700d` |  |
| `capabilities/media/src/ordivon_studio/agent_dependencies.py` | core | 5348 | 147 | `38d11daeba09` |  |
| `capabilities/media/src/ordivon_studio/agent_processing.py` | core | 6049 | 132 | `3ce5c93026d9` |  |
| `capabilities/media/src/ordivon_studio/agent_productions.py` | core | 3781 | 86 | `bfd173f9cd55` |  |
| `capabilities/media/src/ordivon_studio/agent_surface.py` | core | 4984 | 113 | `78516a49e65e` |  |
| `capabilities/media/src/ordivon_studio/agent_surface_contracts.py` | core | 6741 | 120 | `755540b0041a` |  |
| `capabilities/media/src/ordivon_studio/assets.py` | core | 7364 | 186 | `5d77c4194b01` |  |
| `capabilities/media/src/ordivon_studio/cli.py` | core | 13816 | 264 | `eb87d272c0f0` |  |
| `capabilities/media/src/ordivon_studio/cli_handlers/__init__.py` | core | 270 | 11 | `a88100ed3cf8` |  |
| `capabilities/media/src/ordivon_studio/cli_handlers/ecology.py` | core | 4100 | 103 | `98add5d6c37d` |  |
| `capabilities/media/src/ordivon_studio/cli_handlers/equipment.py` | core | 2626 | 80 | `86ed3f82a637` |  |
| `capabilities/media/src/ordivon_studio/cli_handlers/media.py` | core | 8209 | 232 | `9401fc5c9b43` |  |
| `capabilities/media/src/ordivon_studio/cloudflare_r2.py` | core | 4459 | 125 | `5f6c6a625264` |  |
| `capabilities/media/src/ordivon_studio/cloudflare_r2_transport.py` | core | 5701 | 164 | `cd4b66e28dff` |  |
| `capabilities/media/src/ordivon_studio/creative_index.py` | core | 10989 | 261 | `678167e0a8b6` |  |
| `capabilities/media/src/ordivon_studio/creative_index_artifact.py` | core | 6805 | 132 | `c3fbcbf5d88b` |  |
| `capabilities/media/src/ordivon_studio/creative_index_library.py` | core | 12779 | 260 | `4f9a141512ef` |  |
| `capabilities/media/src/ordivon_studio/creative_index_source_utils.py` | core | 1727 | 51 | `9ef60805d44e` |  |
| `capabilities/media/src/ordivon_studio/ecology/__init__.py` | core | 224 | 5 | `5f8f1249f6a2` |  |
| `capabilities/media/src/ordivon_studio/ecology/board.py` | core | 18292 | 387 | `1bad8a0526d5` |  |
| `capabilities/media/src/ordivon_studio/ecology/collection.py` | core | 5099 | 121 | `aaf90afaef8f` |  |
| `capabilities/media/src/ordivon_studio/ecology/contracts.py` | core | 792 | 25 | `e02cd3654ee8` |  |
| `capabilities/media/src/ordivon_studio/ecology/feed.py` | core | 3659 | 86 | `b10add6f75d2` |  |
| `capabilities/media/src/ordivon_studio/equipment.py` | core | 4717 | 125 | `453289bfd217` |  |
| `capabilities/media/src/ordivon_studio/equipment_capabilities.py` | core | 14477 | 289 | `151d01b2fb45` |  |
| `capabilities/media/src/ordivon_studio/equipment_discovery.py` | core | 8918 | 213 | `edd72a17465a` |  |
| `capabilities/media/src/ordivon_studio/equipment_evaluation.py` | core | 2649 | 63 | `caa0a6736e9b` |  |
| `capabilities/media/src/ordivon_studio/equipment_plan.py` | core | 13362 | 247 | `41c521295791` |  |
| `capabilities/media/src/ordivon_studio/equipment_plan_contracts.py` | core | 1912 | 61 | `03705fb6075f` |  |
| `capabilities/media/src/ordivon_studio/equipment_plan_delivery.py` | core | 9902 | 149 | `0b87e89590da` |  |
| `capabilities/media/src/ordivon_studio/figma_provider.py` | core | 5965 | 133 | `732732de9a43` |  |
| `capabilities/media/src/ordivon_studio/learning_context.py` | core | 5157 | 119 | `9584d4d93a42` |  |
| `capabilities/media/src/ordivon_studio/models.py` | core | 5417 | 124 | `15037043af52` |  |
| `capabilities/media/src/ordivon_studio/observatory.py` | core | 5773 | 136 | `c36d6afe5991` |  |
| `capabilities/media/src/ordivon_studio/observatory_analysis.py` | core | 14161 | 299 | `4d7d38e4573f` |  |
| `capabilities/media/src/ordivon_studio/observatory_apple_music.py` | core | 2175 | 45 | `01bb98b4d700` |  |
| `capabilities/media/src/ordivon_studio/observatory_contracts.py` | core | 578 | 19 | `80ae780de84a` |  |
| `capabilities/media/src/ordivon_studio/observatory_guardian.py` | core | 4137 | 94 | `b0c566cc6e2c` |  |
| `capabilities/media/src/ordivon_studio/observatory_hacker_news.py` | core | 3369 | 66 | `78d3752c2a60` |  |
| `capabilities/media/src/ordivon_studio/observatory_source.py` | core | 5430 | 164 | `8742a1ad5b71` |  |
| `capabilities/media/src/ordivon_studio/operation_impact.py` | core | 10245 | 228 | `5027d53e0d75` |  |
| `capabilities/media/src/ordivon_studio/perception.py` | core | 4742 | 113 | `b95757c9c482` |  |
| `capabilities/media/src/ordivon_studio/perception_profiles.py` | core | 5179 | 135 | `4742647a5a35` |  |
| `capabilities/media/src/ordivon_studio/perception_selection.py` | core | 3290 | 84 | `8b0124f95a4c` |  |
| `capabilities/media/src/ordivon_studio/perception_video_io.py` | core | 5416 | 147 | `53d54448240e` |  |
| `capabilities/media/src/ordivon_studio/production_context.py` | core | 12882 | 340 | `b66e7e80683d` |  |
| `capabilities/media/src/ordivon_studio/production_validation.py` | core | 9834 | 214 | `bc0785cbb375` |  |
| `capabilities/media/src/ordivon_studio/qc.py` | core | 9975 | 257 | `9cf6040a6881` |  |
| `capabilities/media/src/ordivon_studio/research/__init__.py` | research | 227 | 5 | `5283d0f16507` |  |
| `capabilities/media/src/ordivon_studio/research/creative_analysis.py` | research | 14328 | 269 | `81895d8b9d6a` |  |
| `capabilities/media/src/ordivon_studio/research/creative_observer.py` | research | 7527 | 147 | `2845d131004b` |  |
| `capabilities/media/src/ordivon_studio/research/creative_protocol.py` | research | 11913 | 220 | `6159992fa280` |  |
| `capabilities/media/src/ordivon_studio/research/foundational_media.py` | research | 13166 | 297 | `1e5e75a03dd4` |  |
| `capabilities/media/src/ordivon_studio/research/grounded_av_tasks.py` | research | 16722 | 314 | `cc2cfe0ef5ad` |  |
| `capabilities/media/src/ordivon_studio/research/grounded_contracts.py` | research | 597 | 28 | `60e4ffec986c` |  |
| `capabilities/media/src/ordivon_studio/research/grounded_evidence.py` | research | 5302 | 128 | `b4bae9f0a3a9` |  |
| `capabilities/media/src/ordivon_studio/research/grounded_provider.py` | research | 2353 | 46 | `1d00c4e05f28` |  |
| `capabilities/media/src/ordivon_studio/research/grounded_scoring.py` | research | 18674 | 431 | `491a30963c81` |  |
| `capabilities/media/src/ordivon_studio/research/grounded_text_tasks.py` | research | 10252 | 178 | `d6c52485b85b` |  |
| `capabilities/media/src/ordivon_studio/research/guardian_article.py` | research | 17096 | 359 | `958a03d45365` |  |
| `capabilities/media/src/ordivon_studio/research/null_attack_scoring.py` | research | 3831 | 78 | `ad91add2172e` |  |
| `capabilities/media/src/ordivon_studio/research/search_calibration.py` | research | 16425 | 401 | `5f8ffe9dc265` |  |
| `capabilities/media/src/ordivon_studio/research/trial_ledger.py` | research | 11821 | 286 | `bdb99a20fec7` |  |
| `capabilities/media/src/ordivon_studio/research/trial_registration.py` | research | 7799 | 164 | `8f86b6f00681` |  |
| `capabilities/media/src/ordivon_studio/review.py` | core | 6867 | 176 | `44b03303b21c` |  |
| `capabilities/media/src/ordivon_studio/rich_perception.py` | core | 11014 | 264 | `d3d4d004e3a1` |  |
| `capabilities/media/src/ordivon_studio/rich_perception_comparison.py` | core | 7485 | 173 | `2a3d3b5e9144` |  |
| `capabilities/media/src/ordivon_studio/runtime_receipt_validation.py` | core | 3337 | 80 | `52448abb3f85` |  |
| `capabilities/media/src/ordivon_studio/timed_text.py` | core | 5457 | 142 | `247d5ada806a` |  |
| `capabilities/media/src/ordivon_studio/video.py` | core | 1605 | 57 | `89962c4b63bc` |  |
| `capabilities/media/tests/test_agent_processing.py` | tests | 9651 | 193 | `0dff3f6b4ee5` |  |
| `capabilities/media/tests/test_agent_surface.py` | tests | 19186 | 368 | `241a52533399` |  |
| `capabilities/media/tests/test_assets.py` | tests | 6529 | 152 | `1a959fae29b7` |  |
| `capabilities/media/tests/test_cloudflare_r2.py` | tests | 7621 | 173 | `bf95c0d86808` |  |
| `capabilities/media/tests/test_creative_alpha.py` | tests | 2632 | 51 | `5187b2f27c6d` |  |
| `capabilities/media/tests/test_creative_index.py` | tests | 31722 | 559 | `f4502b3d0a25` |  |
| `capabilities/media/tests/test_creative_library.py` | tests | 17026 | 319 | `04e97e2423b5` |  |
| `capabilities/media/tests/test_ecology.py` | tests | 27380 | 647 | `3197bd58bb83` |  |
| `capabilities/media/tests/test_equipment.py` | tests | 27409 | 463 | `fae8f36fbde8` |  |
| `capabilities/media/tests/test_expression_context.py` | tests | 6846 | 117 | `dc993d9c4095` |  |
| `capabilities/media/tests/test_figma_provider.py` | tests | 2132 | 30 | `83eac4ec81d9` |  |
| `capabilities/media/tests/test_foundational_media.py` | tests | 4619 | 89 | `6cbd63fa8c07` |  |
| `capabilities/media/tests/test_grounded_meaning.py` | tests | 9039 | 159 | `ad0f4ec6be7b` |  |
| `capabilities/media/tests/test_learning_context.py` | tests | 3667 | 72 | `930e55abe54c` |  |
| `capabilities/media/tests/test_models.py` | tests | 14394 | 253 | `c1b5d7a0fd62` |  |
| `capabilities/media/tests/test_observatory.py` | tests | 7915 | 120 | `b68282a7cedd` |  |
| `capabilities/media/tests/test_operation_impact.py` | tests | 11173 | 254 | `8295a026809a` |  |
| `capabilities/media/tests/test_perception.py` | tests | 2251 | 51 | `7253f567e102` |  |
| `capabilities/media/tests/test_production_context.py` | tests | 15252 | 323 | `9f0836afdaa7` |  |
| `capabilities/media/tests/test_qc.py` | tests | 6929 | 205 | `ff902d1d0cb5` |  |
| `capabilities/media/tests/test_research_validity.py` | tests | 12855 | 276 | `0557b665d607` |  |
| `capabilities/media/tests/test_review.py` | tests | 5691 | 126 | `0f1cc9967aeb` |  |
| `capabilities/media/tests/test_rich_perception.py` | tests | 7847 | 147 | `3ff6ccab8100` |  |
| `capabilities/media/tests/test_system_constellation_atlas.py` | tests | 2663 | 65 | `8515b8bdb9e4` |  |
| `capabilities/media/tests/test_timed_text.py` | tests | 3911 | 101 | `6909c53cfa72` |  |
| `capabilities/media/tests/test_video.py` | tests | 1810 | 43 | `25363d5f3e79` |  |
| `capabilities/media/tsconfig.json` | config | 487 | 17 | `f8a239ab7321` |  |
| `capabilities/media/uv.lock` | config | 24532 | — | `56e279ac73df` |  |

### preservation — capabilities/preservation/（46 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `capabilities/preservation/README.md` | docs | 4091 | 43 | `376687653782` |  |
| `capabilities/preservation/SOURCE_BOUNDARY.json` | config | 885 | 25 | `4ba087235706` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/archivematica-r6/acceptance-r6.json` | config | 5556 | 129 | `ffa91c121f2e` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/closeout-r10/closeout-r10.json` | config | 2424 | 64 | `94d1e040c765` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/forward-r1/acceptance-r4.json` | config | 13812 | 260 | `f549fc690a0a` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/forward-r2/acceptance-r5.json` | config | 26568 | 467 | `ff8bcf2c9f2e` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/forward-r2/handoffs-r5.json` | config | 7381 | 171 | `5743452e48a5` |  |
| `capabilities/preservation/artifacts/creative-preservation/forward-r2/resolver-census-r5.json` | config | 6534 | 179 | `a63d9542f1f4` |  |
| `capabilities/preservation/artifacts/creative-preservation/operations-r7/acceptance-r7.json` | config | 9432 | 198 | `cc73dbf15e3b` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-bagit-zip-12work-METS-summary.json` | config | 1601 | 60 | `2664910b1d13` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-bagit-zip-12work-METS.xml` | other | 1039870 | — | `011cc1cc352f` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-bagit-zip-12work-v1.json` | config | 1405 | 41 | `d9b515eb0177` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-bagit-zip-hidden-v1.json` | config | 2124 | 32 | `5476ef50a47c` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/game-adaptive-query-bench.xml` | other | 202945 | — | `7111edd7af6b` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/game-batch-zero.xml` | other | 44684 | — | `b1cbe5cd0fca` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/game-look-away-garden.xml` | other | 45699 | — | `8aaa06250bc4` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/game-nine-wells.xml` | other | 81992 | — | `17ba233b007e` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/game-seen-not-approved-pcb.xml` | other | 29615 | — | `08dca9262844` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/game-signal-garden-evidence-petals.xml` | other | 70546 | — | `9bcbb645f830` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/media-almost-arriving.xml` | other | 53941 | — | `2f94b5d2dac0` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/media-gesture-orrery.xml` | other | 48201 | — | `fa938732996d` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/media-one-bell-three-rooms.xml` | other | 70196 | — | `c7dd077b665e` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/web-article-the-future-will-not-wait.xml` | other | 19602 | — | `30acb21fb6e6` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/web-note-semantic-core-after-measurement.xml` | other | 21499 | — | `a815bcd763f0` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-mets/workstation-signal-seed.xml` | other | 171296 | — | `5ab6ca7e9eee` |  |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-pilot-pass1.json` | config | 41572 | 434 | `9d7b59890eb4` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/a3m-premis-fixity-v1.json` | config | 4976 | 183 | `fe6262576f8e` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/acceptance-r1.json` | config | 6395 | 143 | `07068bda2f7b` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/bagit-transfer-pilot-v1.json` | config | 2177 | 53 | `0ccb394129b0` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/corpus-v1.json` | config | 9261 | 227 | `bffbaa2041f6` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/format-identification-fido-v109.json` | config | 20353 | 482 | `5fe2c38909ca` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/pilot-r1/swhid-pilot-v1.json` | config | 11410 | 257 | `2e17f1030e81` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/retirement-r9/retirement-r9.json` | config | 2277 | 51 | `73c16f23926b` | 1 |
| `capabilities/preservation/artifacts/creative-preservation/standards-r8/migration-r8.json` | config | 4552 | 131 | `33d3a7d72d6a` | 1 |
| `capabilities/preservation/config/archivematica-preservation-r10.compose.yml` | config | 927 | 27 | `903d18f8c16c` |  |
| `capabilities/preservation/docs/creative-preservation-archivematica-r6.md` | docs | 3041 | 50 | `b068c7d3d5ad` |  |
| `capabilities/preservation/docs/creative-preservation-external-composition-r1.md` | docs | 20478 | 234 | `d69240fc75c6` |  |
| `capabilities/preservation/docs/creative-preservation-operations-r7.md` | docs | 14547 | 307 | `684020a7477a` |  |
| `capabilities/preservation/docs/creative-preservation-pilot-r1.md` | docs | 10420 | 269 | `a3461546e607` |  |
| `capabilities/preservation/docs/creative-preservation-standards-migration-r8.md` | docs | 2727 | 51 | `0cfb4b650703` |  |
| `capabilities/preservation/planning/lego-plan-r1.json` | config | 15805 | 288 | `29b91eae2412` | 1 |
| `capabilities/preservation/scripts/fixity_consumer_contract.py` | core | 2964 | 74 | `3fd23eabe9fe` |  |
| `capabilities/preservation/scripts/test_verify_source.py` | tests | 13371 | 317 | `aeb67e8996f0` |  |
| `capabilities/preservation/scripts/verify_source.py` | core | 5221 | 166 | `401400447066` |  |
| `capabilities/preservation/systemd/ordivon-preservation-fixity-r7.service` | config | 979 | 28 | `ef4a3cd34d71` |  |
| `capabilities/preservation/systemd/ordivon-preservation-fixity-r7.timer` | config | 251 | — | `2de777dd26c6` |  |

### game — domains/game/（387 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `domains/game/.gitignore` | other | 389 | — | `64b8112396d0` |  |
| `domains/game/.ordivon/project.yaml` | config | 2105 | 56 | `dedf9ff72421` |  |
| `domains/game/AGENTS.md` | docs | 3699 | 25 | `973c03907d71` |  |
| `domains/game/LICENSE` | other | 11357 | — | `c71d239df917` |  |
| `domains/game/README.md` | docs | 3745 | 59 | `cda67dc01603` | 1 |
| `domains/game/docs/agent-execution-contract-spec.md` | docs | 26563 | 297 | `e4e3f90ebcc2` |  |
| `domains/game/docs/agent-execution-implementation-plan.md` | docs | 12062 | 115 | `4173b6b27d00` |  |
| `domains/game/docs/authority.md` | docs | 1731 | 25 | `3d58278e4299` | 1 |
| `domains/game/docs/factory-pipeline.md` | docs | 18864 | 155 | `47615d9c2902` |  |
| `domains/game/docs/room-encounter-playtest-template.csv` | other | 228 | — | `50be96b54f43` |  |
| `domains/game/docs/room-encounter-playtest.md` | docs | 4789 | 93 | `791e8d9ad4d8` |  |
| `domains/game/examples/beacon-relay/.gitignore` | other | 22 | — | `78ee8a300c62` |  |
| `domains/game/examples/beacon-relay/CREDITS.txt` | other | 750 | 13 | `0771fbd799c9` |  |
| `domains/game/examples/beacon-relay/LICENSE` | other | 1068 | — | `fa7c29376d85` |  |
| `domains/game/examples/beacon-relay/README.md` | docs | 1801 | 40 | `7efcebc87206` |  |
| `domains/game/examples/beacon-relay/acceptance.gd` | core | 5522 | 122 | `b0b57713fe32` |  |
| `domains/game/examples/beacon-relay/acceptance.gd.uid` | other | 20 | — | `f9ac1ec83fad` |  |
| `domains/game/examples/beacon-relay/art/House In a Forest Loop.ogg` | media | 1430743 | — | `32680f2b2631` |  |
| `domains/game/examples/beacon-relay/art/House In a Forest Loop.ogg.import` | other | 428 | — | `27c404dfa757` |  |
| `domains/game/examples/beacon-relay/art/enemyFlyingAlt_1.png` | media | 1968 | — | `62da7d43b4a7` |  |
| `domains/game/examples/beacon-relay/art/enemyFlyingAlt_1.png.import` | other | 956 | — | `0a01dd330422` |  |
| `domains/game/examples/beacon-relay/art/enemyFlyingAlt_2.png` | media | 2006 | — | `bb754c99971c` |  |
| `domains/game/examples/beacon-relay/art/enemyFlyingAlt_2.png.import` | other | 955 | — | `f2f8f6aa963e` |  |
| `domains/game/examples/beacon-relay/art/enemySwimming_1.png` | media | 1981 | — | `93edec676cc4` |  |
| `domains/game/examples/beacon-relay/art/enemySwimming_1.png.import` | other | 953 | — | `a727cd234fee` |  |
| `domains/game/examples/beacon-relay/art/enemySwimming_2.png` | media | 1994 | — | `fb84a191fa45` |  |
| `domains/game/examples/beacon-relay/art/enemySwimming_2.png.import` | other | 953 | — | `8de62c1e00d2` |  |
| `domains/game/examples/beacon-relay/art/enemyWalking_1.png` | media | 1548 | — | `6c8784f1db27` |  |
| `domains/game/examples/beacon-relay/art/enemyWalking_1.png.import` | other | 950 | — | `a5590a63984c` |  |
| `domains/game/examples/beacon-relay/art/enemyWalking_2.png` | media | 1670 | — | `0f8f7f31763a` |  |
| `domains/game/examples/beacon-relay/art/enemyWalking_2.png.import` | other | 950 | — | `e6ccf2620091` |  |
| `domains/game/examples/beacon-relay/art/gameover.wav` | media | 423450 | — | `18693d1d1059` |  |
| `domains/game/examples/beacon-relay/art/gameover.wav.import` | other | 483 | — | `dd5c8eee4a3f` |  |
| `domains/game/examples/beacon-relay/art/playerGrey_up1.png` | media | 2803 | — | `a5caedb9a753` |  |
| `domains/game/examples/beacon-relay/art/playerGrey_up1.png.import` | other | 950 | — | `cdca3e0f14f8` |  |
| `domains/game/examples/beacon-relay/art/playerGrey_up2.png` | media | 2738 | — | `73778e8738af` |  |
| `domains/game/examples/beacon-relay/art/playerGrey_up2.png.import` | other | 950 | — | `527cf2c6092a` |  |
| `domains/game/examples/beacon-relay/art/playerGrey_walk1.png` | media | 2717 | — | `57d14c3d2faf` |  |
| `domains/game/examples/beacon-relay/art/playerGrey_walk1.png.import` | other | 956 | — | `1b2832e2a5a3` |  |
| `domains/game/examples/beacon-relay/art/playerGrey_walk2.png` | media | 2961 | — | `245f2ae01ca6` |  |
| `domains/game/examples/beacon-relay/art/playerGrey_walk2.png.import` | other | 956 | — | `732d5609a845` |  |
| `domains/game/examples/beacon-relay/capture.gd` | core | 924 | 25 | `e35f61d2e51c` |  |
| `domains/game/examples/beacon-relay/capture.gd.uid` | other | 20 | — | `22ec0c52a326` |  |
| `domains/game/examples/beacon-relay/export_presets.cfg` | config | 1006 | 45 | `04ed49b4fd36` |  |
| `domains/game/examples/beacon-relay/fonts/FONTLOG.txt` | other | 8394 | 253 | `025f35aaa570` |  |
| `domains/game/examples/beacon-relay/fonts/LICENSE.txt` | other | 4388 | 94 | `0e18b49e25c5` |  |
| `domains/game/examples/beacon-relay/fonts/Xolonium-Regular.ttf` | other | 229584 | — | `d6453340972b` |  |
| `domains/game/examples/beacon-relay/fonts/Xolonium-Regular.ttf.import` | other | 779 | — | `a705f07d112a` |  |
| `domains/game/examples/beacon-relay/hud.gd` | core | 788 | 32 | `fc0a90c90a06` |  |
| `domains/game/examples/beacon-relay/hud.gd.uid` | other | 19 | — | `eefff5663494` |  |
| `domains/game/examples/beacon-relay/hud.tscn` | other | 2422 | — | `fbeef8d16c24` |  |
| `domains/game/examples/beacon-relay/icon.webp` | media | 7106 | — | `d124fedc52aa` |  |
| `domains/game/examples/beacon-relay/icon.webp.import` | other | 919 | — | `7961c2d5286a` |  |
| `domains/game/examples/beacon-relay/main.gd` | core | 4019 | 107 | `697d41539992` |  |
| `domains/game/examples/beacon-relay/main.gd.uid` | other | 20 | — | `566f15ca15ac` |  |
| `domains/game/examples/beacon-relay/main.tscn` | other | 2762 | — | `a742e63db61c` |  |
| `domains/game/examples/beacon-relay/mob.gd` | core | 258 | 10 | `bcf3fe2b8fa4` |  |
| `domains/game/examples/beacon-relay/mob.gd.uid` | other | 20 | — | `1a532b1a0bd4` |  |
| `domains/game/examples/beacon-relay/mob.tscn` | other | 2013 | — | `555476c13c7e` |  |
| `domains/game/examples/beacon-relay/player.gd` | core | 1330 | 54 | `87f4fcf7481d` |  |
| `domains/game/examples/beacon-relay/player.gd.uid` | other | 19 | — | `d828b54be9f0` |  |
| `domains/game/examples/beacon-relay/player.tscn` | other | 2147 | — | `67e73b55ca0b` |  |
| `domains/game/examples/beacon-relay/project.godot` | other | 5279 | — | `5aa9e26a4036` |  |
| `domains/game/examples/beacon-relay/relay_plan.gd` | core | 352 | 9 | `ca7f86273b56` |  |
| `domains/game/examples/beacon-relay/relay_plan.gd.uid` | other | 19 | — | `d124e16254ef` |  |
| `domains/game/examples/beacon-relay/relay_plan.tres` | other | 308 | — | `ceffdf51f533` |  |
| `domains/game/examples/beacon-relay/relay_sites.gd` | core | 1102 | 29 | `e0547b2ea4d4` |  |
| `domains/game/examples/beacon-relay/relay_sites.gd.uid` | other | 20 | — | `aca32022b189` |  |
| `domains/game/examples/beacon-relay/screenshots/.gdignore` | other | 0 | — | `e3b0c44298fc` |  |
| `domains/game/examples/beacon-relay/screenshots/gameplay.png` | media | 17553 | — | `0a055500185f` |  |
| `domains/game/examples/kenney-visual-composition/.gitignore` | other | 8 | — | `531d0d253cec` |  |
| `domains/game/examples/kenney-visual-composition/README.md` | docs | 2866 | 52 | `b781c3109867` |  |
| `domains/game/examples/kenney-visual-composition/acceptance.gd` | core | 2233 | 53 | `4a4320df300c` |  |
| `domains/game/examples/kenney-visual-composition/acceptance.gd.uid` | other | 20 | — | `606cf5fbf199` |  |
| `domains/game/examples/kenney-visual-composition/alternate_avatar.tscn` | other | 250 | — | `a541bfca0cac` |  |
| `domains/game/examples/kenney-visual-composition/assets/kenney/player_blue_stand.png` | media | 491 | — | `b5c4268e846f` |  |
| `domains/game/examples/kenney-visual-composition/assets/kenney/player_blue_stand.png.import` | other | 968 | — | `ac8d2335c0d0` |  |
| `domains/game/examples/kenney-visual-composition/assets/kenney/player_green_stand.png` | media | 468 | — | `0a185f900898` |  |
| `domains/game/examples/kenney-visual-composition/assets/kenney/player_green_stand.png.import` | other | 972 | — | `a18b043467a0` |  |
| `domains/game/examples/kenney-visual-composition/main.tscn` | other | 307 | — | `0e8085a3a4f5` |  |
| `domains/game/examples/kenney-visual-composition/project.godot` | other | 357 | — | `737b6791ee48` |  |
| `domains/game/examples/native-composition/README.md` | docs | 6668 | 104 | `31ce02f81ba7` |  |
| `domains/game/examples/native-composition/assert.gd` | core | 9224 | 174 | `f182400f7321` |  |
| `domains/game/examples/native-composition/assert_audio.gd` | core | 5755 | 97 | `ff5cd208938b` |  |
| `domains/game/examples/native-composition/assets/kenney-ui-art/button_rectangle_depth_border.png` | media | 411 | — | `19dd881d5c38` |  |
| `domains/game/examples/native-composition/assets/kenney-ui-audio/LICENSE.txt` | other | 459 | 21 | `d3727df992b5` |  |
| `domains/game/examples/native-composition/assets/kenney-ui-audio/README.md` | docs | 1942 | 14 | `a3d636bff05c` |  |
| `domains/game/examples/native-composition/assets/kenney-ui-audio/click1.wav` | media | 18254 | — | `dd90b97f38b0` |  |
| `domains/game/examples/native-composition/assets/kenney-ui-audio/click2.wav` | media | 10062 | — | `a8b35cb35ff4` |  |
| `domains/game/examples/native-composition/composition_root.gd` | core | 1738 | 37 | `e4b82499b100` |  |
| `domains/game/examples/native-composition/configs/base.tres` | other | 245 | — | `d42f1126029a` |  |
| `domains/game/examples/native-composition/configs/player_variant.tres` | other | 245 | — | `47791904ddac` |  |
| `domains/game/examples/native-composition/grid_config.gd` | core | 930 | 23 | `889fc134617c` |  |
| `domains/game/examples/native-composition/grid_rules.gd` | core | 2570 | 70 | `5c77e003a349` |  |
| `domains/game/examples/native-composition/grid_state_view.gd` | core | 630 | 17 | `db49e435c9c2` |  |
| `domains/game/examples/native-composition/grid_state_view.tscn` | other | 596 | — | `bba6959eaa73` |  |
| `domains/game/examples/native-composition/grid_state_view_variant.tscn` | other | 498 | — | `0ed599b5e0e4` |  |
| `domains/game/examples/native-composition/main.tscn` | other | 655 | — | `4a9fa9e0700c` |  |
| `domains/game/examples/native-composition/movement_audio_feedback.gd` | core | 562 | 17 | `5ab2119bd62e` |  |
| `domains/game/examples/native-composition/project.godot` | other | 424 | — | `f34c2bd4e78e` |  |
| `domains/game/examples/orbit-collector/Cargo.lock` | config | 124236 | — | `2c568e328673` |  |
| `domains/game/examples/orbit-collector/Cargo.toml` | config | 701 | 24 | `050399b54c25` |  |
| `domains/game/examples/orbit-collector/README.md` | docs | 4651 | 81 | `e8ce7394580e` |  |
| `domains/game/examples/orbit-collector/src/gameplay.rs` | core | 9498 | 299 | `76f0bc6df849` |  |
| `domains/game/examples/orbit-collector/src/main.rs` | core | 481 | 19 | `e38517b79d05` |  |
| `domains/game/examples/orbit-collector/src/rules.rs` | core | 5547 | 187 | `dfd8f21e545c` |  |
| `domains/game/examples/room-encounter/.gitignore` | other | 8 | — | `531d0d253cec` |  |
| `domains/game/examples/room-encounter/README.md` | docs | 15398 | 233 | `739ea91feac3` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/DialogueManager.cs` | core | 49017 | 1264 | `57c2021af061` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/DialogueManager.cs.uid` | other | 20 | — | `7ab9a28c42b6` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/LICENSE` | other | 1111 | — | `21c98fa971b5` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/cue.svg` | media | 2439 | — | `4a28ce898daa` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/cue.svg.import` | other | 1068 | — | `5ff3c90c5a5c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/icon.svg` | media | 3970 | — | `ec2483b06d70` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/icon.svg.import` | other | 1070 | — | `7f23a5f2c633` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/logo.svg` | media | 10376 | — | `7173842be321` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/logo.svg.import` | other | 1044 | — | `53f2c34a7dae` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/region.svg` | media | 2192 | — | `7c6a93632300` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/region.svg.import` | other | 1076 | — | `649af6528a19` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/resource.svg` | media | 3826 | — | `d796f040c57c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/resource.svg.import` | other | 1083 | — | `014211cccfda` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/update.svg` | media | 5285 | — | `ca44f2575155` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/assets/update.svg.import` | other | 1050 | — | `d7f4b66380ec` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/compilation.gd` | core | 39933 | 1073 | `a173ca926e7b` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/compilation.gd.uid` | other | 20 | — | `b8401f406cac` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/compiled_line.gd` | core | 4465 | 161 | `5057f516ecbc` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/compiled_line.gd.uid` | other | 20 | — | `35a121d5ed1e` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/compiler.gd` | core | 2053 | 57 | `fefa68ba4105` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/compiler.gd.uid` | other | 20 | — | `6830e7bfbc12` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/compiler_regex.gd` | core | 3962 | 50 | `d8e9f8a97cae` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/compiler_regex.gd.uid` | other | 20 | — | `5f8f8564453d` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/compiler_result.gd` | core | 618 | 24 | `81108a26012d` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/compiler_result.gd.uid` | other | 20 | — | `e36cd85462ea` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/expression_parser.gd` | core | 16177 | 529 | `d9b1e888c2e9` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/expression_parser.gd.uid` | other | 20 | — | `ddf1ba8c4a05` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/resolved_goto_data.gd` | core | 2115 | 70 | `97ab542ef235` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/resolved_goto_data.gd.uid` | other | 19 | — | `832e915957a0` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/resolved_line_data.gd` | core | 5532 | 170 | `d63cb2ab721c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/resolved_line_data.gd.uid` | other | 19 | — | `d154ef43550e` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/resolved_tag_data.gd` | core | 869 | 26 | `5953fc885ebc` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/resolved_tag_data.gd.uid` | other | 20 | — | `52f430f30d46` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/tree_line.gd` | core | 1614 | 46 | `3ebc16b66ed5` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/compiler/tree_line.gd.uid` | other | 20 | — | `055afe36661a` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/blank_slate.gd` | core | 1556 | 56 | `2cf599fa2d8c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/blank_slate.gd.uid` | other | 19 | — | `2e8ce619064b` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/blank_slate.tscn` | other | 2440 | — | `e6b88d8ce947` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/code_edit.gd` | core | 52444 | 1508 | `a0646e1a2105` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/code_edit.gd.uid` | other | 20 | — | `f6b61e023e93` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/code_edit.tscn` | other | 1982 | — | `5cc9211cdb06` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/code_edit_syntax_highlighter.gd` | core | 10805 | 255 | `aa31430ea2bd` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/code_edit_syntax_highlighter.gd.uid` | other | 19 | — | `f075f082cee0` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/cue_editor_property/editor_property.gd` | core | 862 | 43 | `b277e79590f2` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/cue_editor_property/editor_property.gd.uid` | other | 20 | — | `c580522aca66` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/cue_editor_property/editor_property_control.gd` | core | 3838 | 142 | `30fc0fb689fe` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/cue_editor_property/editor_property_control.gd.uid` | other | 20 | — | `5ae99d6cdbd6` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/cue_editor_property/editor_property_control.tscn` | other | 1651 | — | `bb5e7b119358` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/cue_list.gd` | core | 3904 | 131 | `8c126bdfb08b` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/cue_list.gd.uid` | other | 20 | — | `300a3edfd0fd` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/cue_list.tscn` | other | 1385 | — | `7fd9f4a79639` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/dialogue_editor_property/editor_property.gd` | core | 1008 | 42 | `b1b1e763fa98` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/dialogue_editor_property/editor_property.gd.uid` | other | 19 | — | `44e44c49b268` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/dialogue_editor_property/editor_property_control.gd` | core | 3743 | 146 | `63ca6cf22557` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/dialogue_editor_property/editor_property_control.gd.uid` | other | 20 | — | `0c05cd563560` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/dialogue_editor_property/editor_property_control.tscn` | other | 2875 | — | `e57614b99791` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/dialogue_editor_property/resource_button.gd` | core | 1484 | 48 | `b1b29512f809` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/dialogue_editor_property/resource_button.gd.uid` | other | 20 | — | `048c5bf1e932` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/dialogue_editor_property/resource_button.tscn` | other | 348 | — | `03c409b74e65` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/download_update_panel.gd` | core | 2450 | 85 | `d90db8e19471` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/download_update_panel.gd.uid` | other | 19 | — | `2e5a59a241b0` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/download_update_panel.tscn` | other | 1916 | — | `b90cd6b29b97` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/errors_panel.gd` | core | 2183 | 83 | `80716a5d18c6` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/errors_panel.gd.uid` | other | 20 | — | `07cb98e9c29b` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/errors_panel.tscn` | other | 6252 | — | `5d90b936325c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/export_to_csv_dialog.gd` | core | 2825 | 100 | `08c4caa2d108` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/export_to_csv_dialog.gd.uid` | other | 20 | — | `017074748074` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/export_to_csv_dialog.tscn` | other | 3436 | — | `d76fc97478ee` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/files_list.gd` | core | 3932 | 151 | `3daa7193d0d5` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/files_list.gd.uid` | other | 20 | — | `c9505c7f4fec` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/files_list.tscn` | other | 1137 | — | `e1ca39e6370c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/preview_generator.gd` | core | 546 | 22 | `21c76397dbc2` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/preview_generator.gd.uid` | other | 20 | — | `5d2f49bfc027` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/search_and_replace.gd` | core | 6181 | 219 | `d217d3781061` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/search_and_replace.gd.uid` | other | 20 | — | `f47f0bf70af0` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/search_and_replace.tscn` | other | 3146 | — | `0a5baff3f196` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/update_button.gd` | core | 4147 | 126 | `16b414b44888` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/update_button.gd.uid` | other | 20 | — | `b1770abce718` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/components/update_button.tscn` | other | 1998 | — | `798286f40c53` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/constants.gd` | core | 9101 | 235 | `311f1fe5111d` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/constants.gd.uid` | other | 20 | — | `1fe86d4b9ee6` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/debugger_plugin.gd` | core | 1868 | 83 | `525a626cfe66` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/debugger_plugin.gd.uid` | other | 20 | — | `bea104a0903a` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_line.gd` | core | 5108 | 147 | `7d6f67e15233` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_line.gd.uid` | other | 19 | — | `84a62ce5e3ee` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_manager.gd` | core | 76525 | 2009 | `43aa046e2692` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_manager.gd.uid` | other | 20 | — | `079d4b3de2c0` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_processor.gd` | core | 276 | 11 | `b6d4a0c6a5f5` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_processor.gd.uid` | other | 19 | — | `da7f416cfad7` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_resource.gd` | core | 1349 | 40 | `45f82c106b02` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_resource.gd.uid` | other | 20 | — | `1cb23bf8b5b9` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_response.gd` | core | 2136 | 76 | `2c1731d257e5` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_response.gd.uid` | other | 20 | — | `a2cd3385b6c1` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/editor_translation_parser_plugin.gd` | core | 2622 | 81 | `e3d212ba287a` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/editor_translation_parser_plugin.gd.uid` | other | 20 | — | `bd01d68bba4b` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/example_balloon/ExampleBalloon.cs` | core | 7354 | 278 | `8945e0dfea48` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/example_balloon/ExampleBalloon.cs.uid` | other | 19 | — | `0699aceb82d4` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/example_balloon/ExampleBalloon.tscn` | other | 7149 | — | `d060b9de012d` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/example_balloon/SmallExampleBalloon.tscn` | other | 7044 | — | `2692de1e0b9b` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/example_balloon/example_balloon.gd` | core | 7292 | 227 | `a9537502daf9` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/example_balloon/example_balloon.gd.uid` | other | 20 | — | `2a23415966d4` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/example_balloon/example_balloon.tscn` | other | 7389 | — | `d1ff4d78aacf` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/example_balloon/small_example_balloon.tscn` | other | 7238 | — | `3bd12ef417b2` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/export_plugin.gd` | core | 1017 | 38 | `8f184401c50a` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/export_plugin.gd.uid` | other | 19 | — | `1d10726c6d94` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/import_plugin.gd` | core | 3228 | 117 | `b2836c64f5ca` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/import_plugin.gd.uid` | other | 20 | — | `adde7ffc6ae7` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/inspector_plugin.gd` | core | 1063 | 26 | `385dfb904a21` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/inspector_plugin.gd.uid` | other | 19 | — | `05e9a5072366` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/l10n/en.po` | other | 12994 | — | `b25422b36d11` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/l10n/es.po` | other | 9247 | — | `cdc1c2044643` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/l10n/translations.pot` | other | 7467 | — | `27eed4e4bf4e` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/l10n/uk.po` | other | 14616 | — | `58a1b5d10b2c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/l10n/zh.po` | other | 10173 | — | `d859c1ad1b87` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/l10n/zh_TW.po` | other | 8129 | — | `712be3b94f44` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/DialogueActionable2D.cs` | core | 4658 | 141 | `ef25b55ae890` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/DialogueActionable2D.cs.uid` | other | 20 | — | `606161df9b05` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/DialogueActionable3D.cs` | core | 4659 | 141 | `357edd8d04e9` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/DialogueActionable3D.cs.uid` | other | 19 | — | `3bb315050988` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/dialogue_actionable_2d.gd` | core | 2900 | 82 | `966b000bbdb2` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/dialogue_actionable_2d.gd.uid` | other | 20 | — | `33b8fd69d323` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/dialogue_actionable_2d.svg` | media | 2760 | — | `3db802a2eb10` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/dialogue_actionable_2d.svg.import` | other | 1133 | — | `e0ae833354ec` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/dialogue_actionable_3d.gd` | core | 2901 | 82 | `af078e613d0f` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/dialogue_actionable_3d.gd.uid` | other | 20 | — | `c818e796177a` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/dialogue_actionable_3d.svg` | media | 2719 | — | `e79530900756` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/actionable/dialogue_actionable_3d.svg.import` | other | 1134 | — | `033072755272` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/context/DialogueStateContext.cs` | core | 2986 | 103 | `78869308ea12` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/context/DialogueStateContext.cs.uid` | other | 20 | — | `06f099f54211` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/context/dialogue_state_context.gd` | core | 2117 | 69 | `4974c4bc71e0` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/context/dialogue_state_context.gd.uid` | other | 20 | — | `bae91a93bff6` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/context/dialogue_state_context.svg` | media | 3415 | — | `c654b8a7e7b6` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/context/dialogue_state_context.svg.import` | other | 1131 | — | `5d6b313e93bd` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/dialogue_label/DialogueLabel.cs` | core | 12328 | 356 | `e93e498a64c1` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/dialogue_label/DialogueLabel.cs.uid` | other | 20 | — | `c972d4dfb47c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/dialogue_label/DialogueLabel.tscn` | other | 649 | — | `7bf58c6cf7bc` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/dialogue_label/dialogue_label.gd` | core | 7860 | 228 | `1a31a692f25e` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/dialogue_label/dialogue_label.gd.uid` | other | 19 | — | `0b76251d186c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/dialogue_label/dialogue_label.svg` | media | 1949 | — | `f83d89f92819` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/dialogue_label/dialogue_label.svg.import` | other | 1113 | — | `f38898e46b82` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/dialogue_label/dialogue_label.tscn` | other | 673 | — | `23e79e6d267c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/DialogueMarker2D.cs` | core | 2051 | 79 | `a2babed0d4c4` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/DialogueMarker2D.cs.uid` | other | 20 | — | `88b039182343` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/DialogueMarker3D.cs` | core | 2268 | 87 | `062d5d8784d2` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/DialogueMarker3D.cs.uid` | other | 20 | — | `0e171728110b` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/dialogue_marker_2d.gd` | core | 1215 | 46 | `d261f3e1cc14` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/dialogue_marker_2d.gd.uid` | other | 20 | — | `e4d2b2eb7bb3` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/dialogue_marker_2d.svg` | media | 1161 | — | `5448dcf2d9c3` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/dialogue_marker_2d.svg.import` | other | 1118 | — | `5e62dbd7df76` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/dialogue_marker_3d.gd` | core | 1332 | 50 | `2fc46f2ee3b5` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/dialogue_marker_3d.gd.uid` | other | 20 | — | `f706a5173ccc` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/dialogue_marker_3d.svg` | media | 1104 | — | `eab22636c7f6` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/marker/dialogue_marker_3d.svg.import` | other | 1118 | — | `fc50e4e3eaf9` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/responses_menu/DialogueResponsesMenu.cs` | core | 9901 | 318 | `63c056c6e850` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/responses_menu/DialogueResponsesMenu.cs.uid` | other | 20 | — | `7e03fcbef8ce` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/responses_menu/dialogue_responses_menu.gd` | core | 5445 | 197 | `2c39c712f175` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/responses_menu/dialogue_responses_menu.gd.uid` | other | 20 | — | `c82dc6b07454` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/responses_menu/dialogue_responses_menu.svg` | media | 1255 | — | `cd748f34361d` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/nodes/responses_menu/dialogue_responses_menu.svg.import` | other | 1141 | — | `9213957de5bb` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/plugin.cfg` | config | 141 | 7 | `413fee5e077c` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/plugin.cfg.uid` | other | 19 | — | `7567096804dd` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/plugin.gd` | core | 17667 | 519 | `d316bb2c9721` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/plugin.gd.uid` | other | 20 | — | `41dd74f6c7ec` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/settings.gd` | core | 10259 | 307 | `549a472e373f` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/settings.gd.uid` | other | 20 | — | `67994fa3b7b1` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/test_scene.gd` | tests | 1178 | 33 | `90af546838b5` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/test_scene.gd.uid` | tests | 20 | — | `fb46fc1cea2f` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/test_scene.tscn` | tests | 249 | — | `b31acd01b3cf` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/builtins.gd` | core | 11535 | 532 | `febf2a0f7319` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/builtins.gd.uid` | other | 20 | — | `c95276016433` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/dialogue_cache.gd` | core | 7611 | 236 | `834ddaa8b0f8` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/dialogue_cache.gd.uid` | other | 20 | — | `5b6d476d38e8` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/error.gd` | core | 284 | 11 | `bac365de2450` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/error.gd.uid` | other | 19 | — | `1fa4e9c67f62` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/theme_values.gd` | core | 4181 | 92 | `8f6ea9a61130` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/theme_values.gd.uid` | other | 20 | — | `300476b36b51` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/translations.gd` | core | 5929 | 163 | `f573c1df143e` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/translations.gd.uid` | other | 20 | — | `2abe02bc51f4` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/waiter.gd` | core | 800 | 35 | `81fba20af61a` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/utilities/waiter.gd.uid` | other | 20 | — | `c1beb0b7b8b7` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/views/debugger_view.gd` | core | 5723 | 198 | `2565e458ac6f` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/views/debugger_view.gd.uid` | other | 20 | — | `478575d0c2b0` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/views/debugger_view.tscn` | other | 2484 | — | `a76ba9037176` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/views/find_in_dialogue_view.gd` | core | 7901 | 230 | `3398c7600e26` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/views/find_in_dialogue_view.gd.uid` | other | 19 | — | `d497bbcd985d` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/views/find_in_dialogue_view.tscn` | other | 5228 | — | `f0603b4a049e` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/views/find_in_dialogue_view_result_template.tscn` | other | 726 | — | `8268d5039683` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/views/main_view.gd` | core | 27985 | 846 | `d2e6d7032bce` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/views/main_view.gd.uid` | other | 20 | — | `158077448303` |  |
| `domains/game/examples/room-encounter/addons/dialogue_manager/views/main_view.tscn` | other | 26327 | — | `fa3b6b54f350` |  |
| `domains/game/examples/room-encounter/agent_episode.gd` | core | 7898 | 175 | `52ad0809b974` |  |
| `domains/game/examples/room-encounter/agent_episode.gd.uid` | other | 20 | — | `1c361611e94c` |  |
| `domains/game/examples/room-encounter/agent_episode_acceptance.py` | core | 12147 | 217 | `c80a26cfd36b` |  |
| `domains/game/examples/room-encounter/assert.gd` | core | 20683 | 349 | `39289459745d` |  |
| `domains/game/examples/room-encounter/assert.gd.uid` | other | 20 | — | `8695ad40312d` |  |
| `domains/game/examples/room-encounter/assert_process_restart.gd` | core | 3899 | 86 | `9a5ee642ecba` |  |
| `domains/game/examples/room-encounter/assert_process_restart.gd.uid` | other | 20 | — | `05c51e28a1c6` |  |
| `domains/game/examples/room-encounter/assets/LICENSE.txt` | other | 458 | 21 | `f713b09eab56` |  |
| `domains/game/examples/room-encounter/assets/README.md` | docs | 944 | 14 | `4e5bf6c078f3` |  |
| `domains/game/examples/room-encounter/assets/click1.wav` | media | 18254 | — | `dd90b97f38b0` |  |
| `domains/game/examples/room-encounter/assets/click1.wav.import` | other | 482 | — | `efb95bde991f` |  |
| `domains/game/examples/room-encounter/assets/click2.wav` | media | 10062 | — | `a8b35cb35ff4` |  |
| `domains/game/examples/room-encounter/assets/click2.wav.import` | other | 483 | — | `3fc1c63730ec` |  |
| `domains/game/examples/room-encounter/configs/default.tres` | other | 359 | — | `9970b403fe35` |  |
| `domains/game/examples/room-encounter/configs/tactical_trial.tres` | other | 381 | — | `fd36371249b9` |  |
| `domains/game/examples/room-encounter/configs/variant.tres` | other | 355 | — | `fb17ce47b3e6` |  |
| `domains/game/examples/room-encounter/encounter_audio_feedback.gd` | core | 354 | 12 | `b6fc2c2c3e60` |  |
| `domains/game/examples/room-encounter/encounter_audio_feedback.gd.uid` | other | 20 | — | `10da2c8cc2ca` |  |
| `domains/game/examples/room-encounter/encounter_root.gd` | core | 3216 | 92 | `c1fe49a9c573` |  |
| `domains/game/examples/room-encounter/encounter_root.gd.uid` | other | 20 | — | `d47ffc3be1ad` |  |
| `domains/game/examples/room-encounter/encounter_rules.gd` | core | 8948 | 230 | `d85138c07628` |  |
| `domains/game/examples/room-encounter/encounter_rules.gd.uid` | other | 20 | — | `b525f37f975e` |  |
| `domains/game/examples/room-encounter/encounter_save_slot.gd` | core | 722 | 19 | `b8259c37ed3a` |  |
| `domains/game/examples/room-encounter/encounter_save_slot.gd.uid` | other | 19 | — | `2fd02290878c` |  |
| `domains/game/examples/room-encounter/encounter_tuning.gd` | core | 479 | 14 | `efaa77174164` |  |
| `domains/game/examples/room-encounter/encounter_tuning.gd.uid` | other | 20 | — | `c05ed878ca84` |  |
| `domains/game/examples/room-encounter/encounter_view.gd` | core | 5205 | 108 | `1a3ca96b5e63` |  |
| `domains/game/examples/room-encounter/encounter_view.gd.uid` | other | 20 | — | `2a1553b811ac` |  |
| `domains/game/examples/room-encounter/encounter_view.tscn` | other | 2289 | — | `25f20c161ac3` |  |
| `domains/game/examples/room-encounter/encounter_view_variant.tscn` | other | 2269 | — | `bc3eaa5b7573` |  |
| `domains/game/examples/room-encounter/export_presets.cfg` | config | 1110 | 45 | `ecc1f87cc3d1` |  |
| `domains/game/examples/room-encounter/main.tscn` | other | 1399 | — | `bda07a24893c` |  |
| `domains/game/examples/room-encounter/narrative/acceptance.gd` | core | 3086 | 72 | `3d4b75c60c45` |  |
| `domains/game/examples/room-encounter/narrative/acceptance.gd.uid` | other | 20 | — | `92544c83cd33` |  |
| `domains/game/examples/room-encounter/narrative/encounter_dialogue.gd` | core | 3358 | 88 | `0aa605b51364` |  |
| `domains/game/examples/room-encounter/narrative/encounter_dialogue.gd.uid` | other | 20 | — | `3e194ad63c8c` |  |
| `domains/game/examples/room-encounter/narrative/encounter_dialogue.tscn` | other | 736 | — | `9c5d57eb4069` |  |
| `domains/game/examples/room-encounter/narrative/gate.dialogue` | other | 273 | — | `e63da5af3c4c` |  |
| `domains/game/examples/room-encounter/narrative/gate.dialogue.import` | other | 347 | — | `3e4e759fb6c5` |  |
| `domains/game/examples/room-encounter/narrative/gate_state.gd` | core | 470 | 17 | `19f10c74d860` |  |
| `domains/game/examples/room-encounter/narrative/gate_state.gd.uid` | other | 20 | — | `8643a4f4eddc` |  |
| `domains/game/examples/room-encounter/native_scene_acceptance.py` | core | 3537 | 77 | `4d0a91df2604` |  |
| `domains/game/examples/room-encounter/project.godot` | other | 558 | — | `c70369cd7bc3` |  |
| `domains/game/examples/room-encounter/room_theme.tres` | other | 2277 | — | `f11066e2ab39` |  |
| `domains/game/examples/room-encounter/visual_capture.gd` | core | 4900 | 102 | `a618230e9f77` |  |
| `domains/game/examples/room-encounter/visual_capture.gd.uid` | other | 20 | — | `7c087b6e0cf9` |  |
| `domains/game/formal/README.md` | docs | 4473 | 83 | `052525cb43b5` |  |
| `domains/game/formal/verify_orbit_rules.py` | core | 3425 | 89 | `ec1e84883ef7` |  |
| `domains/game/formal/verify_room_arithmetic.py` | core | 6942 | 146 | `e530e3452d35` |  |
| `domains/game/knowledge/game_counterexample_synthesis_r1.json` | config | 12403 | 230 | `d0a7f6530ee0` | 1 |
| `domains/game/knowledge/game_design_counterexample_memory_r1.json` | config | 72768 | 1173 | `5cde2cbfd7c1` | 1 |
| `domains/game/knowledge/game_external_knowledge_base_r1.json` | config | 168988 | 4165 | `e33d313d8bfb` | 1 |
| `domains/game/knowledge/game_external_skill_watchlist_r1.json` | config | 8854 | 215 | `c78ac6e5e925` | 1 |
| `domains/game/knowledge/game_mechanism_experience_library_r1.json` | config | 197498 | 4094 | `8337e678811f` | 1 |
| `domains/game/knowledge/game_mechanism_relationship_spec_r1.json` | config | 35140 | 277 | `96add0857151` | 1 |
| `domains/game/knowledge/game_teardown_queue_r1.json` | config | 46404 | 1428 | `d684653adb85` | 1 |
| `domains/game/mise.toml` | config | 9903 | 202 | `869c2e5cc182` |  |
| `domains/game/package.json` | config | 963 | 27 | `25b343b7e240` |  |
| `domains/game/planning/lego-plan-r1.json` | config | 37028 | 831 | `cba8b4343c4d` | 1 |
| `domains/game/pnpm-lock.yaml` | config | 12616 | 398 | `36805def1867` |  |
| `domains/game/research/autonomous-interest-r7/build_manifest_reference.py` | research | 5441 | 132 | `270f88074670` |  |
| `domains/game/research/autonomous-interest-r7/evaluator_reference.py` | research | 27961 | 601 | `009467f6d27b` |  |
| `domains/game/research/autonomous-interest-r7/protocol_selftest.py` | research | 17531 | 295 | `68c229171015` |  |
| `domains/game/research/autonomous-interest-r7/renderer_reference.py` | research | 12219 | 214 | `3ad0516869d0` |  |
| `domains/game/research/autonomous-interest-r7/selection_reference.py` | research | 5999 | 127 | `889df47bcb12` |  |
| `domains/game/research/autonomous-interest-r7/selftest_model.json` | research | 4397 | 264 | `afd197d6d3c7` | 1 |
| `domains/game/research/autonomous-interest-r7/study_runner_reference.py` | research | 19530 | 397 | `24ec4540a9c2` |  |
| `domains/game/scripts/cli-argument.ts` | core | 1101 | 25 | `4b10f732043f` |  |
| `domains/game/scripts/counterexample-synthesis-query.ts` | core | 4391 | 105 | `bb986ec5db9b` |  |
| `domains/game/scripts/design-counterexample-query.ts` | core | 3074 | 79 | `19558cd319b3` |  |
| `domains/game/scripts/external-knowledge-query.ts` | core | 3071 | 86 | `490be388e17c` |  |
| `domains/game/scripts/mechanism-experience-query.ts` | core | 2829 | 71 | `507ee76097fb` |  |
| `domains/game/scripts/mechanism-relationship-query.ts` | core | 4398 | 110 | `ab3e1b815b7f` |  |
| `domains/game/scripts/package_orbit_linux.sh` | core | 3366 | 55 | `d19796d0d5bd` |  |
| `domains/game/scripts/test_orbit_package_contract.py` | tests | 2988 | 75 | `a80727eea1fd` |  |
| `domains/game/src/counterexample-projection.ts` | core | 2910 | 85 | `728d85211ca9` |  |
| `domains/game/src/knowledge-file.ts` | core | 597 | 14 | `5ba6a3db220c` |  |
| `domains/game/src/mechanism-relationship-graph.ts` | core | 6149 | 135 | `9593d7d13391` |  |
| `domains/game/src/query-input.ts` | core | 564 | 13 | `11404806a8b4` |  |
| `domains/game/test/game-cli-argument.test.ts` | core | 849 | 15 | `e9fa40fb92d0` |  |
| `domains/game/test/game-counterexample-projection.test.ts` | core | 1844 | 38 | `fd43e60c3743` |  |
| `domains/game/test/game-design-counterexample-memory.test.ts` | core | 4717 | 88 | `a1c05146c6a2` |  |
| `domains/game/test/game-external-knowledge-base.test.ts` | core | 4958 | 87 | `093f2f79380c` |  |
| `domains/game/test/game-external-knowledge-query.test.ts` | core | 1893 | 33 | `45c1b3b37a3f` |  |
| `domains/game/test/game-lego-catalog.test.ts` | core | 8659 | 130 | `bada7cc7a219` |  |
| `domains/game/test/game-mechanism-experience-library.test.ts` | core | 5452 | 97 | `71ed52d5e791` |  |
| `domains/game/test/game-mechanism-relationship-graph.test.ts` | core | 7891 | 140 | `b515c684e547` |  |
| `domains/game/test/game-query-input.test.ts` | core | 931 | 21 | `c974c5f389df` |  |
| `domains/game/tsconfig.json` | config | 499 | 26 | `f637051da72b` |  |

### capital — domains/capital/（399 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `domains/capital/.gitignore` | other | 268 | — | `a6c60fde65b7` |  |
| `domains/capital/.python-version` | other | 7 | — | `fd81c059718a` |  |
| `domains/capital/README.md` | docs | 31620 | 438 | `2573bd27c6fb` |  |
| `domains/capital/artifacts/.gitkeep` | other | 0 | — | `e3b0c44298fc` |  |
| `domains/capital/config/accounting_substrate.json` | config | 1384 | 36 | `44cf19f32f89` | 1 |
| `domains/capital/config/binance_usdm_equity_perp_provider.json` | config | 6808 | 168 | `0ae0bc6f3085` | 2 |
| `domains/capital/config/candidate_tool_surface_registry.json` | config | 2485 | 63 | `f370802e5be0` | 1 |
| `domains/capital/config/capability_dependencies.json` | config | 5775 | 85 | `000e3868575a` | 1 |
| `domains/capital/config/capital_domain_taxonomy.json` | config | 8361 | 195 | `24b95967c6c8` | 1 |
| `domains/capital/config/clock_quality_gate.json` | config | 822 | 17 | `9f463c72296c` | 2 |
| `domains/capital/config/crypto_data_adapters.json` | config | 2142 | 49 | `20a11047967c` | 2 |
| `domains/capital/config/demo_execution_policy.json` | config | 1586 | 39 | `3ca042e04cae` | 2 |
| `domains/capital/config/execution_feasibility.json` | config | 919 | 13 | `9d5ff1510060` | 2 |
| `domains/capital/config/execution_policy.json` | config | 426 | 8 | `c0fa32dbc48f` | 2 |
| `domains/capital/config/external_candidate_funnel.json` | config | 11229 | 222 | `328bdcd9f9a5` | 1 |
| `domains/capital/config/external_owner_census.json` | config | 95208 | 1901 | `344991acfd58` | 1 |
| `domains/capital/config/fix_order_semantics.json` | config | 1162 | 32 | `06608b49c036` | 2 |
| `domains/capital/config/historical_validation_data.json` | config | 837 | 24 | `87f6f881eaaa` | 2 |
| `domains/capital/config/language_baseline.json` | config | 1172 | 29 | `040e95deb477` | 1 |
| `domains/capital/config/lean_runtime.json` | config | 2684 | 81 | `cdcf10a9585f` | 2 |
| `domains/capital/config/legacy_replay_surface_registry.json` | config | 3435 | 86 | `509edd7ec20f` | 1 |
| `domains/capital/config/live_test_account_policy.json` | config | 4167 | 89 | `5d8b205e4d8f` | 2 |
| `domains/capital/config/network_v2_public_data.json` | config | 3508 | 94 | `de12bc8be656` | 2 |
| `domains/capital/config/nonlive_credential_provisioning.json` | config | 1022 | 27 | `56d7b798015a` | 2 |
| `domains/capital/config/nonlive_effect_authority.json` | config | 651 | 18 | `436e9cb80860` | 2 |
| `domains/capital/config/okx_live_provider.json` | config | 3508 | 95 | `0e24522e24df` | 2 |
| `domains/capital/config/portfolio_risk_budget.json` | config | 342 | 13 | `56c835107bfb` | 2 |
| `domains/capital/config/private_reality_policy.json` | config | 5656 | 121 | `bd55480440dd` | 2 |
| `domains/capital/config/prospective_validation.json` | config | 1009 | 34 | `8069e472fa6c` | 2 |
| `domains/capital/config/protocol_identity_migration_v2.json` | config | 17548 | 462 | `a7251d227c9b` | 2 |
| `domains/capital/config/quantitative_component_inventory.json` | config | 21460 | 543 | `9d68a00d92f4` | 1 |
| `domains/capital/config/shadow_precommit.json` | config | 896 | 22 | `ab305f47de4b` | 2 |
| `domains/capital/contracts/README.md` | schemas | 1329 | 21 | `d3606ff1538d` |  |
| `domains/capital/contracts/external-boundary-v2.json` | schemas | 2438 | 88 | `48a7daac74b5` | 2 |
| `domains/capital/contracts/external-write-policy-input-v2.json` | schemas | 555 | 10 | `5e5787edaf41` | 2 |
| `domains/capital/contracts/legacy_protocol_v1/external-boundary-v1.json` | schemas | 2434 | 88 | `35ae060e6c1c` | 1 |
| `domains/capital/contracts/legacy_protocol_v1/external-write-policy-input-v1.json` | schemas | 551 | 10 | `85a0bf10e206` | 1 |
| `domains/capital/contracts/legacy_protocol_v1/nonlive-effect-admission-v1.json` | schemas | 658 | 15 | `4ca2bd0aa837` | 1 |
| `domains/capital/contracts/legacy_protocol_v1/portfolio-risk-budget-v1.schema.json` | schemas | 2289 | 66 | `8e3f18ae8787` |  |
| `domains/capital/contracts/nonlive-effect-admission-v2.json` | schemas | 960 | 22 | `0147e53ac1ca` | 2 |
| `domains/capital/contracts/parquet-materialization-readback-v1.json` | schemas | 1684 | 36 | `3178a1f1bcb2` | 1 |
| `domains/capital/contracts/portfolio-risk-budget-v2.schema.json` | schemas | 3351 | 155 | `adcb39da9dc3` |  |
| `domains/capital/contracts/production-authorization.json` | schemas | 283 | 7 | `e9a72b7a605f` | 2 |
| `domains/capital/contracts/websocket-client-mechanics-v1.json` | schemas | 1337 | 26 | `48209e0bb842` | 1 |
| `domains/capital/data-products/crypto-public-shadow-r2/acceptance.json` | config | 3696 | 59 | `ba6f3a0bc60a` | 1 |
| `domains/capital/data-products/crypto-public-shadow-r2/governance-policy.odrl.jsonld` | other | 524 | — | `99248894b157` |  |
| `domains/capital/data-products/crypto-public-shadow-r2/odcs.json` | config | 6432 | 205 | `689d9e230930` |  |
| `domains/capital/data-products/crypto-public-shadow-r2/odps.json` | config | 5946 | 191 | `00dfb43af5ec` |  |
| `domains/capital/destroyer/false-green-corpus-v0.json` | config | 872 | 17 | `fad22099f752` | 0 |
| `domains/capital/docs/ALGEBRAIC_FINANCE_POLICY_R1.md` | docs | 15027 | 226 | `d88ae70a2603` |  |
| `domains/capital/docs/ARCHITECTURE.md` | docs | 19112 | 221 | `887821cdf1db` |  |
| `domains/capital/docs/COMPOSITION_FIRST_2026-09-14.md` | docs | 7652 | 86 | `7840b6b5ca96` |  |
| `domains/capital/docs/CRYPTO_FIX44_PROJECTION_R4_2026-09-14.md` | docs | 2469 | 33 | `827ae888f022` |  |
| `domains/capital/docs/FINANCE_DIRECTORY_OWNER_AUDIT_R1.md` | docs | 10032 | 95 | `385788f48bac` |  |
| `domains/capital/docs/FINANCE_HUMAN_GUIDE_R1.md` | docs | 27397 | 359 | `1fd2b49521ce` |  |
| `domains/capital/docs/FINANCE_INVESTMENT_FIRST_R1.md` | docs | 7388 | 149 | `24a160fae642` |  |
| `domains/capital/docs/FINANCE_INVESTMENT_MODE_R2.md` | docs | 7000 | 126 | `05cb5e1cb446` |  |
| `domains/capital/docs/FINANCE_PAPER_INVESTMENT_R1.md` | docs | 12145 | 223 | `b428af798e6d` |  |
| `domains/capital/docs/FINANCE_R2_RESEARCH_BOUNDARY.md` | docs | 10161 | 179 | `3ca444142c53` |  |
| `domains/capital/docs/MARKET_SENSORS_R1.md` | docs | 3406 | 78 | `9af23eb7c751` |  |
| `domains/capital/docs/MULTISTAGE_FINANCE_R1.md` | docs | 25174 | 316 | `5be6210a65d7` |  |
| `domains/capital/docs/OKX_DEMO_EXTERNAL_EXECUTION_R1.md` | docs | 5815 | 108 | `f300c51604d1` |  |
| `domains/capital/docs/ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md` | docs | 7927 | 72 | `a392f7293b2f` |  |
| `domains/capital/docs/PAPER_ETF_EOD_SNAPSHOT_R1.md` | docs | 7311 | 133 | `dad9c933ae11` |  |
| `domains/capital/docs/PIT_JOINT_FORECAST_R1.md` | docs | 13537 | 189 | `ae3204d77432` |  |
| `domains/capital/docs/PORTFOLIO_RISK_MONITORING_R1.md` | docs | 4357 | 60 | `b47825f34f19` |  |
| `domains/capital/docs/PORTFOLIO_SCENARIO_ANALYSIS_R1.md` | docs | 2610 | 46 | `db8b90122f83` |  |
| `domains/capital/docs/UNIT_R_DCA_LONG_HISTORY_R1.md` | docs | 7943 | 115 | `91b31fb72bf7` |  |
| `domains/capital/evidence/acceptance/binance-sndk-usdm-public-canary-r1.json` | evidence | 10656 | 435 | `03243cde3144` | 1 |
| `domains/capital/evidence/acceptance/dependence-model-monitoring-r1.json` | evidence | 13460 | 323 | `9e1bcc8d9099` | 1 |
| `domains/capital/evidence/acceptance/dependence-model-oot-validation-r1.json` | evidence | 21061 | 560 | `98c9279a3809` | 1 |
| `domains/capital/evidence/acceptance/market-sensors-sndk-canary-r1.json` | evidence | 5596 | 139 | `b794d6994ae8` | 1 |
| `domains/capital/evidence/acceptance/model-monitoring-lineage-r1.json` | evidence | 1252 | 33 | `e91bc825e7f2` | 1 |
| `domains/capital/evidence/acceptance/portfolio-counterfactuals-p5-p6-r1.json` | evidence | 4355 | 112 | `16a049241065` | 1 |
| `domains/capital/evidence/acceptance/portfolio-risk-observatory-p1-p4-r1.json` | evidence | 8975 | 250 | `f07645de6538` | 1 |
| `domains/capital/evidence/clock-quality-audit-20260914-postrepair.json` | evidence | 2749 | 68 | `03e3ce1ec5ed` | 1 |
| `domains/capital/evidence/crypto-fix44-projection-r4-20260914.json` | evidence | 3049 | 80 | `6164b2a41793` | 1 |
| `domains/capital/evidence/crypto-public-shadow-r1-20260913.json` | evidence | 3780 | 98 | `028b3f82ed90` | 1 |
| `domains/capital/evidence/crypto-public-shadow-r2-20260914.json` | evidence | 14568 | 403 | `ed5fba6227a5` | 1 |
| `domains/capital/evidence/crypto-public-shadow-r2-20260921.json` | evidence | 1228 | 27 | `29dbdb497c52` | 1 |
| `domains/capital/evidence/crypto-shadow-mechanics-r1-20260913.json` | evidence | 2926 | 101 | `87bb901358fe` | 1 |
| `domains/capital/evidence/crypto-stream-resilience-r3-20260921.json` | evidence | 5047 | 124 | `f73b757dc275` | 1 |
| `domains/capital/evidence/crypto-vpn-public-data-qualification-20260913.json` | evidence | 1644 | 51 | `6ebcdfbc9437` | 1 |
| `domains/capital/evidence/data-products/crypto-public-shadow-consumption-r1/decision-outcome-feedback.json` | evidence | 1750 | 48 | `6cafaf913b63` | 1 |
| `domains/capital/evidence/data-products/crypto-public-shadow-consumption-r1/openlineage.json` | evidence | 1691 | 47 | `698a937a712c` |  |
| `domains/capital/evidence/data-products/crypto-public-shadow-consumption-r1/receipt.json` | evidence | 1202 | 21 | `d650e4065c19` | 1 |
| `domains/capital/evidence/finance-research/spy-shy-forward-20261108/README.md` | evidence | 4335 | 87 | `b9e194773e2e` |  |
| `domains/capital/evidence/finance-research/spy-shy-forward-20261108/current-assessment.json` | evidence | 227 | 10 | `4677e0c56619` | 1 |
| `domains/capital/evidence/finance-research/spy-shy-forward-20261108/frozen-plan.json` | evidence | 1825 | 42 | `f1248dfcfb26` | 1 |
| `domains/capital/evidence/finance-research/spy-shy-forward-20261108/research-plan.json` | evidence | 1494 | 35 | `07d83b6f6f34` | 1 |
| `domains/capital/evidence/finance-research/spy-shy-forward-20261108/retrospective-result.json` | evidence | 2402 | 54 | `102975f53748` | 1 |
| `domains/capital/evidence/full-nonlive-effect-closure-20260914.json` | evidence | 12426 | 151 | `47d0946496e3` | 1 |
| `domains/capital/evidence/okx-live-provider-binding-20260914.json` | evidence | 1756 | 56 | `c19256a40fba` | 1 |
| `domains/capital/evidence/wave-b-m5-status-20260913.json` | evidence | 2137 | 56 | `677066b2e8ca` | 1 |
| `domains/capital/examples/paper_fixed_mix_etf_20261106.json` | config | 847 | 28 | `ed6f41d79227` | 1 |
| `domains/capital/examples/passive_benchmark_first_run_r1.json` | config | 832 | 28 | `2242213dcc70` | 1 |
| `domains/capital/examples/portfolio_scenario_brief_r1.json` | config | 732 | 30 | `55e675af8520` | 1 |
| `domains/capital/examples/r1_witness_parquet_duckdb.py` | core | 2880 | 90 | `3459b9bc8cd7` |  |
| `domains/capital/examples/strategic_contribution_r1.json` | config | 351 | 16 | `acfa33e90e4e` | 1 |
| `domains/capital/fixtures/r5_legacy_bounded/manifest.json` | config | 1398 | 25 | `4214c7288a4c` | 1 |
| `domains/capital/fixtures/r5_legacy_bounded/market-capital-r26-p01-registry-parcel-authority-20260908.json` | config | 8074 | 163 | `0f6735618d1f` | 1 |
| `domains/capital/fixtures/r5_legacy_bounded/market-capital-r27-p21-effect-reconciliation-final-20260908.json` | config | 6252 | 146 | `16a761428335` | 1 |
| `domains/capital/fixtures/r5_legacy_bounded/market-capital-r28-p31-effect-authority-v2-final-20260908.json` | config | 3478 | 69 | `f7d27163890c` | 1 |
| `domains/capital/formal/AccountingReservationR1.smt2` | other | 2890 | — | `cbe87ac36482` |  |
| `domains/capital/formal/AlgebraicCapitalR1.smt2` | other | 2952 | — | `0690f1836756` |  |
| `domains/capital/formal/BrokerLiquidationCashflowR1.smt2` | other | 1936 | — | `f5ef852c84a3` |  |
| `domains/capital/formal/MarketsCapturePITR1.smt2` | other | 2175 | — | `367e5ab836a2` |  |
| `domains/capital/formal/MultistageOneRCashflowR1.smt2` | other | 3014 | — | `7ebe568c569c` |  |
| `domains/capital/formal/PaperCloseAmounts.lean` | core | 3441 | 76 | `62341c14a7ed` |  |
| `domains/capital/formal/PortfolioApportionmentGeneral.lean` | core | 3091 | 75 | `b1e7651aa081` |  |
| `domains/capital/formal/PortfolioContributionR1.smt2` | other | 2554 | — | `a9bd945d5e1a` |  |
| `domains/capital/formal/PortfolioPassiveBenchmarkGeneral.lean` | core | 5696 | 145 | `e5fbcdb269ed` |  |
| `domains/capital/formal/PortfolioPassiveBenchmarkR1.smt2` | other | 4508 | — | `0eace59bf8d5` |  |
| `domains/capital/formal/README.md` | docs | 20332 | 353 | `aee7003748f5` |  |
| `domains/capital/formal/RiskExposureBound.lean` | core | 1475 | 39 | `aa788fa1bd69` |  |
| `domains/capital/formal/RiskExposureBound.md` | docs | 4247 | 70 | `ef31e85d9d73` |  |
| `domains/capital/formal/UnitRMarginBoundR1.smt2` | other | 988 | — | `4b237a686ff6` |  |
| `domains/capital/formal/UnitRRebalanceConservationR1.smt2` | other | 2775 | — | `eb22ab5269af` |  |
| `domains/capital/formal/paper_cash_settlement_r1.smt2` | other | 3838 | — | `187788178b72` |  |
| `domains/capital/formal/paper_settlement_source_contract.py` | core | 2921 | 90 | `e60cdf7261fb` |  |
| `domains/capital/infra/optional-witness-substrate.compose.yaml` | config | 737 | 29 | `99888fa2e1a0` |  |
| `domains/capital/infra/systemd/ordivon-wsl-host-clock-sync.service` | config | 391 | 15 | `1be1c65546d7` |  |
| `domains/capital/mise.toml` | config | 9247 | 238 | `8d73d5670ee3` |  |
| `domains/capital/planning/lego-plan-r1.json` | config | 27041 | 557 | `b9710cc45625` | 1 |
| `domains/capital/pyproject.toml` | config | 898 | 40 | `28ff38813569` |  |
| `domains/capital/rust-toolchain.toml` | config | 51 | 3 | `ca67e66659a8` |  |
| `domains/capital/schema/legacy_protocol_v1/private-reality-snapshot-v1.schema.json` | schemas | 898 | 20 | `3d33712ecbef` |  |
| `domains/capital/schema/private-reality-snapshot-v2.schema.json` | schemas | 1194 | 61 | `45f56b7ef87e` |  |
| `domains/capital/schema/quantitative_component_inventory.schema.json` | schemas | 3312 | 83 | `656d1fa9eb61` |  |
| `domains/capital/scripts/capture-binance-usdm-private-r1` | other | 455 | — | `31a90cb980df` |  |
| `domains/capital/scripts/capture-binance-usdm-public-r1` | other | 593 | — | `e4c45e86f05e` |  |
| `domains/capital/scripts/capture-crypto-public-rest` | other | 3496 | — | `f18b0c0ac629` |  |
| `domains/capital/scripts/check-binance-usdm-equity-perp-preflight` | other | 1764 | — | `9e26da2e0e98` |  |
| `domains/capital/scripts/check-binance-usdm-private-readonly-preflight` | other | 2351 | — | `d51f9b304c99` |  |
| `domains/capital/scripts/check-capabilities` | other | 2319 | — | `30f1e690bb8a` |  |
| `domains/capital/scripts/check-clock-quality-gate` | other | 1754 | — | `60f54a66b56a` |  |
| `domains/capital/scripts/check-crypto-data-adapter-policy` | other | 2316 | — | `0871906942b0` |  |
| `domains/capital/scripts/check-demo-execution-preflight` | other | 1394 | — | `0f2f6c885266` |  |
| `domains/capital/scripts/check-execution-feasibility` | other | 1410 | — | `1cb026352083` |  |
| `domains/capital/scripts/check-execution-policy` | other | 338 | — | `97aa8eaf6afc` |  |
| `domains/capital/scripts/check-language-baseline` | other | 1490 | — | `187ec45ed626` |  |
| `domains/capital/scripts/check-live-test-account-policy` | other | 2004 | — | `9019c8e60630` |  |
| `domains/capital/scripts/check-network-v2-public-data` | other | 5629 | — | `9551800eba97` |  |
| `domains/capital/scripts/check-nonlive-credential-provisioning` | other | 1811 | — | `3aa24bf56eba` |  |
| `domains/capital/scripts/check-nonlive-effect-authority` | other | 2486 | — | `3cdf61f0fd6e` |  |
| `domains/capital/scripts/check-okx-live-provider-binding` | other | 168 | — | `ce809863f426` |  |
| `domains/capital/scripts/check-private-reality-credential-bindings` | other | 2618 | — | `c4eda0d5508d` |  |
| `domains/capital/scripts/check-private-reality-readonly-preflight` | other | 4290 | — | `09da921624dd` |  |
| `domains/capital/scripts/check-provider-registration-handoff` | other | 1269 | — | `6428d6a946de` |  |
| `domains/capital/scripts/check-quantitative-component-inventory` | other | 312 | — | `da21d3931c26` |  |
| `domains/capital/scripts/consume_crypto_public_shadow_product_r1.py` | core | 6837 | 151 | `3ee0d6ae97d9` |  |
| `domains/capital/scripts/finance_lego.py` | core | 2945 | 82 | `81c3abc77585` |  |
| `domains/capital/scripts/install-nonlive-credential` | other | 2364 | — | `a17791eae931` |  |
| `domains/capital/scripts/persist-model-monitoring-r1` | other | 182 | — | `50f51f64517d` |  |
| `domains/capital/scripts/portfolio_scenario_brief.py` | core | 4920 | 135 | `d6c919ad99a7` |  |
| `domains/capital/scripts/reconcile-underlying-reopen-r1` | other | 1635 | — | `64b563ed2942` |  |
| `domains/capital/scripts/run-canonical-tests` | other | 155 | — | `b5cba0903249` |  |
| `domains/capital/scripts/run-capability-python` | other | 694 | — | `927fb5bbf136` |  |
| `domains/capital/scripts/run-capability-rust` | other | 417 | — | `d6970652bd89` |  |
| `domains/capital/scripts/run-capital-trading-fullpath-closure` | other | 6750 | — | `c0709d5058f0` |  |
| `domains/capital/scripts/run-crypto-fix-projection-r4` | other | 4944 | — | `0b21cd7f6ae7` |  |
| `domains/capital/scripts/run-crypto-public-shadow-r1` | other | 809 | — | `c27b791c8e4d` |  |
| `domains/capital/scripts/run-crypto-public-shadow-r2` | other | 1452 | — | `94bb329da760` |  |
| `domains/capital/scripts/run-crypto-public-streaming-r2-candidate` | other | 1835 | — | `0f52bc3f8635` |  |
| `domains/capital/scripts/run-crypto-stream-resilience-r3` | other | 1576 | — | `9ab75ed51216` |  |
| `domains/capital/scripts/run-crypto-stream-resilience-r3-candidate` | other | 1618 | — | `56a0036e4ef2` |  |
| `domains/capital/scripts/run-crypto-stream-resilience-r3-session` | other | 3549 | — | `284de9de2c22` |  |
| `domains/capital/scripts/run-finance-lego` | other | 244 | — | `287aca760dcf` |  |
| `domains/capital/scripts/run-nonlive-capital-effect-matrix` | other | 8189 | — | `0d7a9b182708` |  |
| `domains/capital/scripts/run-okx-demo-execution` | other | 173 | — | `5ccc6ca768d4` |  |
| `domains/capital/scripts/run-okx-factor-observatory-r1` | other | 552 | — | `7f88f01bdb67` |  |
| `domains/capital/scripts/run-okx-instrument-sensors-r1` | other | 931 | — | `99815b77c73c` |  |
| `domains/capital/scripts/run-paper-etf-replay-r1` | other | 248 | — | `a2d3081e5a30` |  |
| `domains/capital/scripts/run-paper-etf-vintage-compare-r1` | other | 243 | — | `65044e095d3e` |  |
| `domains/capital/scripts/run-parquet-duckdb-owner-requalification-r17` | other | 173 | — | `748cdefe1171` |  |
| `domains/capital/scripts/run-portfolio-scenario-brief` | other | 244 | — | `882b25acb42e` |  |
| `domains/capital/scripts/run-strategic-contribution-brief` | other | 256 | — | `7c03a86a90a5` |  |
| `domains/capital/scripts/run-websockets-owner-requalification-r17` | other | 169 | — | `0b2ce7c02b3d` |  |
| `domains/capital/scripts/strategic_contribution_brief.py` | core | 1263 | 46 | `5c2b862247dc` |  |
| `domains/capital/src/ordivon_capital/__init__.py` | core | 91 | 1 | `05ca4590b556` |  |
| `domains/capital/src/ordivon_capital/accounting/__init__.py` | core | 69 | 1 | `890b5c7d0384` |  |
| `domains/capital/src/ordivon_capital/accounting/durable.py` | core | 6653 | 207 | `6193776afb81` |  |
| `domains/capital/src/ordivon_capital/accounting/paper_close.py` | core | 8961 | 218 | `b3aa4f0471d8` |  |
| `domains/capital/src/ordivon_capital/accounting/postgres_ledger.py` | core | 18701 | 424 | `d38807738465` |  |
| `domains/capital/src/ordivon_capital/accounting/postgres_paper_close.py` | core | 20754 | 430 | `f1a74b79bcf5` |  |
| `domains/capital/src/ordivon_capital/accounting/substrate.py` | core | 7277 | 209 | `b1980544bd36` |  |
| `domains/capital/src/ordivon_capital/governance/__init__.py` | core | 41 | 1 | `e81f4dc022d7` |  |
| `domains/capital/src/ordivon_capital/governance/policy_decision.py` | core | 22818 | 606 | `991d41de48ee` |  |
| `domains/capital/src/ordivon_capital/markets/__init__.py` | core | 38 | 1 | `c9e62f130a8f` |  |
| `domains/capital/src/ordivon_capital/markets/binance_usdm_public_capture.py` | core | 5637 | 156 | `cf0fb5fbd4ad` |  |
| `domains/capital/src/ordivon_capital/markets/binance_usdm_reference.py` | core | 3329 | 75 | `a0d29d0e3bef` |  |
| `domains/capital/src/ordivon_capital/markets/crypto_public_shadow.py` | core | 10327 | 228 | `63f7a3da543d` |  |
| `domains/capital/src/ordivon_capital/markets/crypto_public_streaming.py` | core | 12926 | 317 | `7c06b731d3c6` |  |
| `domains/capital/src/ordivon_capital/markets/crypto_stream_health.py` | core | 2236 | 66 | `6bfbfe0e02fc` |  |
| `domains/capital/src/ordivon_capital/markets/crypto_stream_resilience.py` | core | 14031 | 319 | `311bbc4bcd74` |  |
| `domains/capital/src/ordivon_capital/markets/etf_eod_snapshot.py` | core | 9849 | 229 | `75c941d3162d` |  |
| `domains/capital/src/ordivon_capital/markets/historical_close_snapshot.py` | core | 4651 | 125 | `38e7da573f1f` |  |
| `domains/capital/src/ordivon_capital/markets/market_sensors.py` | core | 14425 | 329 | `21bfff86e1c7` |  |
| `domains/capital/src/ordivon_capital/markets/okx_sensor_capture.py` | core | 14799 | 392 | `b1e0f6543787` |  |
| `domains/capital/src/ordivon_capital/markets/websocket_proxy_lifecycle.py` | core | 2239 | 55 | `2c04957355e4` |  |
| `domains/capital/src/ordivon_capital/portfolio/__init__.py` | core | 40 | 1 | `1568adf6ee61` |  |
| `domains/capital/src/ordivon_capital/portfolio/algebraic_policy.py` | core | 13105 | 327 | `9a9cfacb4a56` |  |
| `domains/capital/src/ordivon_capital/portfolio/information_tree.py` | core | 9551 | 215 | `6097949f5165` |  |
| `domains/capital/src/ordivon_capital/portfolio/multistage_policy.py` | core | 19168 | 489 | `95917ded0550` |  |
| `domains/capital/src/ordivon_capital/portfolio/paper_close_performance.py` | core | 9588 | 232 | `3d0f7a90e91f` |  |
| `domains/capital/src/ordivon_capital/portfolio/paper_investment.py` | core | 15218 | 364 | `e653d3b02fe7` |  |
| `domains/capital/src/ordivon_capital/portfolio/paper_vintage.py` | core | 6675 | 167 | `93adf05110bd` |  |
| `domains/capital/src/ordivon_capital/portfolio/passive_benchmark.py` | core | 10405 | 244 | `f77d2d6ecd2c` |  |
| `domains/capital/src/ordivon_capital/portfolio/portfolio_counterfactuals.py` | core | 20364 | 481 | `23fe84c7e803` |  |
| `domains/capital/src/ordivon_capital/portfolio/strategic_contribution.py` | core | 5969 | 136 | `bf3bdfb0a52d` |  |
| `domains/capital/src/ordivon_capital/research/__init__.py` | research | 39 | 1 | `608079443aca` |  |
| `domains/capital/src/ordivon_capital/research/experiment_protocol.py` | research | 19579 | 426 | `d6531567388b` |  |
| `domains/capital/src/ordivon_capital/research/independent_policy_replay.py` | research | 14115 | 287 | `8dfd1ba10cf6` |  |
| `domains/capital/src/ordivon_capital/research/investment_candidate.py` | research | 12567 | 282 | `adf688f08e93` |  |
| `domains/capital/src/ordivon_capital/research/model_monitoring.py` | research | 10574 | 254 | `3f8dc442ed2b` |  |
| `domains/capital/src/ordivon_capital/research/monitoring_persistence.py` | research | 10490 | 286 | `c7ab0511d559` |  |
| `domains/capital/src/ordivon_capital/research/monitoring_persistence_cli.py` | research | 787 | 30 | `1752d5592c0c` |  |
| `domains/capital/src/ordivon_capital/research/okx_factor_observer.py` | research | 11569 | 302 | `b10f198089bb` |  |
| `domains/capital/src/ordivon_capital/research/pit_joint_forecast.py` | research | 37824 | 860 | `77192e42e628` |  |
| `domains/capital/src/ordivon_capital/research/prospective_validation.py` | research | 3121 | 76 | `25fb7512f991` |  |
| `domains/capital/src/ordivon_capital/research/quantitative_inventory_validation.py` | research | 7328 | 203 | `780b77467da8` |  |
| `domains/capital/src/ordivon_capital/research/standards_inventory.py` | research | 2754 | 78 | `7b6a9116fcfb` |  |
| `domains/capital/src/ordivon_capital/research/unit_r_dca.py` | research | 22330 | 555 | `77bd154ea7d7` |  |
| `domains/capital/src/ordivon_capital/risk/__init__.py` | core | 35 | 1 | `cde6a055e337` |  |
| `domains/capital/src/ordivon_capital/risk/broker_margin.py` | core | 10971 | 235 | `17e4394a5175` |  |
| `domains/capital/src/ordivon_capital/risk/dependence_analysis.py` | core | 13698 | 333 | `8ff82bfd3d34` |  |
| `domains/capital/src/ordivon_capital/risk/paper_close_risk.py` | core | 10921 | 254 | `959795dbbed7` |  |
| `domains/capital/src/ordivon_capital/risk/portfolio_risk.py` | core | 12189 | 326 | `e778574f29a2` |  |
| `domains/capital/src/ordivon_capital/risk/risk_budget_validation.py` | core | 2792 | 74 | `9877db46b474` |  |
| `domains/capital/src/ordivon_capital/risk/risk_values.py` | core | 2235 | 64 | `f6e094dc2c54` |  |
| `domains/capital/src/ordivon_capital/risk/tail_report.py` | core | 1727 | 48 | `089f472b43c6` |  |
| `domains/capital/src/ordivon_capital/risk/tail_risk.py` | core | 2935 | 77 | `ec934a18b444` |  |
| `domains/capital/src/ordivon_capital/trading/__init__.py` | core | 38 | 1 | `6dcc96df24af` |  |
| `domains/capital/src/ordivon_capital/trading/binance_usdm_private_capture.py` | core | 10654 | 284 | `b13ce2d9848e` |  |
| `domains/capital/src/ordivon_capital/trading/binance_usdm_provider.py` | core | 1395 | 35 | `ae10ef560dfd` |  |
| `domains/capital/src/ordivon_capital/trading/execution_feasibility.py` | core | 5105 | 131 | `dd936498943d` |  |
| `domains/capital/src/ordivon_capital/trading/execution_reconciliation.py` | core | 7164 | 168 | `defc14bcc392` |  |
| `domains/capital/src/ordivon_capital/trading/fix44_projection.py` | core | 7639 | 204 | `64a4a7ce45b4` |  |
| `domains/capital/src/ordivon_capital/trading/okx_demo_execution.py` | core | 18712 | 425 | `28dbaacd435c` |  |
| `domains/capital/src/ordivon_capital/trading/okx_official_cli.py` | core | 8984 | 189 | `e63e71cee1f6` |  |
| `domains/capital/src/ordivon_capital/trading/okx_readonly_client.py` | core | 7351 | 198 | `6a7cb6d6bcec` |  |
| `domains/capital/src/ordivon_capital/trading/paper_fill_calendar.py` | core | 5086 | 107 | `adb56f7d1d6d` |  |
| `domains/capital/src/ordivon_capital/trading/postgres_demo_intent.py` | core | 10055 | 211 | `0aa9139bc7ca` |  |
| `domains/capital/src/ordivon_capital/trading/private_reality.py` | core | 19150 | 403 | `e6f91f02a755` |  |
| `domains/capital/tests/test_accounting_durable.py` | tests | 6164 | 185 | `5c2970e62bd2` |  |
| `domains/capital/tests/test_accounting_smoke_optimizer_contract.py` | tests | 2577 | 58 | `34f584d9bbb9` |  |
| `domains/capital/tests/test_accounting_substrate.py` | tests | 3894 | 118 | `d5fe01d6a4c7` |  |
| `domains/capital/tests/test_accounting_substrate_type_authority.py` | tests | 1806 | 51 | `ab2876737495` |  |
| `domains/capital/tests/test_algebraic_policy.py` | tests | 5547 | 139 | `4d3a389f44ba` |  |
| `domains/capital/tests/test_binance_usdm_private_capture.py` | tests | 4127 | 105 | `297f28ed0e47` |  |
| `domains/capital/tests/test_binance_usdm_provider.py` | tests | 8602 | 225 | `e5e3b65a35f6` |  |
| `domains/capital/tests/test_broker_margin_evidence.py` | tests | 8031 | 215 | `b2c5973e852e` |  |
| `domains/capital/tests/test_candidate_tool_surface_isolation.py` | tests | 2894 | 66 | `82631e9b6e59` |  |
| `domains/capital/tests/test_capability_current_postgres.py` | tests | 859 | 21 | `757b05abcbec` |  |
| `domains/capital/tests/test_capital_domain_taxonomy.py` | tests | 4866 | 126 | `bada95ee3036` |  |
| `domains/capital/tests/test_clock_quality_gate.py` | tests | 1840 | 34 | `f881a48f696d` |  |
| `domains/capital/tests/test_crypto_data_adapters.py` | tests | 4924 | 97 | `4aa4cc369b46` |  |
| `domains/capital/tests/test_crypto_execution_lane.py` | tests | 2017 | 44 | `e1f2b5467e26` |  |
| `domains/capital/tests/test_crypto_fix44_projection.py` | tests | 3286 | 79 | `84e0a3d5b7b2` |  |
| `domains/capital/tests/test_crypto_public_shadow.py` | tests | 7925 | 151 | `6142b9aeae61` |  |
| `domains/capital/tests/test_crypto_public_streaming.py` | tests | 3872 | 78 | `05cb0a6304df` |  |
| `domains/capital/tests/test_crypto_shadow_mechanics.py` | tests | 1234 | 32 | `a7e5e66b53c3` |  |
| `domains/capital/tests/test_crypto_stream_health.py` | tests | 2055 | 54 | `f509c1de304f` |  |
| `domains/capital/tests/test_crypto_stream_resilience_policy.py` | tests | 1494 | 37 | `4d4bcc08e6d1` |  |
| `domains/capital/tests/test_crypto_stream_resilience_runner.py` | tests | 1666 | 29 | `e88b98d99af8` |  |
| `domains/capital/tests/test_crypto_streaming_runner_policy.py` | tests | 2090 | 38 | `b70b2125abdf` |  |
| `domains/capital/tests/test_current_runtime_admission.py` | tests | 1993 | 38 | `cff4e4e53aab` |  |
| `domains/capital/tests/test_current_source_pointer_integrity.py` | tests | 1283 | 40 | `db35bffd6596` |  |
| `domains/capital/tests/test_data_product_consumption_crypto_public_shadow.py` | tests | 4737 | 96 | `a61167a1ab71` |  |
| `domains/capital/tests/test_data_product_crypto_public_shadow.py` | tests | 3529 | 71 | `6e3cf5a83bc7` |  |
| `domains/capital/tests/test_demo_execution_preflight.py` | tests | 1389 | 31 | `bee4375dd2dd` |  |
| `domains/capital/tests/test_duckdb_provenance_identity.py` | tests | 1583 | 34 | `94e5450fb3cf` |  |
| `domains/capital/tests/test_etf_eod_snapshot.py` | tests | 5576 | 144 | `e5421570098c` |  |
| `domains/capital/tests/test_execution_feasibility.py` | tests | 4399 | 131 | `600fc5ae70d4` |  |
| `domains/capital/tests/test_execution_policy.py` | tests | 2264 | 55 | `c6391e035d99` |  |
| `domains/capital/tests/test_execution_reconciliation.py` | tests | 2696 | 41 | `038a32e660fb` |  |
| `domains/capital/tests/test_experiment_protocol.py` | tests | 6196 | 173 | `faf828cd45c9` |  |
| `domains/capital/tests/test_external_owner_census.py` | tests | 23945 | 457 | `6b168bd246c9` |  |
| `domains/capital/tests/test_factor_lego_consumer_contract.py` | tests | 9126 | 249 | `d0dd865c8fd3` |  |
| `domains/capital/tests/test_finance_agent_role_composition.py` | tests | 8537 | 212 | `50da2c29ce03` |  |
| `domains/capital/tests/test_finance_lego_cli.py` | tests | 3152 | 89 | `21b6e42e26b3` |  |
| `domains/capital/tests/test_finance_real_etf_research_case.py` | tests | 8252 | 180 | `adc612c24dbe` |  |
| `domains/capital/tests/test_finance_research_composition.py` | tests | 10873 | 269 | `c07b504fd9e7` |  |
| `domains/capital/tests/test_fix44_projection.py` | tests | 3825 | 114 | `46545f53b6c3` |  |
| `domains/capital/tests/test_independent_policy_replay.py` | tests | 8884 | 269 | `a6170ad9e733` |  |
| `domains/capital/tests/test_intermediate_obligations.py` | tests | 4832 | 128 | `c5b40252d2b2` |  |
| `domains/capital/tests/test_investment_candidate.py` | tests | 4940 | 144 | `d847226aa9ec` |  |
| `domains/capital/tests/test_investment_candidate_source_replay.py` | tests | 5675 | 164 | `4914362ac489` |  |
| `domains/capital/tests/test_jsonschema_owner_requalification.py` | tests | 5424 | 139 | `5e37816b793e` |  |
| `domains/capital/tests/test_legacy_replay_surface_isolation.py` | tests | 3081 | 81 | `46bccd791166` |  |
| `domains/capital/tests/test_live_test_account_policy.py` | tests | 2729 | 49 | `a9e038f34ce0` |  |
| `domains/capital/tests/test_live_test_admission.py` | tests | 3293 | 57 | `a7ec3671d020` |  |
| `domains/capital/tests/test_live_test_canary_policy.py` | tests | 942 | 19 | `5870fcbee1fd` |  |
| `domains/capital/tests/test_market_sensors.py` | tests | 8291 | 164 | `d166288c3c70` |  |
| `domains/capital/tests/test_model_monitoring.py` | tests | 2763 | 79 | `5a31df7bb69d` |  |
| `domains/capital/tests/test_monitoring_persistence.py` | tests | 4693 | 132 | `f53363ac48fc` |  |
| `domains/capital/tests/test_multistage_policy.py` | tests | 11559 | 325 | `eb2c8132d850` |  |
| `domains/capital/tests/test_nautilus_candidate.py` | tests | 1140 | 31 | `bea8922f5b3e` |  |
| `domains/capital/tests/test_network_v2_public_data_binding.py` | tests | 1431 | 36 | `cc3849b5b7a3` |  |
| `domains/capital/tests/test_nonlive_credential_installer.py` | tests | 464 | 12 | `348601b4b557` |  |
| `domains/capital/tests/test_nonlive_credential_provisioning.py` | tests | 1054 | 24 | `5042bd364e37` |  |
| `domains/capital/tests/test_nonlive_effect_authority.py` | tests | 1506 | 37 | `1cd9c5d4abe4` |  |
| `domains/capital/tests/test_nonlive_effect_qualification.py` | tests | 2231 | 58 | `ebe2b6530b31` |  |
| `domains/capital/tests/test_nonlive_policy_optimized_contract.py` | tests | 10548 | 243 | `ea59b30d51c6` |  |
| `domains/capital/tests/test_observability_legacy_retirement.py` | tests | 1699 | 45 | `238f1844527d` |  |
| `domains/capital/tests/test_okx_demo_execution.py` | tests | 7604 | 179 | `a73e6efdedcc` |  |
| `domains/capital/tests/test_okx_factor_observer.py` | tests | 7025 | 161 | `05660a7565c7` |  |
| `domains/capital/tests/test_okx_live_provider_binding.py` | tests | 3005 | 70 | `2c884da72c48` |  |
| `domains/capital/tests/test_okx_official_cli.py` | tests | 6865 | 158 | `7a12093ddae3` |  |
| `domains/capital/tests/test_okx_readonly_client.py` | tests | 5516 | 192 | `676fdf6adf53` |  |
| `domains/capital/tests/test_okx_sensor_capture.py` | tests | 4997 | 129 | `09a0ae6d7a7e` |  |
| `domains/capital/tests/test_paper_close.py` | tests | 16813 | 383 | `dd7d68a45b7d` |  |
| `domains/capital/tests/test_paper_close_performance.py` | tests | 13769 | 331 | `04a660291a6d` |  |
| `domains/capital/tests/test_paper_close_risk.py` | tests | 15228 | 358 | `1782b559c9bb` |  |
| `domains/capital/tests/test_paper_fill_calendar.py` | tests | 4649 | 107 | `1768547c5e25` |  |
| `domains/capital/tests/test_paper_head_readback.py` | tests | 3298 | 76 | `ea1980db7fa8` |  |
| `domains/capital/tests/test_paper_investment.py` | tests | 8794 | 249 | `b0523fd9b7e4` |  |
| `domains/capital/tests/test_paper_vintage_comparison.py` | tests | 6165 | 171 | `53b27f0c678c` |  |
| `domains/capital/tests/test_parquet_duckdb_owner_requalification.py` | tests | 2580 | 60 | `5432d718288b` |  |
| `domains/capital/tests/test_passive_benchmark.py` | tests | 13721 | 335 | `d5025589de7e` |  |
| `domains/capital/tests/test_pit_etf_eod_composition.py` | tests | 9057 | 214 | `c658fc6dfec6` |  |
| `domains/capital/tests/test_pit_joint_forecast.py` | tests | 36524 | 866 | `e850f12e914c` |  |
| `domains/capital/tests/test_portfolio_counterfactuals.py` | tests | 21121 | 490 | `05f795eb0d04` |  |
| `domains/capital/tests/test_portfolio_risk.py` | tests | 14998 | 341 | `f019367fb40e` |  |
| `domains/capital/tests/test_portfolio_scenario_brief_consumer.py` | tests | 5062 | 134 | `c2873c9cc6c4` |  |
| `domains/capital/tests/test_postgres_accounting_traces.py` | tests | 6031 | 147 | `dbc8a82a79a2` |  |
| `domains/capital/tests/test_postgres_demo_intent.py` | tests | 5214 | 140 | `7d41d90fad26` |  |
| `domains/capital/tests/test_postgres_ledger.py` | tests | 9782 | 240 | `5a6d8964803e` |  |
| `domains/capital/tests/test_private_reality_bindings.py` | tests | 1280 | 25 | `f4aa763f3fb9` |  |
| `domains/capital/tests/test_private_reality_normalization.py` | tests | 6648 | 115 | `526b15daf48c` |  |
| `domains/capital/tests/test_private_reality_policy.py` | tests | 2354 | 41 | `e855128dcf30` |  |
| `domains/capital/tests/test_prospective_validation.py` | tests | 3820 | 107 | `5eb41a047177` |  |
| `domains/capital/tests/test_protocol_identity_v2.py` | tests | 4136 | 112 | `b3f9ba2debbd` |  |
| `domains/capital/tests/test_r21_capital_source_responsibilities.py` | tests | 3984 | 103 | `2a936a01a780` |  |
| `domains/capital/tests/test_r5_legacy_differential.py` | tests | 1783 | 46 | `3666c40c048b` |  |
| `domains/capital/tests/test_standalone_source_retirement.py` | tests | 2627 | 56 | `6660c20c4c57` |  |
| `domains/capital/tests/test_standards_inventory.py` | tests | 3395 | 87 | `5d410565141a` |  |
| `domains/capital/tests/test_strategic_contribution.py` | tests | 5906 | 163 | `97e5ec859118` |  |
| `domains/capital/tests/test_terminal_liabilities.py` | tests | 5879 | 135 | `b159378e1f98` |  |
| `domains/capital/tests/test_unit_r_dca.py` | tests | 7673 | 194 | `c56482186996` |  |
| `domains/capital/tests/test_verification_boundary.py` | tests | 505 | 13 | `c1cb83ad4370` |  |
| `domains/capital/tests/test_wave_b_contract.py` | tests | 4477 | 76 | `07e6d33afee3` |  |
| `domains/capital/tests/test_websocket_proxy_lifecycle.py` | tests | 3914 | 104 | `2ae92078688b` |  |
| `domains/capital/tests/test_websockets_owner_requalification.py` | tests | 1502 | 36 | `9cb8f9368cd8` |  |
| `domains/capital/tools/jsonschema_4_26_0/check-candidate` | other | 594 | — | `d8ec86f9f974` |  |
| `domains/capital/tools/jsonschema_4_26_0/differential_r18.py` | core | 17626 | 496 | `edaef6f535f9` |  |
| `domains/capital/tools/jsonschema_4_26_0/qualification-r18.json` | config | 2216 | 71 | `c4452ad088e2` | 1 |
| `domains/capital/tools/jsonschema_4_26_0/run-differential-r18` | other | 261 | — | `e46e4cab947e` |  |
| `domains/capital/tools/legacy_replay/README.md` | docs | 613 | 7 | `9acf4309e7fd` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/algorithm/MarketCapitalValidationAlgorithm.cs` | core | 11997 | 192 | `fc9b2f7772ee` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/algorithm/MarketCapitalValidationAlgorithm.csproj` | other | 1025 | — | `c869208d9de3` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/algorithm/packages.lock.json` | config | 1283 | 37 | `418aded46795` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/check-lean-runtime` | other | 933 | — | `0a58849898c2` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/fetch-nasdaq-wave-b-m3` | other | 4659 | — | `7bf39cc174ec` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/prepare-lean-validation-data` | other | 1909 | — | `be818cfa1353` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/probe-prospective-validation-wave-b-m5` | other | 3987 | — | `f3d24279b7c9` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/run-lean-wave-b-m1` | other | 3341 | — | `1471a05c041a` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/run-lean-wave-b-m2` | other | 3639 | — | `4c4b9db99b38` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/run-lean-wave-b-m3` | other | 3816 | — | `b2ece04de07d` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/run-lean-wave-b-m4` | other | 4427 | — | `fdb84f0709e0` |  |
| `domains/capital/tools/legacy_replay/lean_wave_b/run-shadow-precommit-wave-b-m6` | other | 5315 | — | `37c9aa18d253` |  |
| `domains/capital/tools/nautilus_rc4/check-candidate` | other | 1608 | — | `309de5899675` |  |
| `domains/capital/tools/nautilus_rc4/check-crypto-execution-lane` | other | 422 | — | `d2654726ecf2` |  |
| `domains/capital/tools/nautilus_rc4/check-demo-execution-configs` | other | 1378 | — | `87e9fc71131f` |  |
| `domains/capital/tools/nautilus_rc4/check-okx-read-surface` | other | 772 | — | `3852f74c86f9` |  |
| `domains/capital/tools/nautilus_rc4/config/crypto_execution_lane.json` | config | 2673 | 74 | `7766a931da1a` | 2 |
| `domains/capital/tools/nautilus_rc4/config/crypto_shadow_mechanics.json` | config | 455 | 14 | `c69297382060` | 2 |
| `domains/capital/tools/nautilus_rc4/config/nautilus_candidate.json` | config | 766 | 16 | `db2bbdc135b3` | 2 |
| `domains/capital/tools/nautilus_rc4/crypto_lane.py` | core | 4611 | 130 | `2457be514186` |  |
| `domains/capital/tools/nautilus_rc4/crypto_shadow_mechanics.py` | core | 11239 | 262 | `8fd9311509f9` |  |
| `domains/capital/tools/nautilus_rc4/nautilus_qualification.py` | core | 10739 | 291 | `bd7e4d1aeac6` |  |
| `domains/capital/tools/nautilus_rc4/nonlive_effect_matrix.py` | core | 7442 | 177 | `72ac436640e2` |  |
| `domains/capital/tools/nautilus_rc4/nonlive_effect_qualification.py` | core | 5820 | 159 | `37922761d32d` |  |
| `domains/capital/tools/nautilus_rc4/okx_live_config_probe.py` | core | 2271 | 63 | `4b23b106b815` |  |
| `domains/capital/tools/nautilus_rc4/run-crypto-shadow-mechanics-r1` | other | 689 | — | `4edfa4cd9097` |  |
| `domains/capital/tools/nautilus_rc4/run-m6-differential` | other | 666 | — | `11b87b078e6a` |  |
| `domains/capital/tools/nautilus_rc4/run-nonlive-effect-matrix` | other | 675 | — | `1f5e631c05e0` |  |
| `domains/capital/tools/okx_live_provider_probe.py` | core | 6952 | 157 | `f9fb470a8910` |  |
| `domains/capital/tools/okx_official_cli/.gitignore` | other | 14 | — | `4d56952b0fb1` |  |
| `domains/capital/tools/okx_official_cli/package.json` | config | 263 | 9 | `1f3f9e5fc490` |  |
| `domains/capital/tools/okx_official_cli/pnpm-lock.yaml` | config | 1101 | 46 | `1e6ff6c6818f` |  |
| `domains/capital/tools/opa_1_20_2/README.md` | docs | 674 | 12 | `fd197c68a194` |  |
| `domains/capital/tools/opa_1_20_2/market_controls.rego` | core | 8566 | 229 | `0169aee787a8` |  |
| `domains/capital/tools/qualification/parquet_duckdb_owner_r17.py` | core | 13398 | 347 | `263bd7cc85f1` |  |
| `domains/capital/tools/qualification/websockets_owner_r17.py` | core | 9822 | 298 | `b23842a34a92` |  |
| `domains/capital/tools/quickfixn_1_14_1/README.md` | docs | 789 | 15 | `d0eab3017447` |  |
| `domains/capital/tools/quickfixn_1_14_1/fix44-projector/MarketCapital.Fix44Projector.csproj` | other | 403 | — | `3e9e2dd7638a` |  |
| `domains/capital/tools/quickfixn_1_14_1/fix44-projector/Program.cs` | core | 4885 | 98 | `7e3261fa7cd5` |  |
| `domains/capital/tools/quickfixn_1_14_1/fix44-projector/packages.lock.json` | config | 1283 | 37 | `418aded46795` |  |
| `domains/capital/tools/tigerbeetle_0_17_9/ordivon_capital/__init__.py` | core | 52 | 1 | `fad8913f843a` |  |
| `domains/capital/tools/tigerbeetle_0_17_9/ordivon_capital/accounting/__init__.py` | core | 63 | 1 | `da745266e3f1` |  |
| `domains/capital/tools/tigerbeetle_0_17_9/ordivon_capital/accounting/tigerbeetle_durable.py` | core | 7596 | 217 | `3bacdaf1b14d` |  |
| `domains/capital/tools/tigerbeetle_0_17_9/ordivon_capital/accounting/tigerbeetle_substrate.py` | core | 10692 | 327 | `08846efc63c0` |  |
| `domains/capital/tools/tigerbeetle_0_17_9/replay/run-tigerbeetle-capital-substrate-smoke-r1` | other | 3478 | — | `ac900435ebeb` |  |
| `domains/capital/tools/tigerbeetle_0_17_9/replay/run-tigerbeetle-durable-restart-smoke-r32` | other | 8189 | — | `2788d95c295d` |  |
| `domains/capital/tools/tigerbeetle_0_17_9/replay/run-tigerbeetle-reservation-resolution-smoke-r31` | other | 6320 | — | `6c0856a7ffaa` |  |
| `domains/capital/tools/tigerbeetle_0_17_9/tigerbeetle_capital_substrate.json` | config | 2740 | 65 | `2856a01b676d` | 2 |
| `domains/capital/uv.lock` | config | 56751 | — | `30380ab93c0a` |  |
| `domains/capital/wave_b/fixtures/wave_a_target_portfolio.json` | config | 974 | 21 | `137265667683` |  |

### data — packages/data/（19 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `packages/data/AGENTS.md` | docs | 1505 | 21 | `128cb9a106a4` |  |
| `packages/data/README.md` | docs | 10260 | 174 | `bc85d967e3d0` |  |
| `packages/data/docs/AGENT.md` | docs | 6875 | 115 | `bb4b2c85669e` |  |
| `packages/data/docs/FORMAL_VERIFICATION.md` | docs | 13370 | 203 | `fa7d9eb95908` |  |
| `packages/data/docs/HUMAN.md` | docs | 7187 | 128 | `e15b6cd23531` |  |
| `packages/data/docs/LEGO_CENSUS.md` | docs | 5726 | 88 | `90b7ad899cdb` |  |
| `packages/data/formal/DataMultiVersion.lean` | core | 7451 | 179 | `43f23f55b7ba` |  |
| `packages/data/formal/DataProduct.lean` | core | 3560 | 95 | `73828e673633` |  |
| `packages/data/formal/DataPublication.lean` | core | 3958 | 98 | `b32246343fed` |  |
| `packages/data/mise.toml` | config | 1117 | 20 | `7fdc4f18139d` |  |
| `packages/data/scripts/inspect_federation.py` | core | 4731 | 134 | `c1c2c56afe91` |  |
| `packages/data/scripts/project_owned_products.py` | core | 2657 | 89 | `e988d5219f46` |  |
| `packages/data/src/ordivon_data/__init__.py` | core | 139 | 4 | `03d56a0be527` |  |
| `packages/data/src/ordivon_data/catalog.py` | core | 6913 | 177 | `580329137634` |  |
| `packages/data/src/ordivon_data/local_evidence.py` | core | 4524 | 111 | `971f4d42e19e` |  |
| `packages/data/src/ordivon_data/odps_projection.py` | core | 7333 | 181 | `b88acf393720` |  |
| `packages/data/src/ordivon_data/verification.py` | core | 932 | 20 | `00acbbcbd948` |  |
| `packages/data/tests/test_catalog.py` | tests | 7584 | 179 | `c48539319182` |  |
| `packages/data/tests/test_odps_projection.py` | tests | 17723 | 418 | `7cafed668bda` |  |

### web — apps/web/（35 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `apps/web/.gitignore` | other | 27 | — | `2931a03de250` |  |
| `apps/web/README.md` | docs | 5293 | 184 | `5d93bbec1675` |  |
| `apps/web/agent-native-e2e.sh` | core | 3312 | 85 | `8c3b42023e84` |  |
| `apps/web/browser-e2e.sh` | core | 491 | 21 | `c0fe871d431b` |  |
| `apps/web/evidence/AGENT-AUTHORITY-BROWSER-E2E-R1.json` | evidence | 2948 | 86 | `20ebe7644bd0` | 1 |
| `apps/web/evidence/AGENT-NATIVE-WEBSITE-E2E-R1.json` | evidence | 4037 | 115 | `bfaf260aaef8` | 1 |
| `apps/web/evidence/HUMAN-RAIL-BROWSER-E2E-R1.json` | evidence | 1335 | 40 | `a5dc472290b2` | 1 |
| `apps/web/mise.toml` | config | 166 | 12 | `89c5588c73e3` |  |
| `apps/web/package.json` | config | 966 | 34 | `45f989aa5030` |  |
| `apps/web/planning/lego-plan-r1.json` | config | 15845 | 383 | `25aca4d78a15` | 1 |
| `apps/web/pnpm-lock.yaml` | config | 35704 | 1115 | `e20ec41fe970` |  |
| `apps/web/pnpm-workspace.yaml` | config | 16 | 2 | `44b627aa5890` |  |
| `apps/web/src/agent-authority.ts` | core | 3325 | 120 | `ab14563c34ca` |  |
| `apps/web/src/app.ts` | core | 21038 | 721 | `ec49b263eefc` |  |
| `apps/web/src/browser-request-boundary.ts` | core | 2951 | 108 | `18216c0bf790` |  |
| `apps/web/src/config.ts` | core | 1869 | 56 | `dc9db2f35759` |  |
| `apps/web/src/errors.ts` | core | 323 | 13 | `724b38881fb6` |  |
| `apps/web/src/identity-digests.ts` | core | 1032 | 31 | `8712568bd769` |  |
| `apps/web/src/model.ts` | core | 4544 | 169 | `0393b429bf84` |  |
| `apps/web/src/security-agent-verifier.ts` | core | 2081 | 68 | `424ce860e538` |  |
| `apps/web/src/server.ts` | core | 640 | 20 | `e0a802ade317` |  |
| `apps/web/src/store-agent-grants.ts` | core | 4661 | 152 | `bcf106c5623c` |  |
| `apps/web/src/store-row-projections.ts` | core | 4739 | 187 | `bf167852bf66` |  |
| `apps/web/src/store-schema.ts` | schemas | 5458 | 153 | `d4e4e9573a1d` |  |
| `apps/web/src/store-sessions.ts` | core | 4879 | 174 | `5bc0d3795a3c` |  |
| `apps/web/src/store.ts` | core | 23474 | 810 | `5f11322625b5` |  |
| `apps/web/src/webauthn.ts` | core | 14224 | 463 | `47dbee43bbc4` |  |
| `apps/web/test/agent-authority.test.ts` | core | 10838 | 337 | `423393396fa2` |  |
| `apps/web/test/agent-native-e2e.ts` | core | 17507 | 534 | `68df01d8eb83` |  |
| `apps/web/test/app.test.ts` | core | 8442 | 281 | `c4c4cbb9b92b` |  |
| `apps/web/test/browser-e2e.ts` | core | 16188 | 498 | `cc0a27568875` |  |
| `apps/web/test/store-rows.test.ts` | core | 2759 | 68 | `eef2ec08037f` |  |
| `apps/web/test/store-schema.test.ts` | schemas | 1833 | 53 | `eb0826f23d57` |  |
| `apps/web/test/verification-entry.test.ts` | core | 3077 | 57 | `645ac661c425` |  |
| `apps/web/tsconfig.json` | config | 447 | 17 | `08ad4932f540` |  |

### chaoxing-autosign — apps/chaoxing-autosign/（11 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `apps/chaoxing-autosign/README.md` | docs | 1023 | 30 | `07748b18c584` |  |
| `apps/chaoxing-autosign/chaoxing_mvp/__init__.py` | core | 465 | 25 | `1ff6cf065b74` |  |
| `apps/chaoxing-autosign/chaoxing_mvp/adapters.py` | core | 2163 | 75 | `1956320663e3` |  |
| `apps/chaoxing-autosign/chaoxing_mvp/cli.py` | core | 1777 | 62 | `a3a6355dd575` |  |
| `apps/chaoxing-autosign/chaoxing_mvp/engine.py` | core | 6550 | 183 | `df6304fc0007` |  |
| `apps/chaoxing-autosign/chaoxing_mvp/ledger.py` | core | 5351 | 166 | `dddbb4fab053` |  |
| `apps/chaoxing-autosign/chaoxing_mvp/models.py` | core | 2877 | 122 | `472907a13152` |  |
| `apps/chaoxing-autosign/chaoxing_mvp/policy.py` | core | 1837 | 49 | `285a6899c4ce` |  |
| `apps/chaoxing-autosign/chaoxing_mvp/ports.py` | core | 1027 | 36 | `e820acfd25c8` |  |
| `apps/chaoxing-autosign/chaoxing_mvp/runner.py` | core | 2164 | 67 | `ed71ee4020f6` |  |
| `apps/chaoxing-autosign/tests/test_chaoxing_autosign_mvp.py` | tests | 11030 | 298 | `52509382feac` |  |

### source-region — （所有非 owner 路径）（441 files）

| path | role | bytes | lines | sha12 | schema |
| --- | --- | ---: | ---: | --- | --- |
| `.agents/skills/artifact-work/SKILL.md` | docs | 6173 | 73 | `c3d0c73ddc7d` |  |
| `.agents/skills/artifact-work/references/audio.md` | docs | 3319 | 32 | `54d26586b796` |  |
| `.agents/skills/artifact-work/references/consumer-acceptance.md` | docs | 5979 | 67 | `3c3e0b5ed082` |  |
| `.agents/skills/artifact-work/references/dataset.md` | docs | 870 | 24 | `f2f7e12b17a6` |  |
| `.agents/skills/artifact-work/references/design-3d.md` | docs | 839 | 25 | `4e9ab7d714c8` |  |
| `.agents/skills/artifact-work/references/geospatial.md` | docs | 814 | 26 | `1dff9863cf44` |  |
| `.agents/skills/artifact-work/references/moving-image.md` | docs | 825 | 25 | `89988ab8a392` |  |
| `.agents/skills/artifact-work/references/presentation.md` | docs | 2820 | 48 | `7d4dc6e43a16` |  |
| `.agents/skills/artifact-work/references/software-release.md` | docs | 998 | 27 | `5c50b4d21de0` |  |
| `.agents/skills/artifact-work/references/still-image.md` | docs | 925 | 29 | `04ca6a81056d` |  |
| `.agents/skills/causal-intervention/SKILL.md` | docs | 3718 | 74 | `36972a234274` |  |
| `.agents/skills/ck-design/SKILL.md` | docs | 3710 | 86 | `96f0605d13e9` |  |
| `.agents/skills/compositional-contracts/SKILL.md` | docs | 5654 | 113 | `b69e10fa0844` |  |
| `.agents/skills/design-structure-matrix/SKILL.md` | docs | 2308 | 64 | `ab04832b6579` |  |
| `.agents/skills/enterprise-work/SKILL.md` | docs | 10909 | 171 | `1172aab730fd` |  |
| `.agents/skills/evidence-calibrated-dialogue/SKILL.md` | docs | 2858 | 33 | `8c44bb33d84b` |  |
| `.agents/skills/evolutionary-search/SKILL.md` | docs | 3216 | 83 | `2bf1af8a954b` |  |
| `.agents/skills/exploration-policy/SKILL.md` | docs | 3553 | 81 | `d6948a58e652` |  |
| `.agents/skills/external-capability-evaluation/SKILL.md` | docs | 4358 | 51 | `c68926622e0d` |  |
| `.agents/skills/external-world-evidence-review/SKILL.md` | docs | 6338 | 44 | `8904eccf9303` |  |
| `.agents/skills/feedback-control/SKILL.md` | docs | 2291 | 56 | `e120887a1770` |  |
| `.agents/skills/feedback-grounded-repair/SKILL.md` | docs | 3034 | 33 | `fe3513f1a46c` |  |
| `.agents/skills/finance-demo-execution/SKILL.md` | docs | 7115 | 125 | `8894b57b7595` |  |
| `.agents/skills/finance-experiment-review/SKILL.md` | docs | 15520 | 256 | `618eaa11533b` |  |
| `.agents/skills/finance-paper-investment/SKILL.md` | docs | 29617 | 474 | `8613c31cdf2c` |  |
| `.agents/skills/finance-paper-risk-review/SKILL.md` | docs | 5163 | 88 | `979a30960bad` |  |
| `.agents/skills/finance-pit-joint-forecast/SKILL.md` | docs | 6868 | 96 | `8238c2f02bbb` |  |
| `.agents/skills/fmea-fta/SKILL.md` | docs | 3388 | 73 | `e533008a0c49` |  |
| `.agents/skills/gateway-formal-routing/SKILL.md` | docs | 4565 | 81 | `fd0a44401b44` |  |
| `.agents/skills/information-flow-analysis/SKILL.md` | docs | 6566 | 99 | `3c2867cf79b9` |  |
| `.agents/skills/media-native-processing/SKILL.md` | docs | 6452 | 104 | `b02730d26018` |  |
| `.agents/skills/media-studio-navigation/SKILL.md` | docs | 6242 | 78 | `cb8515ca85e8` |  |
| `.agents/skills/method-router/SKILL.md` | docs | 7182 | 117 | `a819ef8bb85f` |  |
| `.agents/skills/method-router/references/agent-engineering-delivery.md` | docs | 4121 | 36 | `6986f09d13d2` |  |
| `.agents/skills/method-router/references/innovation-lens-routing.md` | docs | 8793 | 123 | `5a7d6c8fb37d` |  |
| `.agents/skills/method-router/references/method-map.md` | docs | 4158 | 52 | `95a7e4b19e69` |  |
| `.agents/skills/method-router/references/representation-first.md` | docs | 7781 | 91 | `23e9cad3e8b0` |  |
| `.agents/skills/minimum-sufficient-representation/SKILL.md` | docs | 3065 | 53 | `3f1a9fb331f4` |  |
| `.agents/skills/mobile-app-security/SKILL.md` | docs | 9279 | 193 | `c6c9c745eb55` |  |
| `.agents/skills/mobile-app-security/references/top3-upstream-notes.md` | docs | 3703 | 61 | `0c13e045a950` |  |
| `.agents/skills/natural-chinese-writing/SKILL.md` | docs | 3254 | 33 | `7da0a8623b9d` |  |
| `.agents/skills/ordivon-security-owner/SKILL.md` | docs | 5176 | 33 | `7e69eadb8668` |  |
| `.agents/skills/organizational-cybernetics/SKILL.md` | docs | 3887 | 80 | `fdf36f3ec45e` |  |
| `.agents/skills/ppt-master/SKILL.md` | docs | 5104 | 75 | `61b32af36303` |  |
| `.agents/skills/project-kernel-decomposition/SKILL.md` | docs | 10111 | 279 | `3b56af1ca03f` |  |
| `.agents/skills/project-kernel-decomposition/references/decomposition-contract.md` | docs | 2372 | 84 | `d3d101dd3efc` |  |
| `.agents/skills/project-kernel-decomposition/references/node-graph-contract.md` | docs | 6223 | 193 | `b12b98543198` |  |
| `.agents/skills/recursive-lego-calculus/SKILL.md` | docs | 19261 | 236 | `48def885f0c5` |  |
| `.agents/skills/recursive-lego-calculus/references/consumer-rooted-retirement.md` | docs | 6221 | 105 | `945bb4ed1390` |  |
| `.agents/skills/recursive-lego-calculus/references/formal-model.md` | docs | 41462 | 703 | `cc3cd10cdaa4` |  |
| `.agents/skills/recursive-lego-calculus/references/formal-thinking-legos-human-agent.md` | docs | 25055 | 329 | `945760348c30` |  |
| `.agents/skills/recursive-lego-calculus/references/owner-provider-human-agent.md` | docs | 5718 | 96 | `d30dd48c50a4` |  |
| `.agents/skills/research-claim-framing/SKILL.md` | docs | 3105 | 33 | `55f2cab2d068` |  |
| `.agents/skills/research-publication-closure/SKILL.md` | docs | 2572 | 59 | `814cc4d8c231` |  |
| `.agents/skills/research-publication-perceptual-conformance/SKILL.md` | docs | 2964 | 90 | `bce717c20a4f` |  |
| `.agents/skills/skill-supply-chain-audit/SKILL.md` | docs | 6481 | 130 | `40ce2df931d8` |  |
| `.agents/skills/skill-supply-chain-audit/references/skillspector-contract.md` | docs | 1679 | 38 | `9d24b207c8e7` |  |
| `.agents/skills/stpa/SKILL.md` | docs | 2507 | 63 | `657a3dc10ea7` |  |
| `.agents/skills/systems-engineering/SKILL.md` | docs | 2417 | 49 | `ff271165f678` |  |
| `.agents/skills/task-space-reentry/SKILL.md` | docs | 3153 | 29 | `8bdb99523288` |  |
| `.agents/skills/task-space-reentry/references/task-packet.md` | docs | 7192 | 107 | `05f876326110` |  |
| `.agents/skills/task-space-reentry/scripts/check_obligation_handoff.py` | core | 6442 | 139 | `297e85d37b9b` |  |
| `.agents/skills/web-provider-routing/SKILL.md` | docs | 4673 | 74 | `22c97201f66e` |  |
| `.github/CODEOWNERS` | other | 757 | — | `419f8105b768` |  |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | config | 850 | 35 | `c30154547525` |  |
| `.github/ISSUE_TEMPLATE/config.yml` | config | 28 | 1 | `1f103c6a9dd0` |  |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | config | 616 | 23 | `3438c1fe8f7c` |  |
| `.github/ISSUE_TEMPLATE/game-player-feedback.yml` | config | 1841 | 61 | `5366e7d878b4` |  |
| `.github/PULL_REQUEST_TEMPLATE.md` | docs | 737 | 28 | `368e9e950c45` |  |
| `.github/dependabot.yml` | config | 1412 | 48 | `3ac98c1dd4c6` |  |
| `.github/workflows/ci.yml` | config | 57590 | 1190 | `a5ab28ab6d3b` |  |
| `.github/workflows/codeql.yml` | config | 1463 | 49 | `c475e17a13bf` |  |
| `.github/workflows/game-factory.yml` | config | 4257 | 128 | `fcb797d5d5aa` |  |
| `.github/workflows/game-orbit-factory.yml` | config | 3407 | 78 | `efa769e9d0cc` |  |
| `.github/workflows/game-rules-proof.yml` | config | 1097 | 39 | `2c1166c73f0e` |  |
| `.github/workflows/runtime-release.yml` | config | 12427 | 288 | `39c5954dd154` |  |
| `.gitignore` | other | 442 | — | `b8875a83372a` |  |
| `.gitleaksignore` | other | 9373 | — | `c52b9ed75b93` |  |
| `AGENTS.md` | docs | 11049 | 88 | `08e4c946d5aa` |  |
| `CONTRIBUTING.md` | docs | 1971 | 31 | `42d468ded35a` |  |
| `LICENSE` | other | 11357 | — | `c71d239df917` |  |
| `README.md` | docs | 8514 | 91 | `4d6444623db3` |  |
| `SECURITY.md` | docs | 1645 | 17 | `ebc0f94d19dc` |  |
| `catalogs/data-products/experimental-episode-corpus-r1/acceptance.json` | config | 1967 | 26 | `cf97dfaeae76` | 1 |
| `catalogs/data-products/experimental-episode-corpus-r1/artifact-dataset-contract.json` | config | 1148 | 53 | `2ca600033b0c` |  |
| `catalogs/data-products/experimental-episode-corpus-r1/governance-policy.odrl.jsonld` | other | 509 | — | `414d63af04ba` |  |
| `catalogs/data-products/experimental-episode-corpus-r1/odcs.json` | config | 6751 | 205 | `cef627ce2eee` |  |
| `catalogs/data-products/experimental-episode-corpus-r1/odps.json` | config | 7496 | 209 | `6691c6168c7d` |  |
| `catalogs/knowledge/README.md` | docs | 3346 | 58 | `d57a5d33dbb1` |  |
| `catalogs/knowledge/evidence/acceptance/agent-architecture-lego-catalog-r1.json` | evidence | 4832 | 111 | `7122e567588e` | 1 |
| `catalogs/knowledge/evidence/acceptance/agent-service-control-stability-r1.json` | evidence | 2124 | 58 | `798328040867` | 1 |
| `catalogs/knowledge/evidence/agent-campaigns/agent-common-structure-destroyer-r1-C01.md` | evidence | 22426 | 528 | `84e1e4dfbd55` |  |
| `catalogs/knowledge/evidence/agent-campaigns/prompt-corpus-common-structure-r1-wave1-recovered.md` | evidence | 12578 | 435 | `eaebe8569b43` |  |
| `catalogs/knowledge/evidence/analysis/agent-service-control-stability-r1.json` | evidence | 4322 | 103 | `72bd34dbc029` | 1 |
| `catalogs/knowledge/graphs/agent-architecture-lego-catalog-r1.json` | config | 10198 | 109 | `059db384b315` | 1 |
| `catalogs/knowledge/graphs/ai-miracle-material-lego-case-r1.json` | config | 14583 | 528 | `404a020aac81` | 1 |
| `catalogs/knowledge/graphs/browser-security-detector-coverage-r6.json` | config | 6603 | 153 | `acbb0f37d1e1` | 1 |
| `catalogs/knowledge/graphs/browser-security-detector-coverage-r9.json` | config | 8639 | 166 | `df3390a6f300` | 1 |
| `catalogs/knowledge/graphs/cloudflare-provider-security-boundary-r1.json` | config | 12795 | 406 | `3635e7b9076e` | 1 |
| `catalogs/knowledge/graphs/ordivon-agent-birth-r1.json` | config | 22391 | 824 | `b5682a35d32c` | 1 |
| `catalogs/knowledge/graphs/ordivon-agent-service-control-stability-r1.json` | config | 4633 | 115 | `4964dcf030af` | 1 |
| `catalogs/knowledge/graphs/zcode-workspace-snapshot-security-lego-r1.json` | config | 8262 | 289 | `a0f098e11e69` | 1 |
| `catalogs/knowledge/lessons/agent-architecture-lego-catalog-r1.md` | docs | 32866 | 681 | `2aa0c211759e` |  |
| `catalogs/knowledge/lessons/agent-birth-provider-boundary-r1.md` | docs | 6519 | 215 | `e412bf851a5a` |  |
| `catalogs/knowledge/lessons/agent-product-common-structure-r1-wave3-partial.md` | docs | 11706 | 396 | `e165136d2c32` |  |
| `catalogs/knowledge/lessons/agent-product-common-structure-r1.md` | docs | 17494 | 546 | `b6e2f9bf37e6` |  |
| `catalogs/knowledge/lessons/agent-security-cross-domain-destroyer-r1.md` | docs | 22725 | 785 | `c59598348716` |  |
| `catalogs/knowledge/lessons/agent-security-cross-system-destroyer-r1.md` | docs | 24859 | 681 | `4bb6ac3811a8` |  |
| `catalogs/knowledge/lessons/agent-security-lego-r1.md` | docs | 15876 | 566 | `f828066dfb6d` |  |
| `catalogs/knowledge/lessons/agent-service-regime-card-r1.md` | docs | 14050 | 336 | `fb0d12fd08df` |  |
| `catalogs/knowledge/lessons/agent-skills-kernel.md` | docs | 8779 | 197 | `506195af061b` |  |
| `catalogs/knowledge/lessons/ai-miracle-material-lego-case-r1.md` | docs | 19495 | 461 | `a65c5aa0c174` |  |
| `catalogs/knowledge/lessons/authority-mature-substrate-decomposition-r1.md` | docs | 12207 | 153 | `f6305b22f68a` |  |
| `catalogs/knowledge/lessons/aws-agentcore-agent-service-kernel-r1.md` | docs | 15261 | 296 | `c61ed338ad69` |  |
| `catalogs/knowledge/lessons/browser-automation-dynamic-defense-r1.md` | docs | 20774 | 218 | `8d6f5a54af5a` |  |
| `catalogs/knowledge/lessons/browser-use-agent-browser-kernel.md` | docs | 8214 | 224 | `3bdee314345b` |  |
| `catalogs/knowledge/lessons/browserless-source-deep-dive-r1.md` | docs | 7513 | 172 | `1b4ed7376581` |  |
| `catalogs/knowledge/lessons/camoufox-source-deep-dive-r1.md` | docs | 6460 | 144 | `f4a5ae075f3c` |  |
| `catalogs/knowledge/lessons/cloudflare-provider-security-boundary-r1.md` | docs | 5719 | 207 | `679053b79a17` |  |
| `catalogs/knowledge/lessons/cloudflare-provider-security-exp-r1.md` | docs | 5308 | 152 | `08a8404dabf7` |  |
| `catalogs/knowledge/lessons/cloudflare-provider-security-exp-r2.md` | docs | 6925 | 200 | `3d877fd32cf8` |  |
| `catalogs/knowledge/lessons/cloudflare-provider-security-exp-r5.md` | docs | 8101 | 202 | `e2c5d9fae22e` |  |
| `catalogs/knowledge/lessons/cloudflare-provider-security-exp-r9.md` | docs | 6428 | 210 | `580cf1628254` |  |
| `catalogs/knowledge/lessons/composition-science-foundations-r1.md` | docs | 3873 | 98 | `645284d94daf` |  |
| `catalogs/knowledge/lessons/dagster-asset-orchestration-kernel.md` | docs | 10364 | 319 | `9917d1d28fc3` |  |
| `catalogs/knowledge/lessons/dify-ai-application-platform-kernel.md` | docs | 11038 | 351 | `ad8ae8553e1e` |  |
| `catalogs/knowledge/lessons/firecrawl-web-context-kernel.md` | docs | 9774 | 339 | `3b3b80089b64` |  |
| `catalogs/knowledge/lessons/flaresolverr-source-deep-dive-r1.md` | docs | 5758 | 131 | `3f2f2a8c5b04` |  |
| `catalogs/knowledge/lessons/langfuse-phoenix-ai-engineering-platform-kernel.md` | docs | 9297 | 303 | `ea04ef07ce61` |  |
| `catalogs/knowledge/lessons/langgraph-agent-state-machine-kernel.md` | docs | 10691 | 354 | `b505dd629c32` |  |
| `catalogs/knowledge/lessons/lego-question-compiler-outcome-pressure-r1.md` | docs | 4833 | 83 | `f79988ecab44` |  |
| `catalogs/knowledge/lessons/lego-self-analysis-wave1-r1.md` | docs | 4059 | 131 | `3e9a565ae01f` |  |
| `catalogs/knowledge/lessons/lego-theory-foundations-r1.md` | docs | 3314 | 98 | `d8869634b1a4` |  |
| `catalogs/knowledge/lessons/lego-wave2-prospective-validation-r1.md` | docs | 10797 | 325 | `a452d202b704` |  |
| `catalogs/knowledge/lessons/lego-wave23-self-audit-r1.md` | docs | 3341 | 94 | `a5406cb12ddf` |  |
| `catalogs/knowledge/lessons/lego-wave3-prospective-validation-r1.md` | docs | 6539 | 164 | `5ace8a1a1056` |  |
| `catalogs/knowledge/lessons/litellm-model-gateway-kernel.md` | docs | 11338 | 341 | `024095557a8c` |  |
| `catalogs/knowledge/lessons/llamaindex-haystack-context-retrieval-kernel.md` | docs | 9819 | 325 | `74dff90f2e29` |  |
| `catalogs/knowledge/lessons/markitdown-document-normalization-kernel.md` | docs | 7942 | 249 | `b724bac74e8c` |  |
| `catalogs/knowledge/lessons/mcp-interoperability-kernel.md` | docs | 11177 | 331 | `923ee34ec27d` |  |
| `catalogs/knowledge/lessons/microsoft-activation-scripts-avoidance-study.md` | docs | 9682 | 237 | `6a6f6378c982` |  |
| `catalogs/knowledge/lessons/microsoft-activation-scripts-deep-architecture-study.md` | docs | 28904 | 849 | `b1fd3a806fec` |  |
| `catalogs/knowledge/lessons/microsoft-foundry-agent-service-kernel-r1.md` | docs | 9701 | 242 | `98a7f04ff9df` |  |
| `catalogs/knowledge/lessons/n8n-dsh-node-composition-r1.md` | docs | 5113 | 150 | `1994ed9d688b` |  |
| `catalogs/knowledge/lessons/n8n-integration-kernel.md` | docs | 5841 | 142 | `4d4c84ea101d` |  |
| `catalogs/knowledge/lessons/oh-my-pi-adaptive-edit-abi-kernel.md` | docs | 8952 | 268 | `2375239b14fd` |  |
| `catalogs/knowledge/lessons/oh-my-pi-child-run-agent-hub-kernel.md` | docs | 8884 | 288 | `f7d869350f55` |  |
| `catalogs/knowledge/lessons/oh-my-pi-harness-mechanism-map.md` | docs | 6669 | 204 | `060b965e7c2c` |  |
| `catalogs/knowledge/lessons/ordivon-agent-birth-lego-r1.md` | docs | 22824 | 660 | `93813625660f` |  |
| `catalogs/knowledge/lessons/ordivon-agent-service-control-stability-r1.md` | docs | 10507 | 467 | `6741447c3654` |  |
| `catalogs/knowledge/lessons/otel-openinference-observability-kernel.md` | docs | 8871 | 272 | `098d72c677b2` |  |
| `catalogs/knowledge/lessons/patchright-source-deep-dive-r1.md` | docs | 7505 | 162 | `a075f4161e0a` |  |
| `catalogs/knowledge/lessons/poker-ai-lego-question-compiler-pilot-r1.md` | docs | 10156 | 213 | `5e145cd46acb` |  |
| `catalogs/knowledge/lessons/qdrant-vector-search-kernel.md` | docs | 9135 | 279 | `fdc90f819f83` |  |
| `catalogs/knowledge/lessons/rebrowser-patches-source-deep-dive-r1.md` | docs | 6857 | 174 | `0f0c9499ff98` |  |
| `catalogs/knowledge/lessons/seleniumbase-source-deep-dive-r1.md` | docs | 6232 | 162 | `f629534437bd` |  |
| `catalogs/knowledge/lessons/spec-kit-engineering-kernel.md` | docs | 7446 | 171 | `ef4096a20f33` |  |
| `catalogs/knowledge/lessons/superpowers-engineering-discipline-kernel.md` | docs | 11126 | 269 | `e526f5230c01` |  |
| `catalogs/knowledge/lessons/system-prompts-corpus-deep-architecture-study.md` | docs | 25962 | 898 | `e6a51357b5c8` |  |
| `catalogs/knowledge/lessons/temporal-durable-execution-kernel.md` | docs | 12153 | 327 | `32fa4c2dba70` |  |
| `catalogs/knowledge/lessons/worktrunk-workspace-native-git-r1.md` | docs | 1565 | 11 | `9742ae0f0f13` |  |
| `catalogs/knowledge/lessons/zcode-workspace-snapshot-security-lego-r1.md` | docs | 12729 | 459 | `06e2321abc0e` |  |
| `docs/architecture/AGENT_CONCEPTS_FORMAL_LEGO_RESEARCH_20261024.md` | docs | 30848 | 309 | `9be2372c108d` |  |
| `docs/architecture/AGENT_CONTRACT_EXECUTION_SPEC_R1.md` | docs | 42321 | 305 | `026c310021bf` |  |
| `docs/architecture/AGENT_OUTCOME_CONSTRAINT_EXECUTION_SPEC_R1.md` | docs | 21192 | 220 | `1294c1ba07df` |  |
| `docs/architecture/AGENT_OUTCOME_REALIZATION_R21_SPEC_20261109.md` | docs | 37798 | 383 | `0e39e28e7bc4` |  |
| `docs/architecture/AGENT_PLUGIN_BOUNDARY_R2.md` | docs | 26696 | 613 | `c6db4cf2cb18` |  |
| `docs/architecture/AGENT_PLUGIN_CORE_R3.md` | docs | 22784 | 587 | `b13a380ae8f4` |  |
| `docs/architecture/AGENT_PLUGIN_R4_ACCEPTANCE_20260921.md` | docs | 3381 | 82 | `7506917e3f48` |  |
| `docs/architecture/ARCHITECTURE_CONVERGENCE_A01R2.md` | docs | 3833 | 82 | `80df286e6558` |  |
| `docs/architecture/AUTHORITY_SEMANTIC_EXPRESSION_R1.md` | docs | 8233 | 158 | `d1e4c881de8a` |  |
| `docs/architecture/C03_SKILL_BRIDGE_CONSUMER_CENSUS_R1.md` | docs | 3398 | 68 | `d387d812d370` |  |
| `docs/architecture/CAPABILITY_PACKAGES_R1.md` | docs | 28807 | 610 | `ac47d8bcc79d` |  |
| `docs/architecture/COMMERCIAL_STRATEGY_CURRENT_FACTS_R1.md` | docs | 12085 | 191 | `eef5c224c712` |  |
| `docs/architecture/COMPOSITION_SCIENCE_R1.md` | docs | 28604 | 849 | `6356dbc17c67` |  |
| `docs/architecture/COUNTEREXAMPLE_GUIDED_REPRESENTATION_R1.md` | docs | 10375 | 136 | `18596ed5d6ef` |  |
| `docs/architecture/CROSS_DOMAIN_VERIFICATION_R3.md` | docs | 8528 | 298 | `70ccb432acda` |  |
| `docs/architecture/CURRENT_ARCHITECTURE.md` | docs | 16159 | 287 | `b6c9fa82b07a` |  |
| `docs/architecture/DATA_DURABLE_PRESERVATION_R1.md` | docs | 4984 | 140 | `29d3e84d5645` |  |
| `docs/architecture/DATA_LIFECYCLE_CENSUS_R1.md` | docs | 13920 | 217 | `34eb659f510e` |  |
| `docs/architecture/DATA_PRODUCTS_FEDERATION_R1.md` | docs | 3390 | 107 | `d120b0084e9a` |  |
| `docs/architecture/DATA_PRODUCT_CONSUMPTION_FEEDBACK_R1.md` | docs | 3155 | 118 | `1905ddbea5b7` |  |
| `docs/architecture/DECISIONS.md` | docs | 1509 | 13 | `d41da17a08d7` |  |
| `docs/architecture/ENTERPRISE_OPERATING_MODEL_R1.md` | docs | 28652 | 478 | `7fec89b167ed` |  |
| `docs/architecture/EVIDENCE_BOUNDARY_CENSUS_R1.md` | docs | 939 | 12 | `16b6d6a0edfb` |  |
| `docs/architecture/EXTERNAL_INNOVATION_THEORY_CENSUS_R1.md` | docs | 28832 | 780 | `7bbaab23eba4` |  |
| `docs/architecture/GATEWAY_B02_CAPABILITY_PROJECTION_ACCEPTANCE_20260921.md` | docs | 1468 | 31 | `e418805b2d5e` |  |
| `docs/architecture/GATEWAY_CAPABILITY_AUTHZ_CONTRACT_R1.md` | docs | 1748 | 33 | `da7ca14c29b9` |  |
| `docs/architecture/GATEWAY_HOST_NORTHBOUND_ACCEPTANCE_20260922.md` | docs | 3942 | 96 | `a9c9bbc4ab91` |  |
| `docs/architecture/LEARNING_DATA_OWNERSHIP_CENSUS_R1.md` | docs | 1187 | 14 | `40c106900b9a` |  |
| `docs/architecture/LEGO_THEORY_WAVE2_R1.md` | docs | 5284 | 142 | `26d74922f183` |  |
| `docs/architecture/LEGO_THEORY_WAVE3_R1.md` | docs | 4717 | 126 | `f9b9bff4544f` |  |
| `docs/architecture/ORDIVON_COMPOSITION_ARCHITECTURE_EXECUTION_PLAN_R1.md` | docs | 12680 | 273 | `65a738a9cf4f` |  |
| `docs/architecture/ORDIVON_COMPOSITION_ARCHITECTURE_R1.md` | docs | 7780 | 145 | `1e46dc251c28` |  |
| `docs/architecture/OWNER_DEPENDENCY_BOUNDARY_R1.md` | docs | 2225 | 45 | `26dc5b661e4b` |  |
| `docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md` | docs | 28723 | 196 | `c701f6f173ad` |  |
| `docs/architecture/RESEARCH_PUBLICATION_CLOSURE_R1.md` | docs | 3595 | 92 | `e6e9aa1705a8` |  |
| `docs/architecture/RESEARCH_PUBLICATION_PERCEPTUAL_CONFORMANCE_R2.md` | docs | 6009 | 195 | `10f40f330af6` |  |
| `docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md` | docs | 5554 | 117 | `9aae3e43a9a0` |  |
| `docs/architecture/SKILLS.md` | docs | 3487 | 49 | `f6f297df9bb4` |  |
| `docs/architecture/STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R1.md` | docs | 11745 | 210 | `7f23dff46d93` |  |
| `docs/architecture/STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2.md` | docs | 16552 | 336 | `bef2da04a9fd` |  |
| `docs/architecture/STRUCTURE_R2.md` | docs | 8991 | 196 | `928c8c0825f9` |  |
| `docs/architecture/TESTING_UPSTREAM_ADOPTION_R1.md` | docs | 20876 | 195 | `3bbec041b7bc` |  |
| `docs/architecture/agent-native-measurement-improvement-loop-r1.json` | config | 6592 | 270 | `f6e7bdb8a836` | 1 |
| `docs/architecture/agent-plugin-adoption-r1.md` | docs | 12123 | 164 | `47072a204c3e` |  |
| `docs/architecture/architecture-convergence-a01r2.json` | config | 497 | 19 | `9206c38c6282` | 1 |
| `docs/architecture/c03-skill-bridge-consumer-census-r1.json` | config | 2945 | 66 | `13fd5adf5a52` | 1 |
| `docs/architecture/classification.md` | docs | 3540 | 55 | `b9be6116906a` |  |
| `docs/architecture/convergence-queue-lego-r1.json` | config | 11035 | 344 | `1634b9daa90d` | 1 |
| `docs/architecture/deployed-architecture-r1.json` | config | 6205 | 191 | `37723f38e2c7` | 1 |
| `docs/architecture/e01-e02-trace-identity-acceptance-20260921.json` | config | 3151 | 87 | `1b4851fad2b7` | 1 |
| `docs/architecture/e01-trace-context-contract-r1.json` | config | 1020 | 34 | `978deee53790` | 1 |
| `docs/architecture/e02-authenticated-principal-boundary-r2.json` | config | 908 | 32 | `2306c95d0a01` | 2 |
| `docs/architecture/evidence-boundary-census-r1.json` | config | 2958 | 96 | `32ddb28f7f0f` | 1 |
| `docs/architecture/evidence/CONVERGENCE_OBSERVATION_DATASET_R1.json` | evidence | 3521 | 96 | `3642500e0b40` | 1 |
| `docs/architecture/evidence/CONVERGENCE_OWNER_COST_F2EC_R1.json` | evidence | 3811 | 141 | `3db6c79c6b26` | 1 |
| `docs/architecture/evidence/CONVERGENCE_QUEUE_TELEMETRY_BASELINE_R1.json` | evidence | 6397 | 208 | `f4421c21be97` | 1 |
| `docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261024_R1.json` | evidence | 200773 | 2602 | `65285489c73c` | 1 |
| `docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261024_R2.json` | evidence | 5656 | 97 | `736f32bd9842` | 1 |
| `docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261025_R1.json` | evidence | 53035 | 581 | `1fe29d92afd1` | 1 |
| `docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261101_R1.json` | evidence | 13111 | 201 | `75aa4d11fba7` | 1 |
| `docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261101_R2.json` | evidence | 20372 | 299 | `537806f34b30` | 1 |
| `docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261107_R1.json` | evidence | 56569 | 980 | `301fe21f4a7b` | 1 |
| `docs/architecture/evidence/ORDIVON_PHASE1_NAME_SEEDS_20261027_R4.json` | evidence | 50966 | 1201 | `96a38e4230ba` |  |
| `docs/architecture/evidence/PHASE1_LINUX_UNIT_DRIFT_FACETS_20261027_R1.json` | evidence | 11098 | 232 | `05eaecc99e35` | 1 |
| `docs/architecture/evidence/PHASE1_R8_148_NODES_UPSTREAM_PARITY_20261028.json` | evidence | 215400 | 5373 | `9b3f1ceeeb03` | 1 |
| `docs/architecture/evidence/PHASE1_SOURCE_INSTALLED_BOUNDARIES_20261027_R1.json` | evidence | 6357 | 179 | `5c872d89c352` | 1 |
| `docs/architecture/evidence/PHASE1_WHOLE_SYSTEM_NEGATIVE_SPACE_20261028_R1.json` | evidence | 20286 | 613 | `da53fa3c7604` | 1 |
| `docs/architecture/evidence/lego-theory-wave2-prospective-r1.json` | evidence | 3541 | 68 | `4c155c13e3be` | 1 |
| `docs/architecture/evidence/lego-theory-wave3-prospective-r1.json` | evidence | 2805 | 68 | `a4b47628db74` | 1 |
| `docs/architecture/experimental-episode-r1.md` | docs | 2694 | 84 | `2942e5289223` |  |
| `docs/architecture/gateway-single-agent-northbound-acceptance-20260926.json` | config | 6067 | 111 | `9261a639f16b` | 1 |
| `docs/architecture/gateway-swf-northbound-acceptance-20260924.json` | config | 2559 | 94 | `14e1cf8e64d0` | 1 |
| `docs/architecture/intent-field-census-r1.json` | config | 3146 | 119 | `a96366b65bda` | 1 |
| `docs/architecture/ordivon-composition-architecture-lego-r1.json` | config | 23573 | 621 | `560a979afb6f` | 1 |
| `docs/architecture/persistent-trace-backend-acceptance-20260921.json` | config | 1947 | 59 | `9cab09794c1d` | 1 |
| `docs/architecture/policies/CONSUMPTION_BOUNDARY_R1.md` | docs | 4332 | 55 | `dd9c5d7e7c2b` |  |
| `docs/architecture/policies/EXTERNAL_OWNERSHIP_BOUNDARY.md` | docs | 3962 | 57 | `4e384b4e7c12` |  |
| `docs/architecture/policies/README.md` | docs | 4239 | 33 | `b88bd7608a4f` |  |
| `docs/architecture/policies/external-ownership-boundary.json` | config | 14992 | 424 | `2252f28ca11b` | 1 |
| `docs/architecture/research-study-authority-r1.json` | config | 2487 | 73 | `1ddca32e5796` | 1 |
| `docs/architecture/schemas/convergence-ci-economic-annotation-v1.schema.json` | schemas | 1360 | 25 | `01f657b8674f` |  |
| `docs/architecture/schemas/convergence-ci-observation-v1.schema.json` | schemas | 3631 | 188 | `af14146ee9f4` |  |
| `docs/architecture/schemas/convergence-owner-cost-episode-v1.schema.json` | schemas | 1999 | 36 | `9e90dda25252` |  |
| `docs/architecture/schemas/convergence-pressure-assessment-v1.schema.json` | schemas | 1748 | 78 | `50aaa628725d` |  |
| `docs/architecture/schemas/convergence-queue-observation-v1.schema.json` | schemas | 2804 | 136 | `6cae776a1ba7` |  |
| `docs/architecture/structure-r2-transition-r1.json` | config | 25017 | 857 | `920c4f30f283` | 1 |
| `docs/migration/acceptance/HARNESS_SECURITY_OWNER_CONSUMER_CUTOVER_ACCEPTANCE_20260921.md` | docs | 6531 | 130 | `c55437f08e84` |  |
| `docs/migration/retirement/business-operations-erpnext-r1.md` | docs | 10635 | 229 | `495de510919d` |  |
| `docs/migration/retirement/codex-harness-mcp-retirement.md` | docs | 2165 | 30 | `cb5d0423b1c8` |  |
| `docs/migration/retirement/commercial-marketing-externalization-r1.md` | docs | 3726 | 80 | `bf237bc635f9` |  |
| `docs/migration/retirement/commercial-practice-externalization.md` | docs | 3782 | 45 | `f57158aad9a7` |  |
| `docs/migration/retirement/commercial-strategy-debt-externalization-r1.md` | docs | 1958 | 40 | `80c77b0a8a6a` |  |
| `docs/migration/retirement/harness-standalone-policy.json` | config | 1806 | 48 | `08b18cd11127` | 1 |
| `docs/migration/retirement/host-v2-standalone-policy.json` | config | 1186 | 37 | `9ecd56b64f03` | 1 |
| `docs/migration/retirement/media-standalone-policy.json` | config | 1606 | 43 | `2fbc6bd1a0b7` | 1 |
| `docs/migration/retirement/network-v2-standalone-policy.json` | config | 1186 | 37 | `78ed735847e6` | 1 |
| `docs/migration/retirement/next-standalone-policy.json` | config | 1997 | 50 | `2bee5601af1d` | 1 |
| `docs/migration/retirement/runtime-standalone-policy.json` | config | 2632 | 55 | `b9efa0a70f38` | 1 |
| `docs/migration/retirement/workstation-lab-policy.json` | config | 2766 | 72 | `36f482fa25c6` | 1 |
| `docs/migration/retirement/workstation-v2-standalone-policy.json` | config | 1858 | 54 | `7f3f801c12dd` | 1 |
| `docs/start/README.md` | docs | 3461 | 61 | `88fad5e1d6f5` |  |
| `docs/start/agent-first-run.md` | docs | 5623 | 111 | `3157fae84652` |  |
| `docs/start/human-first-run.md` | docs | 2376 | 52 | `6c1bde20c939` |  |
| `docs/start/tasks.md` | docs | 2266 | 42 | `8adf8ee6487f` |  |
| `mise.toml` | config | 11781 | 412 | `d85e75310663` |  |
| `profiles/domains/README.md` | docs | 769 | 18 | `0a385172eab4` |  |
| `profiles/domains/game/GAME_AUTONOMOUS_INTEREST_PROTOCOL_R7.md` | docs | 16486 | 358 | `2d6ca85ccd3d` |  |
| `profiles/domains/game/README.md` | docs | 776 | 7 | `69e0f975a6dd` |  |
| `profiles/domains/game/game-autonomous-interest-model-r7.schema.json` | schemas | 4968 | 244 | `34fd3da5cea9` |  |
| `profiles/domains/game/game-autonomous-interest-protocol-r7.json` | config | 21902 | 438 | `d330371daeaf` | 7 |
| `profiles/research/mechanical-components/research-mechanical-component-r1.schema.json` | schemas | 2376 | 120 | `662685da9b70` |  |
| `profiles/research/publication/carrier-attestation-r1.schema.json` | schemas | 1245 | 45 | `01353eb7014e` |  |
| `profiles/research/publication/finding-r1.schema.json` | schemas | 902 | 28 | `ae4e85cd61b0` |  |
| `profiles/research/publication/observer-report-r1.schema.json` | schemas | 2028 | 66 | `c6a98eeebd15` |  |
| `profiles/research/publication/observer-task-envelope-r1.schema.json` | schemas | 1389 | 49 | `196cb47eaef3` |  |
| `profiles/research/publication/perceptual-conformance-r1.json` | research | 2849 | 93 | `4a29b90a6b0e` | 1 |
| `profiles/research/publication/perceptual-conformance-r1.schema.json` | schemas | 1447 | 46 | `4607726f5246` |  |
| `profiles/research/publication/publication-closure-r1.json` | research | 1982 | 54 | `a3891f00be71` | 1 |
| `profiles/research/publication/publication-closure-r2.json` | research | 2036 | 52 | `dee1a389c48d` | 2 |
| `profiles/research/tool-qualification/TOOL_QUALIFICATION_R1.md` | research | 1899 | 29 | `16b9569265e3` |  |
| `profiles/research/tool-qualification/examples/worktrunk-workspace-r1.json` | research | 1159 | 27 | `b06f00f7f08b` | r1 |
| `profiles/research/tool-qualification/tool-qualification-packet-r1.schema.json` | schemas | 4144 | 208 | `c472a400a831` |  |
| `renovate.json` | config | 385 | 13 | `ccb6c37fd577` |  |
| `studies/data-lifecycle/data-lifecycle-census-r1.json` | research | 7819 | 280 | `aa029de8658c` | 1 |
| `studies/data-lifecycle/data-lifecycle-census-r2.json` | research | 6233 | 210 | `a73e317337aa` | 2 |
| `studies/data-lifecycle/data-lifecycle-census-r3.json` | research | 7016 | 211 | `de24264226fe` | 3 |
| `studies/data-lifecycle/data-lifecycle-census-r4.json` | research | 8412 | 225 | `d64f6da2dbf3` | 4 |
| `studies/data-lifecycle/data-lifecycle-census-r5.json` | research | 9877 | 234 | `272c9944c02f` | 5 |
| `studies/data-lifecycle/data-lifecycle-census-r6.json` | research | 10843 | 240 | `d702ce6310ab` | 6 |
| `studies/data-lifecycle/evidence/data-products-r1/acceptance.json` | evidence | 6420 | 109 | `a8e1e6fc1d6e` | 1 |
| `studies/data-lifecycle/evidence/data-products-r1/federated-catalog.dcat.jsonld` | evidence | 3712 | — | `9acbc862c62e` |  |
| `studies/data-lifecycle/evidence/data-products-r1/product-provenance.prov.jsonld` | evidence | 5090 | — | `439ac60abae4` |  |
| `studies/data-lifecycle/evidence/data-products-r2/acceptance.json` | evidence | 1439 | 30 | `48d80988582d` | 2 |
| `studies/data-lifecycle/evidence/data-products-r2/federated-catalog.dcat.jsonld` | evidence | 5809 | — | `5446baeb4d4d` |  |
| `studies/data-lifecycle/evidence/data-products-r2/product-provenance.prov.jsonld` | evidence | 8638 | — | `a96fa9457733` |  |
| `studies/data-lifecycle/evidence/experimental-episode-rw5/acceptance.json` | evidence | 2723 | 58 | `842974bc9bdb` | 1 |
| `studies/data-lifecycle/evidence/experimental-episode-rw5/observability.json` | evidence | 1547 | 51 | `03b2bdd06a62` | 1 |
| `studies/data-lifecycle/evidence/experimental-episode-rw5/standard-validation.json` | evidence | 1145 | 42 | `46515610aa89` | 1 |
| `studies/data-lifecycle/evidence/github-pilot-r1/.gitignore` | evidence | 52 | — | `f46884dd84bd` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/analysis/analysis-summary.json` | evidence | 378 | 13 | `bfa82f405a71` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/analysis/crossref-country-metadata-rates.csv` | evidence | 11026 | — | `7afbc415dd98` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/analysis/se4all-yearly-country-means.csv` | evidence | 1165 | — | `37126bb9e145` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/catalog/catalog.dcat.jsonld` | evidence | 4573 | — | `76515da85858` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/contracts/crossref-member-participation.odcs.json` | schemas | 10107 | 315 | `064a0b502c66` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/contracts/crossref-metadata-coverage.odcs.json` | schemas | 20481 | 632 | `5605e85db827` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/contracts/se4all-energy.odcs.json` | schemas | 24578 | 718 | `abb9ac17264e` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/lineage/crossref-transform.openlineage.json` | evidence | 2217 | 59 | `5e9a59e31db3` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/lineage/se4all-transform.openlineage.json` | evidence | 1518 | 47 | `0a6c983f3bf3` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/manifest.json` | evidence | 3969 | 105 | `3e3c9d861789` | 1 |
| `studies/data-lifecycle/evidence/github-pilot-r1/quality-report.json` | evidence | 5298 | 129 | `ba73974ab50c` | 1 |
| `studies/data-lifecycle/evidence/github-pilot-r1/semantics/external-semantic-profile.json` | evidence | 5237 | 140 | `f3b43eb5150e` | 1 |
| `studies/data-lifecycle/evidence/github-pilot-r1/source/acquisition-policy.json` | evidence | 2711 | 34 | `d05b1986e3a2` | 1 |
| `studies/data-lifecycle/evidence/github-pilot-r1/source/repository.txt` | evidence | 51 | 1 | `d45ae52b6df8` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/source/standards.json` | evidence | 776 | 21 | `1e6b9e46b6d6` | 1 |
| `studies/data-lifecycle/evidence/github-pilot-r1/source/tidytuesday-main.sha` | evidence | 41 | — | `b14fae146509` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/standards/OpenLineage-2.0.2.json` | evidence | 9155 | 304 | `69f68bee00b9` |  |
| `studies/data-lifecycle/evidence/github-pilot-r1/standards/odcs-json-schema-v3.2.0.json` | schemas | 110505 | 3648 | `edb41f33ec46` |  |
| `studies/data-lifecycle/evidence/preservation-r1/acceptance.json` | evidence | 4725 | 111 | `fc675c27b7b6` | 1 |
| `studies/data-lifecycle/evidence/preservation-r1/ndsa-2.1-assessment.json` | evidence | 2731 | 70 | `e4f7a267b54c` | 1 |
| `studies/data-lifecycle/evidence/temporal-evolution-r1/.gitignore` | evidence | 35 | — | `dfd8eee2ddb2` |  |
| `studies/data-lifecycle/evidence/temporal-evolution-r1/activation-decision.json` | evidence | 710 | 20 | `f846bcf58c1d` | 1 |
| `studies/data-lifecycle/evidence/temporal-evolution-r1/bounded-replay-conformance.json` | evidence | 957 | 31 | `14240ef7a1d3` | 1 |
| `studies/data-lifecycle/evidence/temporal-evolution-r1/manifest.json` | evidence | 998 | 30 | `c8fd17a72583` | 1 |
| `studies/data-lifecycle/evidence/temporal-evolution-r1/reference-identity-report.json` | evidence | 1924 | 51 | `fb83f13c8362` | 1 |
| `studies/data-lifecycle/evidence/temporal-evolution-r1/revision-ledger.json` | evidence | 4555 | 167 | `bf9a11858d1c` | 1 |
| `studies/data-lifecycle/evidence/temporal-evolution-r1/schema-evolution-conformance.json` | schemas | 3384 | 98 | `569ed12edfe6` | 1 |
| `studies/data-lifecycle/evidence/temporal-evolution-r1/source/external-temporal-reference-profile.json` | evidence | 3269 | 80 | `404439891ebf` | 1 |
| `studies/data-lifecycle/tests/test_data_lifecycle_semantics.py` | tests | 3104 | 70 | `9e98577a5332` |  |
| `studies/data-lifecycle/tests/test_data_preservation_evidence.py` | tests | 4133 | 109 | `16f74bbd555d` |  |
| `studies/data-lifecycle/tests/test_data_product_consumption_feedback.py` | tests | 2755 | 71 | `d38902f7e8af` |  |
| `studies/data-lifecycle/tests/test_data_product_federation.py` | tests | 2763 | 72 | `2898b1eef951` |  |
| `studies/data-lifecycle/tests/test_data_product_governance.py` | tests | 2638 | 69 | `7d961e606120` |  |
| `studies/data-lifecycle/tests/test_data_temporal_evolution.py` | tests | 2309 | 60 | `e48458499ca8` |  |
| `studies/experimental-episodes/episode-store/README.md` | research | 11483 | 192 | `4dc0a5854387` |  |
| `studies/experimental-episodes/episode-store/alembic.ini` | research | 592 | 38 | `b5fda014c638` |  |
| `studies/experimental-episodes/episode-store/migrations/env.py` | research | 1932 | 66 | `6dcb845e3632` |  |
| `studies/experimental-episodes/episode-store/migrations/versions/0001_episode_projection.py` | research | 4514 | 123 | `0f6ff83f2a29` |  |
| `studies/experimental-episodes/episode-store/mise.toml` | research | 194 | 13 | `e500993752ce` |  |
| `studies/experimental-episodes/episode-store/pyproject.toml` | research | 1165 | 47 | `567ada9bd017` |  |
| `studies/experimental-episodes/episode-store/sql/runtime_r5c_export.sql` | schemas | 1435 | 50 | `bfbfd38b9628` |  |
| `studies/experimental-episodes/episode-store/src/ordivon_experimental_episode_store/__init__.py` | research | 62 | 1 | `093a0774803a` |  |
| `studies/experimental-episodes/episode-store/src/ordivon_experimental_episode_store/aip_readback.py` | research | 7421 | 192 | `8bea7a897dc1` |  |
| `studies/experimental-episodes/episode-store/src/ordivon_experimental_episode_store/analysis.py` | research | 11355 | 312 | `fb0693791988` |  |
| `studies/experimental-episodes/episode-store/src/ordivon_experimental_episode_store/ingest.py` | research | 23490 | 679 | `e8291650c7ed` |  |
| `studies/experimental-episodes/episode-store/src/ordivon_experimental_episode_store/r5c_backfill.py` | research | 5314 | 141 | `4921fd129047` |  |
| `studies/experimental-episodes/episode-store/src/ordivon_experimental_episode_store/r5c_projection.py` | research | 12166 | 333 | `5f2dcee51d7b` |  |
| `studies/experimental-episodes/episode-store/tests/test_aip_readback.py` | tests | 11294 | 312 | `4a8c96bff67a` |  |
| `studies/experimental-episodes/episode-store/tests/test_analysis_contract.py` | tests | 1475 | 44 | `41f837d61be9` |  |
| `studies/experimental-episodes/episode-store/tests/test_committed_ingest_readback.py` | tests | 20710 | 539 | `4d6774023cfa` |  |
| `studies/experimental-episodes/episode-store/tests/test_data_product_contract.py` | tests | 5944 | 142 | `4685a995d63c` |  |
| `studies/experimental-episodes/episode-store/tests/test_ingest_contract.py` | tests | 2487 | 85 | `fdbfcdba4db4` |  |
| `studies/experimental-episodes/episode-store/tests/test_r5c_projection.py` | tests | 10294 | 281 | `f0bf5909efab` |  |
| `studies/experimental-episodes/episode-store/uv.lock` | research | 50617 | — | `0cfba7223674` |  |
| `studies/experimental-episodes/evidence/acceptance/experimental-episode-rw5-bindings.json` | evidence | 614 | 14 | `6648f4450c8d` | 1 |
| `studies/experimental-episodes/evidence/analysis/experimental-system-analysis-r1.json` | evidence | 8947 | 327 | `e5e2c6bd8801` | 1 |
| `studies/experimental-episodes/evidence/corpus-r1/manifest.json` | evidence | 2959 | 61 | `67c917eacd59` | 1 |
| `studies/experimental-episodes/evidence/data-products/experimental-episode-analysis-r1/artifact-index-verification.json` | evidence | 11210 | 384 | `1d63df720b1d` | 1 |
| `studies/experimental-episodes/evidence/data-products/experimental-episode-analysis-r1/openlineage.json` | evidence | 1703 | 47 | `75f8d32f4230` |  |
| `studies/experimental-episodes/evidence/data-products/experimental-episode-analysis-r1/provenance.prov.jsonld` | evidence | 3671 | — | `eea41c2c57d6` |  |
| `studies/experimental-episodes/evidence/data-products/experimental-episode-analysis-r1/receipt.json` | evidence | 1064 | 17 | `de828483c291` | 1 |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/README.md` | research | 4661 | 91 | `0dd2974d1ae5` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/RESULTS.md` | research | 5328 | 93 | `1a4005bac1c1` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/TASK_OUTCOME_RESULTS_20261109.md` | research | 5001 | 92 | `855326b7b146` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/deliver_research.py` | research | 8497 | 210 | `677d4f330485` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/delivery-20261109.json` | research | 1975 | 43 | `14599a550350` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/pilot.py` | research | 13960 | 368 | `75278eb0c39b` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/result-20261108.json` | research | 19596 | 701 | `77a4d39c53b5` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/task-outcomes-20261109.json` | research | 4205 | 115 | `141468ebfdd8` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/task_outcome_pilot.py` | research | 10438 | 290 | `aa0cfb95ef56` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/test_deliver_research.py` | tests | 4983 | 114 | `80ae18ec48b7` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/test_pilot.py` | tests | 5311 | 142 | `12ddf68ec356` |  |
| `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/test_task_outcome_pilot.py` | tests | 5329 | 128 | `cca0146e37c7` |  |
| `tests/catalogs/test_research_tool_and_mechanical_component_contracts.py` | tests | 3292 | 51 | `cb3e017acf53` |  |
| `tests/fixtures/research/publication-carrier-paper3-dogfood-r1.json` | tests | 1518 | 35 | `e9cdaa39957f` | 1 |
| `tools/formal/Proof.als` | other | 90 | — | `c5e65abe1827` |  |
| `tools/formal/Proof.dfy` | other | 70 | — | `ced59b7b0d11` |  |
| `tools/formal/Proof.qnt` | other | 115 | — | `357d9a0aedc5` |  |
| `tools/formal/Proof.rs` | core | 114 | 7 | `6c88573f7334` |  |
| `tools/formal/ProofKani.rs` | core | 95 | 5 | `f8b9023f3164` |  |
| `tools/formal/README.md` | docs | 2111 | 36 | `5e01116b5b45` |  |
| `tools/formal/RecursiveLegoRefinement.lean` | core | 94531 | 2242 | `4810d8017f7b` |  |
| `tools/formal/RecursiveLegoVariationFrame.lean` | core | 25679 | 582 | `70f313b21d7b` |  |
| `tools/formal/mise.toml` | config | 1342 | 18 | `ab3871d84aa7` |  |
| `tools/formal/verify.py` | core | 32316 | 611 | `8acea29b02c2` |  |
| `tools/repo/affected_owners.py` | core | 14865 | 388 | `6b2e4f853c8d` |  |
| `tools/repo/agent_plugin/materialize.py` | core | 9105 | 254 | `d662f543bf67` |  |
| `tools/repo/agent_plugin/source.py` | core | 5075 | 134 | `74f5e1f48644` |  |
| `tools/repo/agent_plugin/test_materialize.py` | tests | 11818 | 297 | `a991a9159d9b` |  |
| `tools/repo/bash-5.3.20.sha256` | other | 1622 | — | `33a97d9e2fa0` |  |
| `tools/repo/check_architecture_docs.py` | core | 125062 | 2524 | `7c6236027c88` |  |
| `tools/repo/check_archived_source_boundary.py` | core | 4975 | 137 | `d2f254199ef2` |  |
| `tools/repo/check_composition_architecture.py` | core | 7737 | 185 | `13839152d970` |  |
| `tools/repo/check_github_governance.py` | core | 16730 | 366 | `504439116574` |  |
| `tools/repo/check_owner_boundaries.py` | core | 11397 | 317 | `8589652b7f09` |  |
| `tools/repo/check_sql_dialects.py` | core | 28775 | 593 | `0d21e9227c4d` |  |
| `tools/repo/check_structure_r2.py` | core | 13286 | 276 | `218da0024f50` |  |
| `tools/repo/check_tracked_secrets.sh` | core | 685 | 17 | `40b0b6b61030` |  |
| `tools/repo/ci_owner_shards.py` | core | 3175 | 84 | `937bb12ce9e5` |  |
| `tools/repo/ci_telemetry.py` | core | 13128 | 373 | `2e925a7e8d29` |  |
| `tools/repo/convergence_plan.py` | core | 47965 | 1025 | `801d9ee9dc2e` |  |
| `tools/repo/convergence_pressure.py` | core | 15234 | 415 | `aa1b4218afd3` |  |
| `tools/repo/dependency_contracts.toml` | config | 10750 | 281 | `5209d46f0ef2` |  |
| `tools/repo/exhaustive_coverage.py` | core | 103295 | 2052 | `64d41ac7214a` |  |
| `tools/repo/install_latest_stable_bash.sh` | core | 2946 | 74 | `c2d2e6241a4b` |  |
| `tools/repo/install_sql_verifiers.sh` | core | 3174 | 67 | `c1c5b14e1e26` |  |
| `tools/repo/install_verified_cargo_deny.py` | core | 5939 | 141 | `759ccfe61265` |  |
| `tools/repo/migration/check-primary-main.sh` | core | 1815 | 43 | `bac891263cba` |  |
| `tools/repo/migration/check-publication-main.sh` | core | 1923 | 48 | `3419912ba4a8` |  |
| `tools/repo/migration/integrate-main.sh` | core | 2717 | 85 | `c678aed15bf3` |  |
| `tools/repo/migration/test-check-publication-main.sh` | core | 4270 | 102 | `93d49abd7c42` |  |
| `tools/repo/migration/test-integrate-main.sh` | core | 3742 | 94 | `0b82bef86378` |  |
| `tools/repo/owners.toml` | config | 2498 | 121 | `8d76f5e96088` |  |
| `tools/repo/planning/lego-plan-r1.json` | config | 17918 | 212 | `44abe315ae22` | 1 |
| `tools/repo/queue_telemetry.py` | core | 14347 | 381 | `79025c66b22a` |  |
| `tools/repo/source_content_facets.py` | core | 24831 | 457 | `6eda217d18ce` |  |
| `tools/repo/source_history_legos.py` | core | 31399 | 715 | `695f05ccbe53` |  |
| `tools/repo/test-check-archived-source-boundary.sh` | core | 3584 | 100 | `e98a142c75ce` |  |
| `tools/repo/test_affected_owners.py` | tests | 26978 | 572 | `cbd2d46fa7a6` |  |
| `tools/repo/test_architecture_docs.py` | tests | 118337 | 2477 | `2c1976c233c3` |  |
| `tools/repo/test_ci_owner_shards.py` | tests | 3386 | 87 | `53dad632d3af` |  |
| `tools/repo/test_composition_architecture.py` | tests | 6449 | 163 | `cc8afe8773e1` |  |
| `tools/repo/test_convergence_plan.py` | tests | 92805 | 1849 | `4b8d72723ac1` |  |
| `tools/repo/test_convergence_pressure.py` | tests | 8643 | 217 | `11f7ebe733c2` |  |
| `tools/repo/test_dependency_update_ownership.py` | tests | 11559 | 229 | `9e480201d42b` |  |
| `tools/repo/test_exhaustive_coverage.py` | tests | 84059 | 1616 | `8358a8491a1f` |  |
| `tools/repo/test_formal_source_contract.py` | tests | 38664 | 781 | `93393c594b3b` |  |
| `tools/repo/test_github_governance.py` | tests | 106949 | 2109 | `9e5595d64fd6` |  |
| `tools/repo/test_install_verified_cargo_deny.py` | tests | 7820 | 182 | `645ad9b6c8cd` |  |
| `tools/repo/test_issue_owner_registration.py` | tests | 14930 | 322 | `be2217cf1799` |  |
| `tools/repo/test_lego_graph_laws.py` | tests | 123215 | 2657 | `c40d5ee9d7df` |  |
| `tools/repo/test_owner_boundaries.py` | tests | 11545 | 248 | `d59c151210c1` |  |
| `tools/repo/test_postgres_owner_migration_issue.py` | tests | 3824 | 82 | `1535e86c62da` |  |
| `tools/repo/test_source_content_facets.py` | tests | 5303 | 87 | `1c4dd6ac9c05` |  |
| `tools/repo/test_source_history_legos.py` | tests | 73441 | 1442 | `4d0fff68777f` |  |
| `tools/repo/test_sql_dialects.py` | tests | 22397 | 485 | `6dc70e3d8849` |  |
| `tools/repo/test_structure_r2.py` | tests | 11778 | 261 | `4e27ff73a2f0` |  |
| `tools/repo/test_tracked_secrets.py` | tests | 3306 | 79 | `e60ad7d8e75a` |  |
| `tools/repo/test_workspace_ready.py` | tests | 31591 | 649 | `55924b4e7032` |  |
| `tools/repo/workspace-ready` | other | 10576 | — | `401e8e1cb383` |  |

## 仅供复核的完全相同内容候选

扫描到 13 组两项以上、128B～1MB 范围内字节一致的文件。相同历史证据可能依赖不同身份/来源；未经当前可观测引用确认，**不自动删除**。

- `LICENSE` / `capabilities/media/LICENSE` / `domains/game/LICENSE` / `services/harness/LICENSE` / `services/runtime/LICENSE`
- `capabilities/media/productions/archive-archipelago-001/render/archive-archipelago-001.png` / `capabilities/media/productions/live-relay-001/source/archive-archipelago-001.png`
- `domains/capital/tools/legacy_replay/lean_wave_b/algorithm/packages.lock.json` / `domains/capital/tools/quickfixn_1_14_1/fix44-projector/packages.lock.json`
- `domains/game/examples/native-composition/assets/kenney-ui-audio/click1.wav` / `domains/game/examples/room-encounter/assets/click1.wav`
- `domains/game/examples/native-composition/assets/kenney-ui-audio/click2.wav` / `domains/game/examples/room-encounter/assets/click2.wav`
- `platform/security/contracts/agent-request-verifier-v1/patches/oauth4webapi@3.8.8.patch` / `platform/security/labs/agent-admission-rs/patches/oauth4webapi@3.8.8.patch`
- `platform/security/contracts/agent-request-verifier-v1/tsconfig.json` / `platform/security/labs/agent-admission-rs/tsconfig.json`
- `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r3-20260918.json` / `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r3-run2-20260918.json`
- `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r5-controlled-run1-20260918.json` / `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r5-controlled-run2-20260918.json`
- `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r7-controlled-run1-20260918.json` / `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r7-controlled-run2-20260918.json`
- `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r8-fresh-service-run1-20260918.json` / `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r8-fresh-service-run2-20260918.json`
- `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r9-window-placement-run1-20260918.json` / `services/harness/evidence/browser-security/cloudflare-provider-security-exp-r9-window-placement-run2-20260918.json`
- `services/harness/evidence/harness-h2-runtime-r2-live-d50f609-20260731.json` / `services/runtime/evidence/harness-h2-runtime-r2-live-d50f609-20260731.json`

## 统计解释及缺口

扫描范围覆盖跟踪文件全体；动态 import、OS/systemd 路径、GitHub Actions 手动调用、外部 URL 和 Git 历史使用者不在本次全量字面计数的完备闭包内。要决定删除，下一步必须从该文件起追踪现有 Owner 实际消费。全部遍历记录不替代代码审查。
