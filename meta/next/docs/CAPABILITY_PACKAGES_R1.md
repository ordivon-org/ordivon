# Common Capability Packages R1

Date: 2026-09-13

This document is a working coverage map for frequently used real-world problem classes. It is **not** a fixed Ordivon topology, mandatory stack, universal taxonomy, or prescribed execution order.

A Capability Package is a reusable collection of mature knowledge, standards, methods, skills, tools, providers, execution patterns, validators, evidence requirements, and local lessons that is useful for a class of real problems. The active working set is selected per task.

## Operating rule

For every package:

1. prefer mature external disciplines, standards, tools, Skills and providers;
2. keep existing Ordivon implementation only when it still owns a real residual capability or local integration boundary;
3. do not copy mature provider implementation into `ordivon-next`;
4. prove package usefulness with a real workload, not architecture-completion tests;
5. add capabilities only after a real task exposes a gap;
6. preserve negative knowledge: why a tempting design/tool is not used, and what evidence would justify reopening it.

## Coverage summary

| Package | Current treatment | Local standing | Next proof |
| --- | --- | --- | --- |
| Research | mature methods + Skills + Research v2 providers | usable now; Research v2 source still dirty | current paper: experiment -> analysis -> figures -> manuscript -> peer review |
| Engineering | ISO/software-engineering methods + Codex + existing toolchain | usable now; no new package repo required | complete one real software change from requirement through verified acceptance |
| Security | NIST/OWASP/OpenSSF + Security v2 + security Skills | mature local provider set | run one repository through threat/code/dependency/supply-chain evidence and bounded standing |
| Artifact | native standards + Artifact v2 + `artifact-work` | mature local provider; accepted source authority | execute a fresh native-target-verified artifact task |
| Preservation | OAIS/PAIMAS/PAIS + E-ARK + mature preservation providers | usable standard-native composition; historical R4-R7 are evidence only | use E-ARK SIP/Commons-IP now; activate Enduro only when recurring durable ingest orchestration is proven |
| Media | editorial/media disciplines + native production tools + Artifact/Distribution | needs re-profile; do not migrate old Media ownership wholesale | produce one real media work from source research through accessible deliverable |
| Game | game-development disciplines + Godot/Blender + Engineering/Artifact | useful existing project, needs package re-profile | produce and falsify one real playable Veilwild candidate |
| Data & Analytics | FAIR/data-management/statistics + Python/DuckDB/etc. | usable composition; no new package repo required | take a real dataset from ingest through quality/analysis/visual evidence |
| Distribution | provider APIs/standards + Distribution v2 | mature read/control boundary; writes remain authority-gated | prove one exact publish/read-back path when explicit effect authority exists |
| Operations | mature ops stack + Operations v2 + Runtime | mature composition; minor local workspace residue only | durable execute -> observe -> failure/recovery proof on one real workflow |
| Network | IETF/native networking + Network v2 | mature local WSL/network package | solve one real reachability/throughput/path problem with falsification evidence |
| Business Operations | ERPNext + native business/accounting semantics | accepted local mature owner for current workload | use the first real company/customer/accounting event without inventing an Ordivon business schema |

---

## 1. Research

### Problem coverage

- research question and scope;
- prior art / literature review;
- hypothesis and claim formation;
- study / experimental design;
- data acquisition and research-data management;
- statistical / causal / computational analysis;
- reproducibility and workflow execution;
- scientific visualization;
- interpretation and claim discipline;
- scientific writing;
- peer review / adversarial critique;
- publication artifacts and provenance.

### Mature anchors

- scientific method and domain research methods;
- FAIR principles for findable, accessible, interoperable and reusable digital research assets;
- domain reporting standards where applicable;
- Git/content digests for source identity;
- Snakemake for scientific DAGs;
- DVC or equivalent when data version/dependency management is actually needed;
- MLflow or equivalent for experiment/run tracking when needed;
- Inspect AI or domain-native evaluation systems when model/agent evaluation is the research object.

### Current local working set

- `literature-review`;
- `experimental-design`;
- `statistical-analysis`;
- `scientific-visualization`;
- `scientific-writing`;
- `peer-review`;
- Python / uv / Git / DuckDB;
- Research v2 external-first knowledge and provider mappings;
- Runtime for exact local execution where needed;
- Artifact for publication figures/documents/packages.

### Current gap

Do not repair Research v2 merely for architectural cleanliness. Its working tree currently has unresolved changes. Continue real research from the current project authority and migrate only stable knowledge/decisions as tasks expose them.

### First acceptance workload

Use the current paper as the acceptance case. The package passes R1 only if it can support a real chain from the current experiment state through analysis, figure generation, manuscript update and independent review evidence.

---

## 2. Engineering

### Problem coverage

- stakeholder need / requirement;
- architecture and design;
- implementation;
- build and dependency management;
- testing and verification;
- integration;
- release/deployment;
- operation and observability;
- maintenance/evolution;
- retirement when relevant.

### Mature anchors

- ISO/IEC/IEEE 12207:2026 software life-cycle processes;
- ISO/IEC/IEEE 15288:2023 for broader system life-cycle concerns when the Entity of Interest is a system, not only software;
- ordinary software architecture, testing, CI/CD, configuration management and SRE practices.

### Current local working set

- Codex as coding/semantic execution harness;
- `acquire-codebase-knowledge` for explicit repository onboarding/mapping;
- Git / GitHub CLI;
- Python / Node / uv / package managers;
- Docker / Podman;
- Playwright;
- Security Skills and Security v2;
- Runtime where exact execution evidence matters;
- Temporal for durable long-running process where justified;
- n8n for integration-edge automation;
- Ansible / OpenTofu for desired-state realization;
- Artifact and Distribution for release artifacts/effects.

### Current gap

No dedicated Engineering v2 repository is required. Add a package-specific skill only if repeated real tasks show Codex + existing methods/tools lack reusable procedural knowledge.

### First acceptance workload

Take one real repository change from explicit requirement to implementation, tests, security checks, integration evidence and user-visible acceptance. Do not count `tests pass` alone as system validation.

---

## 3. Security

### Problem coverage

- governance and risk;
- asset/exposure identification;
- threat modeling;
- identity, access and secrets;
- secure design/code review;
- dependency and supply-chain risk;
- SBOM/provenance/policy;
- infrastructure/configuration security;
- runtime detection;
- vulnerability management;
- incident response/recovery;
- security verification evidence.

### Mature anchors

- NIST Cybersecurity Framework 2.0 outcome structure;
- OWASP guidance and ASVS for applicable application-security verification;
- OpenSSF guidance and Scorecard for OSS supply-chain risk signals;
- SLSA/in-toto/Sigstore and SBOM ecosystems where release trust is required.

### Current local working set

- `security-best-practices`;
- `security-threat-model`;
- `security-review`;
- Security v2 providers including Gitleaks, Semgrep, OSV-Scanner, Trivy, Syft, OPA/Rego and OpenSSF Scorecard;
- Cosign and existing artifact/release tooling.

### First acceptance workload

Choose a real software repository and produce bounded evidence for threat model, source/dependency findings, supply-chain posture and policy result. Keep provider-native evidence formats rather than normalizing them into a private universal finding model.

---

## 4. Artifact

### Problem coverage

- choose artifact family and native representation;
- author/create/transform;
- structural/conformance validation;
- semantic/object-contract validation;
- native target/consumer validation;
- visual/accessibility checks where relevant;
- metadata/rights where relevant;
- packaging/provenance/trust;
- exact delivery/read-back evidence when required.

### Mature anchors

Use each family's native standard rather than a universal Artifact AST: OOXML/ODF/PDF, W3C web/accessibility standards, PNG/image standards, Parquet/Arrow, IETF media formats, OGC geospatial standards, glTF/ISO 12113, OCI, SLSA/in-toto/Sigstore and others as applicable.

### Current local working set

- `artifact-work` Agent Skill;
- Artifact v2 at its accepted forward source authority;
- Typst, qpdf, FFmpeg, ImageMagick, Blender, DuckDB, GDAL/OGR, Syft, Trivy, Skopeo, Cosign and family-specific frozen validators/providers;
- PowerPoint/OpenXML target path where presentation requirements demand it.

### First acceptance workload

Run a fresh artifact request through native creation, independent validation and target-consumer evidence. A generated file alone is not PASS.

---

## 5. Media

### Problem coverage

- communication goal and audience;
- source research and fact grounding;
- editorial/narrative/script;
- asset acquisition and rights;
- graphics/image/audio/video/animation production;
- editing/composition;
- accessibility;
- encoding/mastering;
- artifact production;
- publication/distribution;
- audience/analytics feedback when useful.

### Mature anchors

- established editorial and production practice;
- native image/audio/video standards and professional toolchains;
- W3C WCAG 2.2 for applicable web accessibility;
- platform/provider publishing rules and rights/licensing regimes.

### Current local working set

- FFmpeg / ImageMagick / Blender / Godot where appropriate;
- Artifact for format/target validation;
- Distribution for publication effects;
- Research for source grounding;
- existing `ordivon-media` contains useful historical knowledge but its broad "structured mediation" ownership is not automatically forward architecture.

### Current gap

Re-profile Media around actual creation/publishing problems. Do not preserve a universal mediation ontology merely because it exists historically.

### First acceptance workload

Produce one real public-facing media object with source grounding, rights/asset record, accessible artifact, target encoding and publication-ready package.

---

## 6. Game

### Problem coverage

- product/player intent;
- game/system/mechanics design;
- narrative/world/level design;
- UX/accessibility;
- engine/runtime engineering;
- gameplay/AI/physics/network where applicable;
- art/model/rig/animation/material/lighting;
- audio;
- build/performance/QA;
- playtesting;
- packaging/distribution;
- telemetry/live operations where justified.

### Mature anchors

No single universal game-development standard is treated as the owner. Before product commitment, use a non-linear discovery/prototype/playtest loop: Design Council Double Diamond is a useful divergence/convergence skeleton; ISO 9241-210/11 and Games User Research practice ground applicable Human/player evidence; mature studio R&D practices are precedents rather than standards. After product commitment, use mature requirements/lifecycle/quality disciplines plus engine/platform requirements and domain-native tools. Reuse Engineering, Security, Artifact, Media, Network and Distribution rather than recreating them inside Game.

### Current local working set

- Godot;
- Blender;
- FFmpeg/ImageMagick;
- Codex;
- current `ordivon-game` / Veilwild evidence and game-specific knowledge;
- shared Engineering / Artifact / Security / Distribution capabilities.

### Current gap

The existing Game repository contains substantial historical architecture and evidence. Re-profile it as game-specific knowledge, content and validated compositions rather than a container that owns all supporting disciplines.

### First acceptance workload

The active first-formal-product work is pre-commitment. Broad R0 genre/reference expansion is saturated for the current decision. Forward search operates on mechanism graphs: decompose mature references and historical prototypes into mechanics/rules/goals/couplings, compose candidate graphs, then build the cheapest playable needed to test uncertain interactions. Human evidence updates node/edge/composition standing. Genre is a downstream market label, not the design primitive. Historical Veilwild/Station Zero playables remain evidence/apparatus, not automatic product candidates.

---

## 7. Data & Analytics

### Problem coverage

- acquisition/import;
- schema and metadata;
- cleaning/transformation;
- quality checks;
- storage/query;
- descriptive/inferential analysis;
- modeling where applicable;
- visualization/reporting;
- provenance/lineage;
- reproducibility and reuse.

### Mature anchors

- FAIR principles where research/reuse matters;
- domain-native schemas and data standards;
- Parquet/Arrow and mature database/query ecosystems where appropriate;
- established statistics/data-science methods rather than an Ordivon analytics theory.

### Current local working set

- Python;
- DuckDB / SQLite;
- GDAL/OGR for geospatial data;
- statistical-analysis and scientific-visualization Skills;
- Research workflows and Artifact dataset profiles.

### Current gap

Do not create `ordivon-data-v2` unless repeated ownership problems appear. At current scale this is a composition of mature data systems and task-specific contracts.

### First acceptance workload

Use a real research/project dataset: bind source identity, validate schema/quality, perform one analysis, reproduce it from declared inputs, and emit a validated figure/table/report artifact.

---

## 8. Distribution

### Problem coverage

- destination/provider selection;
- exact artifact/payload identity;
- account/identity/credential boundary;
- authorization for consequential effects;
- provider API/upload/publish;
- idempotency/retry/reconciliation;
- provider acceptance/read-back;
- rollout/withdrawal when applicable.

### Mature anchors

- provider-native APIs and platform rules;
- OAuth/OIDC and provider identity/authorization mechanisms where applicable;
- OCI Distribution for OCI/content distribution use cases;
- mature workflow/transport providers rather than custom transfer engines;
- ISO 20252:2026 + ICC/ESOMAR 2025 for market/customer research where research rigor is useful;
- ICC Advertising and Marketing Communications Code 2024 for responsible marketing communications;
- Google Search Essentials for Google organic-search eligibility/best practices when that channel is active;
- provider-native acquisition/attribution semantics such as GA4 traffic-source dimensions when analytics is deployed;
- ISO 20671-1:2021 only when brand evaluation has a real decision purpose;
- IAB Tech Lab / MRC standards only when paid-media/ad-tech scale makes those controls materially useful.

### Marketing/channel boundary

Distribution may carry commercial content, but it does not own a generic marketing ontology or channel-ranking algorithm.

For the current pre-customer stage, channel choice is a task-local experiment:

```text
hypothesized buyer + offer
  -> bounded channel test
  -> qualified conversation
  -> proposal
  -> paid delivery
  -> acceptance / repeat / referral
```

Use research standards for research, marketing-communications codes for outbound/content, provider rules for provider behavior, and real customer outcomes for channel selection. ISO 20252 explicitly excludes direct marketing, so research and outreach must not be conflated.

### Current local working set

- Distribution v2;
- Runtime immutable/evidence-bound execution paths;
- n8n for integration edges;
- OCI/Skopeo/ORAS-family tooling where applicable;
- provider-native clients/APIs.

### Durable lessons

- exact external effect must bind exact intent/account/payload occurrence;
- reusable credentials do not equal authorization for one consequential effect;
- local execution/upload success does not equal provider acceptance;
- ambiguous external outcomes must not be blindly retried without idempotency or authoritative absence evidence.

### First acceptance workload

When explicit write authority exists, publish one bounded artifact to a real provider and prove provider-side identity/read-back. Until then, read-only/dry-run evidence remains the correct boundary.

---

## 9. Operations

### Problem coverage

- desired state/configuration;
- service lifecycle;
- durable process execution;
- automation/integration;
- deployment;
- telemetry/observability;
- backup/restore;
- incident/recovery mechanics;
- capacity/resource facts where actually needed.

### Mature anchors

- systemd / Podman/Quadlet for service lifecycle;
- Ansible and Nix/DSC-facing mechanisms for host desired state where appropriate;
- OpenTofu for external infrastructure desired state;
- Temporal for durable workflows;
- n8n for integration automation;
- OpenTelemetry plus Prometheus/logging systems for observability.

### Current local working set

Operations v2 already follows this external-first boundary. Runtime remains physical execution/evidence provider rather than domain-semantic authority.

### Current gap

No new operations framework. The current source has only minor local residue; address it only if it affects actual operation or reproducibility.

### First acceptance workload

Take one useful long-running workflow through start, observation, induced/reproduced failure where safe, recovery/resume, and final domain-specific verification.

---

## 10. Network

### Problem coverage

- reachability;
- DNS/resolution;
- routing/path selection;
- proxy/tunnel/VPN composition;
- IPv4/IPv6 and Windows/WSL divergence;
- MTU/HTTP/path failure diagnosis;
- throughput/reliability measurement;
- isolation and egress selection;
- falsification evidence.

### Mature anchors

Use IETF/native protocol standards and mature OS/network implementations. Treat DNS/proxy/tunnel/probe/telemetry mechanisms as replaceable providers, not a custom network stack.

### Current local working set

Network v2 is already a mature package-shaped implementation: classify requirement -> select mature mechanism -> compose isolated realization -> falsify known failure modes -> emit evidence.

### Durable lessons

Do not infer workload success from one successful ping/curl/small request. Preserve tests for path identity, throughput, Windows/WSL divergence, DNS, IPv4/IPv6, MTU, HTTP behavior, resume behavior and ambient-state dependency when relevant.

### First acceptance workload

The next real package/download/repository/network failure becomes the acceptance case. Resolve it using the minimum mature mechanism and retain evidence showing why the selected path satisfies the workload requirement.

---

## 11. Business Operations

### Problem coverage

- company/master data;
- customer and CRM records;
- opportunity and sales pipeline;
- sales/invoice lifecycle;
- customer contract/SOW lifecycle and commercial commitments;
- accounting documents and general-ledger effects;
- operating budgets, variance and basic project economics;
- business projects;
- quality records;
- customer support/helpdesk state only when real support load requires durable shared records;
- inventory/procurement/payments/tax/payroll only when a real company workload actually requires them;
- API/integration edges to other mature business providers.

### Mature anchors

Use mature provider-native business semantics instead of creating an Ordivon business ontology.

Provider ownership is responsibility-specific rather than permanently assigned to one suite:

- ERPNext/Frappe remains the accepted local owner for transactional selling/accounting/project/quality facts already proven;
- current Frappe documentation schedules ERPNext's built-in CRM workspace for removal in version 17, so new CRM pipeline work should evaluate Frappe CRM rather than accumulating compatibility debt in the old workspace;
- ERPNext Buying is the native candidate for supplier/RFQ/PO/purchase-invoice facts when procurement becomes real;
- WorldCC / CCM Institute Contract Management Standard is the professional lifecycle reference when contract-management structure is useful; legal effect and drafting risk remain with the actual agreement, applicable law and qualified counsel;
- ERPNext Budget/Budget Variance and accounting/project reports are the native first owner for approved budgets and plan-vs-actual evidence; they are not a complete FP&A or cash-forecast methodology;
- Frappe Helpdesk is the candidate support system when real ticket/SLA/customer-portal/knowledge-base coordination appears; ISO/IEC 20000-1 applies only when a genuine service-management system is in scope;
- ISO 10002/10004 provide customer complaint/satisfaction process guidance when actual customer evidence exists;
- ISO 30405:2023 provides recruitment guidance when a real hire exists;
- Frappe HR can own employee/payroll operational records when useful, while statutory payroll/tax/social-insurance correctness stays with applicable law and qualified/local providers;
- ISO 20400:2017 applies when sustainable-procurement concerns are material, while ISO 37500 applies to material outsourcing;
- statutory, tax, banking, payment, payroll and jurisdiction-specific behavior stays in the applicable regulatory/professional/provider system.

### Current local working set

- ERPNext `16.34.2` / Frappe as the currently proven transactional ERP/accounting owner;
- MariaDB `11.8` and Redis `8.6` as ERPNext-owned storage/runtime dependencies;
- rootless Podman/Quadlet + user systemd as service-lifecycle owner;
- Frappe native document/API lifecycle for existing ERP business records;
- no newly activated CRM, HR/payroll, procurement, helpdesk, CLM or dedicated FP&A service merely to complete the architecture;
- n8n as a bounded integration edge;
- Runtime only for mechanical execution/evidence when operating the local service.

Detailed acceptance evidence and the CRM provider-succession note are in `migrations/records/business-operations-erpnext-r1.md`.

### Authority boundary

Do not use ERPNext as the universal work/task database, and do not preserve a retiring ERPNext CRM workspace by wrapping it in Ordivon abstractions. Host v2 remains the current minimal work/continuity utility; Plane is an optional heavier work-management provider only if a real workload justifies activation. Temporal/MAF/Runtime/domain owners retain their own process/orchestration/execution/semantic truth. Likewise, Market Capital remains a separate read-only market/capital domain rather than being collapsed into ERP accounting.

### Current standing

The current local acceptance workload passed a native chain from Customer/Opportunity/Project/Quality through a submitted CNY 100 Sales Invoice and balanced General Ledger entries, then survived complete Pod stop/start and the later manual-Pod -> Quadlet ownership cutover. A published n8n workflow also reached ERPNext through the existing loopback gateway path and received `pong` from the live Frappe endpoint.

This remains valid historical evidence for that ERPNext v16 slice. It is not evidence of a real customer, and it is not a commitment to use ERPNext's built-in CRM for future pipeline work. Real tax, bank, payment, payroll, inventory, procurement and statutory invoicing workflows also remain unconfigured until triggered.

### First real business workload

Use the first genuine company/customer/accounting event. For a first real sales pipeline, compare the current Frappe CRM provider against the actual founder-led workflow before activation; keep accepted transactional selling/accounting records in ERPNext where native. Let the first real customer agreement exercise the WorldCC-informed contracting boundary plus jurisdiction-specific legal review instead of creating a CLM. Let the first approved spending plan exercise ERPNext Budget/Variance before considering FP&A software. Let the first real employee/payroll obligation decide whether Frappe HR and a payroll provider are needed. Let repeated support load decide whether Frappe Helpdesk is worth activating. Configure only the minimum provider-native records needed, use dedicated least-privilege integration identities for authenticated automation, and verify the resulting provider-native state/effect. Do not add custom Ordivon business semantics unless repeated mature-provider substitution failure is measured.

---

# Shared mature disciplines

These are **not mandatory layers** and are not owned by any package. Load them when the current problem needs them:

- Knowledge Management;
- Decision Science / DSS;
- Operations Research;
- Systems Engineering;
- BPM / Workflow / Adaptive Case Management;
- Verification & Validation / Quality;
- Risk Management;
- Governance;
- Human Factors;
- Scientific Method / Statistics.

Do not reduce these disciplines to LLM prompts when their mature methods materially matter.

# Enabling capability universe

Packages may consume, without owning:

- Agents and harnesses;
- Agent Skills;
- MCP/A2A/API/CLI interfaces;
- deterministic programs;
- solvers;
- databases;
- workflow engines;
- humans and approvals;
- storage/compute/network infrastructure;
- validators and target environments.

# R1 prioritization

No additional software or Skill installation is justified by this census alone. The current local pack is sufficient to begin real work.

Use this order only as a **near-term workload queue**, not an architecture order:

1. Research — current paper is already active and provides the strongest immediate acceptance workload.
2. Engineering — use the next real software change, not a synthetic demo.
3. Game — decompose references/historical playables into mechanism evidence and test the next high-information mechanism composition.
4. Artifact — continue real presentation/document/media work as it arrives.
5. Security — attach to real Engineering/Game/Research release surfaces rather than run disconnected audits.
6. Media — re-profile through the first actual media production request.
7. Data & Analytics — validate through real Research/Game/Market-Capital datasets.
8. Distribution — graduate only when a real publish effect is authorized.
9. Operations — validate through workflows created by the above work.
10. Network — activate on demand when a real path/reachability/throughput issue occurs.
11. Business Operations — ERPNext is accepted locally; use it on the first real company/customer/accounting event and configure only the required native module surface.

The package map is successful if Ordivon-owned implementation stays small while real output throughput and verified outcomes increase.

---

## Preservation

### Problem coverage

- producer/archive submission agreement and exact source selection;
- interoperable SIP construction/validation;
- preservation ingest, format identification and metadata;
- AIP storage, fixity, replication and recovery;
- repository/preservation-program maturity assessment.

### Mature anchors

- ISO 14721:2025 OAIS;
- ISO 20652:2006 PAIMAS;
- ISO 20104:2015 PAIS;
- E-ARK CSIP/SIP 2.2.0;
- PREMIS/METS, PRONOM/Siegfried;
- NDSA Levels of Digital Preservation 2.1;
- DPC RAM v3;
- CoreTrustSeal Requirements 2026–2028.

### Current local working set

- Commons-IP 2.11.3, proven on the exact 86-file frozen corpus;
- Archivematica 1.18 + Storage Service and Artefactual Fixity from the R6/R7 graduated workload;
- owner-domain exact-byte selection/adapters;
- Enduro as a workload-triggered replacement candidate for preservation ingest orchestration.

### Boundary

Do not create an Ordivon preservation maturity scale, package ontology, fixity model, replication model or recovery model. Historical R4-R7 labels are engineering evidence only. E-ARK is the forward submission/interchange profile; external assessment tools own preservation maturity.

### Next proof

The next preservation infrastructure addition must be triggered by a real gap such as independent/off-site failure domain or recurring durable multi-SIP ingest. Do not deploy Enduro/Kubernetes or another repository stack merely to fill an architecture box.
