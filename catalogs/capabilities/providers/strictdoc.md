# Provider: StrictDoc

- Upstream: StrictDoc
- Installed version: `0.29.0`
- Role: text/Git-native requirements and traceability workbench with ReqIF interoperability
- Migration mode: external replaceable tool; native SDoc remains tool-owned
- Local standing: **AVAILABLE / REQIF-SMOKE-PASS**

## Boundary

StrictDoc is not a standards authority, enterprise ontology, universal requirement schema or source of legal/professional obligations.

Use it only when a task benefits from explicit requirements/references and traceability. The true authority remains the external law, contract, standard, platform, professional body, customer or other source.

Use OMG ReqIF 1.2 for cross-tool requirements interchange when needed.

## Local R1 evidence

Pinned installation:

```text
strictdoc 0.29.0
```

A disposable local project exported one demo requirement to:

- HTML;
- JSON;
- ReqIF via the provider-native `reqif-sdoc` export.

The stable demo UID `DEMO-EXT-001` was observed in all three output families, including `output/reqif/output.reqif`.

The demo statement was explicitly a smoke fixture and is not an Ordivon policy or standard.

## Forward rule

Use StrictDoc/ReqIF only for workloads that need explicit traceability. For security-control automation, prefer domain-native standards such as NIST OSCAL when applicable. Do not copy licensed standards text into SDoc merely for convenience.
