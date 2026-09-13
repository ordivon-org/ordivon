# Provider: Flowable

- Upstream: `flowable/flowable-engine`
- Selected release: `8.0.0`
- License: Apache-2.0 for the open-source engine
- Role: executable OMG BPMN / CMMN / DMN provider
- Migration mode: external replaceable provider; no Ordivon fork
- Local standing: **MATERIALIZED / ENGINE-BOOT-SMOKE-PASS / PRODUCTION-HOLD-UNTIL-WORKLOAD**

## Use when

- a business process is prescriptive enough to benefit from BPMN execution;
- adaptive case semantics materially improve a knowledge-work case and CMMN is appropriate;
- a repeatable business decision benefits from explicit DMN modeling/execution.

## Do not use as

- Ordivon's universal workflow engine;
- a replacement for Temporal durable technical orchestration;
- a replacement for n8n integration automation;
- a global Task or business-record database;
- a reason to pre-model open-ended agent investigation as BPMN.

## Local R1 evidence

On 2026-09-14 direct Docker Hub access timed out, so the existing Network v2 `surfpath` path plus `skopeo` was used to materialize the official `flowable-rest:8.0.0` image without changing default host routing.

Observed image:

- local tag: `localhost/ordivon-flowable-rest:8.0.0`;
- manifest digest: `sha256:b67720807e7b091ef46b5e96f191541e1aa67ba0eb284504b5c6e2771d6a5ae2`;
- config/image ID: `49480a54bd98df6e3ba16cd737b539cc41831504c7582f75e341ea357707ea2b`;
- observed size: `341894286` bytes;
- architecture/OS: `amd64/linux`.

A disposable container boot proved:

- Flowable `8.0.0` / Spring Boot `4.0.2` startup;
- `ProcessEngine default created`;
- `DmnEngine default created`;
- `CmmnEngine default created`;
- application context `/flowable-rest` on port `8080`;
- in-container unauthenticated HTTP reached the REST service and was correctly challenged with `401`.

Runtime attempt-local loopback publication did not provide a stable cross-attempt path to the published host port, so this R1 smoke does not claim cross-namespace REST integration acceptance. A real workload should provide the next acceptance boundary.

## Forward rule

Keep the image/materialization available, but do not maintain Flowable as an always-on service until a real BPMN/CMMN/DMN workload justifies it.
