# INVENTORY — real Git tree and source census

Revision: ef17d6879d12faa61fff3bb762b0d500d73c9113
Source paths: 5002; read bytes: 123,199,041. Mechanical parser: 1460 Python AST, 1315 JSON, 50 TOML, 0 parse errors. This does NOT prove 5002 files are semantically correct. The versioned input is Git; the one-time audit source manifest INVENTORY_FILES.tsv has sha256 424a029a9df32a48425e03715350b7e49ba7abbb98264f5010ad011129a130fe.

## Existing Owner trees and native verify

| Natural Owner | Tracked source files | Dominant source types | Existing verify task |
|---|---:|---|---|
| authority-catalog (catalogs/authorities/) | 376 | json:365, python:6, toml:2 | authority-catalog:verify |
| capability-catalog (catalogs/capabilities/) | 77 | markdown:58, python:12, json:6 | capability-catalog:verify |
| composition (packages/composition/) | 86 | python:32, json:22, .cfg:13 | composition:verify |
| control-plugin (extensions/ordivon-control-plane/) | 2 | json:2 | control-plugin:verify |
| runtime (services/runtime/) | 452 | rust:126, markdown:121, python:74 | runtime:verify |
| host (services/host/) | 117 | python:90, markdown:8, json:5 | host:verify |
| harness (services/harness/) | 731 | python:367, json:171, markdown:140 | harness:verify |
| gateway (services/gateway/) | 107 | python:62, json:13, .cfg:9 | gateway:verify |
| skills (extensions/chatgpt-skills-mcp/) | 45 | python:28, json:7, markdown:4 | skills:verify |
| security (platform/security/) | 162 | python:51, json:25, markdown:21 | security:verify |
| workstation (platform/workstation/) | 265 | python:76, markdown:34, yaml:33 | workstation:ci |
| network (platform/network/) | 236 | python:53, shell:38, json:34 | network:ci |
| artifact (capabilities/artifact/) | 425 | python:195, json:174, markdown:30 | artifact:verify |
| distribution (capabilities/distribution/) | 30 | json:19, shell:6, markdown:2 | distribution:verify |
| media (capabilities/media/) | 553 | json:160, markdown:133, python:126 | media:verify |
| preservation (capabilities/preservation/) | 46 | json:21, .xml:13, markdown:6 | preservation:verify |
| game (domains/game/) | 387 | .uid:89, gdscript:86, .tscn:36 | game:verify |
| capital (domains/capital/) | 399 | python:185, json:89, other:71 | capital:verify |
| data (packages/data/) | 19 | python:9, markdown:6, .lean:3 | data:verify |
| web (apps/web/) | 35 | ts:22, json:6, shell:2 | web:verify |
| chaoxing-autosign (apps/chaoxing-autosign/) | 11 | python:10, markdown:1 | chaoxing:verify |
| repo/source regions | 441 | markdown:197, json:119, python:70 | repo:ci |

## Web Owner: file-by-file mapping (35 of 35)

| Relative apps/web path | Lines | SHA256 prefix | Role/decision |
|---|---:|---|---|
| .gitignore | 3 | 2931a03de250 | Package / native verify entry / lockfile: KEEP |
| README.md | 185 | 5d93bbec1675 | Owner capability contract; KEEP |
| agent-native-e2e.sh | 86 | 8c3b42023e84 | Package / native verify entry / lockfile: KEEP |
| browser-e2e.sh | 22 | c0fe871d431b | Package / native verify entry / lockfile: KEEP |
| evidence/AGENT-AUTHORITY-BROWSER-E2E-R1.json | 87 | 20ebe7644bd0 | Historical bounded E2E receipt: KEEP as historical, not installed |
| evidence/AGENT-NATIVE-WEBSITE-E2E-R1.json | 116 | bfaf260aaef8 | Historical bounded E2E receipt: KEEP as historical, not installed |
| evidence/HUMAN-RAIL-BROWSER-E2E-R1.json | 41 | a5dc472290b2 | Historical bounded E2E receipt: KEEP as historical, not installed |
| mise.toml | 13 | 89c5588c73e3 | Package / native verify entry / lockfile: KEEP |
| package.json | 35 | 45f989aa5030 | Package / native verify entry / lockfile: KEEP |
| planning/lego-plan-r1.json | 384 | 25aca4d78a15 | Consumed by root architecture validator: KEEP |
| pnpm-lock.yaml | 1116 | e20ec41fe970 | Package / native verify entry / lockfile: KEEP |
| pnpm-workspace.yaml | 3 | 44b627aa5890 | Package / native verify entry / lockfile: KEEP |
| src/agent-authority.ts | 121 | ab14563c34ca | Security admission adapter: HOLD F03 (synchronous child) |
| src/app.ts | 722 | ec49b263eefc | Existing source code: KEEP, inspect real seam |
| src/browser-request-boundary.ts | 109 | 18216c0bf790 | Existing source code: KEEP, inspect real seam |
| src/config.ts | 57 | dc9db2f35759 | Config OS path/env admission: FIX F01/F02 |
| src/errors.ts | 14 | 724b38881fb6 | Existing source code: KEEP, inspect real seam |
| src/identity-digests.ts | 32 | 8712568bd769 | Existing source code: KEEP, inspect real seam |
| src/model.ts | 170 | 0393b429bf84 | Existing source code: KEEP, inspect real seam |
| src/security-agent-verifier.ts | 69 | 424ce860e538 | Existing source code: KEEP, inspect real seam |
| src/server.ts | 21 | e0a802ade317 | Existing source code: KEEP, inspect real seam |
| src/store-agent-grants.ts | 153 | bcf106c5623c | Existing source code: KEEP, inspect real seam |
| src/store-row-projections.ts | 188 | bf167852bf66 | Existing source code: KEEP, inspect real seam |
| src/store-schema.ts | 154 | d4e4e9573a1d | Existing source code: KEEP, inspect real seam |
| src/store-sessions.ts | 175 | 5bc0d3795a3c | Existing source code: KEEP, inspect real seam |
| src/store.ts | 811 | 5f11322625b5 | Existing source code: KEEP, inspect real seam |
| src/webauthn.ts | 464 | 47dbee43bbc4 | Existing source code: KEEP, inspect real seam |
| test/agent-authority.test.ts | 338 | 423393396fa2 | Existing native test/E2E consumer: KEEP unchanged |
| test/agent-native-e2e.ts | 535 | 68df01d8eb83 | Existing native test/E2E consumer: KEEP unchanged |
| test/app.test.ts | 282 | c4c4cbb9b92b | Existing native test/E2E consumer: KEEP unchanged |
| test/browser-e2e.ts | 499 | cc0a27568875 | Existing native test/E2E consumer: KEEP unchanged |
| test/store-rows.test.ts | 69 | eef2ec08037f | Existing native test/E2E consumer: KEEP unchanged |
| test/store-schema.test.ts | 54 | eb0826f23d57 | Existing native test/E2E consumer: KEEP unchanged |
| test/verification-entry.test.ts | 58 | 645ac661c425 | Existing native test/E2E consumer: KEEP unchanged |
| tsconfig.json | 18 | 08ad4932f540 | Package / native verify entry / lockfile: KEEP |

## Real boundary relationships

server.ts -> app.ts -> browser-request-boundary.ts, WebAuthn service and WebStore; WebStore -> schema, sessions, grants and row projections. The Agent verification wrapper calls the declared Security source contract; no Web copy of Rego policy was observed. apps/web/planning/lego-plan-r1.json is consumed by tools/repo/check_architecture_docs.py line 227; keep it. tests/evidence/locks have different roles and must not be removed because source hashes match.

## Observed duplicate-byte groups

23 groups, 65 paths in the 5002 baseline, mostly deliberate toolchain pins, license copies, historical fixtures and independent media assets. Do not infer duplicate responsibilities from byte identity. Root docs current Owner listing says 20 but actual owners.toml names 21; that root programme is concurrently handled in PRs #2006/#2010/#2013.
