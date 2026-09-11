# Operations E2E v2 Architecture — R1

## 1. Design direction

The architecture starts from external standards and mature systems, then admits only the residual Ordivon semantics that those systems cannot safely own.

Reference paradigms:

- Google SRE: monitoring, SLOs, actionable alerting, incident response, toil reduction, simplicity.
- OpenGitOps: declarative desired state, versioned/immutable state, automated retrieval, continuous reconciliation.
- OpenTelemetry: standard traces, metrics, logs, resources, semantic conventions, OTLP.
- NIST SP 800-61 Rev. 3: incident response integrated with cybersecurity risk management.
- CIS Controls: recovery and operational safeguards should prove recovery capability, not merely backup command success.

## 2. Thin-waist architecture

```text
owner desired state
        |
        v
Git versioned declarations
        |
        +--> Ansible ---------> host configuration
        +--> OpenTofu --------> external/cloud infrastructure
        |
        v
systemd / Podman / provider-native controllers
        |
        +--> short local lifecycle
        |
        +--> Temporal --------> durable retries/timers/cancellation/recovery
                 |
                 v
          Ordivon Runtime ----> exact Job/Attempt execution truth
                 |
                 v
      owner semantic verifier
```

Observability is orthogonal:

```text
service facts / owner facts
    | metrics        | logs             | traces/events
    v                v                  v
Prometheus        journald -> Vector   OpenTelemetry
    |                |                  |
    |                v                  |
    |               Loki <--------------+
    |                                    
    +-------------------+----------------+
                        v
                     Grafana

external reachability / black-box contracts -> Gatus
```

## 3. Truth ownership

### External tools may own

- process status and restart behavior;
- generic host facts;
- metric/log/trace transport and storage;
- generic backup storage and retention;
- desired-state application;
- cloud resource state;
- policy evaluation;
- vulnerability scanning;
- generic dependency update proposals.

### Operations v2 may own

- mapping an owner requirement to the selected upstream mechanism;
- evidence-binding rules where ordinary telemetry is insufficient;
- SLO/alert declarations for shared operational infrastructure;
- migration/disposition records for legacy operational scaffolding.

### Operations v2 MUST NOT own

- Runtime Job/Attempt semantic meaning;
- Host continuity semantics;
- Workstation node-specific semantic recovery policy;
- Network path/provider meaning;
- Finance market/capital correctness;
- Research claim/scientific correctness;
- any domain's final success verdict.

## 4. Health model

There is no universal `Doctor` verdict.

Generic facts come from upstream observability and inventory systems. A specific operation requests only the facts it needs and applies an owner-scoped verifier:

```text
facts + freshness + exact source/config identity
                    |
                    v
         verify(<owner-operation>)
                    |
             bounded verdict
```

Examples:

- `systemd active` can prove a process is running; it cannot prove the Research service is semantically correct.
- `pgBackRest restore completed` can prove physical database recovery; it cannot prove all Research lineage invariants survived.
- `Gatus HTTP 401` can prove the tested edge/auth wall is reachable; it cannot prove an authenticated connector reached the origin.

## 5. Orchestration rule

Use the smallest mature owner for each lifecycle:

- systemd: long-lived local processes, dependencies, restart, timers;
- Ansible: host desired state and repeatable configuration;
- OpenTofu: external/cloud desired state;
- Temporal: durable multi-stage workflows, retries, timers, signals, cancellation, recovery;
- Runtime: exact physical execution and terminal evidence.

Operations v2 does not introduce another scheduler.

## 6. Current scale decision

Kubernetes, Argo CD, Flux, Helm, Vault, Backstage, Mimir/Thanos, Chaos Mesh and similar systems are deliberately deferred. They are mature, but current single-workstation/WSL scale does not justify their control-plane cost. Revisit only when concrete multi-node, multi-tenant, multi-operator, or fleet requirements appear.
