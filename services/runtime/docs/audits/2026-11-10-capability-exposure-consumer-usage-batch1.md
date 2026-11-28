# Capability exposure / consumer / usage audit — batch 1 (2026-11-10)

This is a **dated, non-authoritative observation**, not a new capability registry, deployment receipt, or task-completion authority. Follow current Gateway, Skills, Runtime and Research owners for live truth. The first-batch consumer is the follow-up tool-discovery/latency optimization decision.

## Source cuts and S0: exposed vs usable

- Repository source: Windows audit of `origin/main` at `8ee84f61767eb8f73c0fac3874aee4f040795963`; independent Linux verification at `c7bbeed016be16f4860fec4ba069f3ee0cb11932`. These are not claims that any candidate patch is installed.
- Gateway `0.10.8`, `surfaceEpoch=9`: native MCP SDK `Client(build_server()).list_tools()` returned **38 tools** and verified the exact manifest and `contractDigest=sha256:fcf0bd94a1e4db6e5c72ad0e825c57d9fcff2424d4275074af088982451055fa`.
- The ChatGPT Gateway connection in this audit showed **36 tools**; the absent consumer entries were `capability.resolve` and `topic.state.set`. This is a **client-visible difference**, not proof of a missing deployed service method. A direct unauthenticated request to local `http://127.0.0.1:19003/mcp` returned **403**; do not bypass verified ingress identity to force an installed `tools/list` observation.
- Gateway projected 17 capabilities: four runtime/continuity/artifact routes ready, 13 Research composition routes `readiness_state=unknown`, `available=false`. Research routes are *discovery/composition metadata*, not evidence of a ready scientific provider.
- Project Skill service: **40 discovered, 40 valid, 40 admitted**, **35 model-visible under implicit invocation**. All five omitted names (`method-router`, `causal-intervention`, `compositional-contracts`, `finance-experiment-review`, `ordivon-security-owner`) were individually resolved with `invocationMode=explicit`. No indexing/data-loss fix is justified by 40 vs 35.

## S1: real consumer slice and its limit

Observed: Gateway `capability.search("literature")` found `research.literature.discovery`, with provider readiness correctly `unknown`; Skills resolved `codex-user/paper-lookup` and returned digest-fenced `SKILL.md` bytes; Windows Runtime executed a bounded Crossref API request. The scientific identifier consumer checked required fields instead of using HTTP success or Job exit alone.

- Positive: Crossref `GET https://api.crossref.org/works/10.1038/nature14539`; DOI `10.1038/nature14539`, title `Deep learning`, publication year 2015, author count 3; accepted.
- Windows Runtime Job `job-01a1c4c7-a059-7a60-998f-41d2462370b4`, exact stdout Artifact `attempt-01a1c4c7-a059-7a60-998f-41e48a0c230d.stdout`, digest `sha256:b2c282dba94e87dd04401df63c1590eb28ac7bebc12eeb022e0bfa1a7e5214ac`; verified with `artifact.read`.
- Negative: `10.1038/ordivon-nonexistent-20261110` returned Crossref **404**, classified only as `not_found_in_crossref`, not as global nonexistence. Runtime Job `job-01a1c4ce-5542-7b62-ac08-7a720bdc4ba6`, stdout digest `sha256:a013de587882c12fdc9827f1d4a23ca7916d0b83f29e13c0895ad1504fcb2076`.
- **Not proven:** full installed `Gateway capability.resolve -> provider` execution, Study owner acceptance, any publication/scientific outcome, or ChatGPT client publication of all 38 tools. Skill authority remains advisory; Runtime Job success is physical execution evidence.

## S2: actual Windows Runtime MCP trace, 24-hour window

Read existing JSONL `C:\ProgramData\Ordivon\RuntimeCandidateR6\registry\runtime-trace.jsonl`, selecting `kind=mcp_tool_call_outcome` with `observedUnixMs >= 1794216267722` (2026-11-09 09:24:27Z). **978 observed MCP tool-call outcomes**, 916 recorded success, 62 other outcomes. This is the Windows Runtime call boundary only; it is *not* global fleet usage, token consumption, or semantic task success. `totalMs` includes more than useful compute; percentiles below use sorted observed values.

| Tool | Calls | P50 totalMs | P95 totalMs | Non-success |
|---|---:|---:|---:|---:|
| workspace.exec | 530 | 3,613 | 78,338 | 7 |
| workspace.list | 94 | 751 | 185,764 | 0 |
| workspace.get | 82 | 15,034 | 29,090 | 14 |
| job.observe | 52 | 1,513 | 18,089 | 0 |
| job.list | 51 | 5 | 45 | 0 |
| workspace.read | 51 | 1 | 3 | 34 |
| workspace.close | 46 | 35,163 | 167,432 | 5 |
| runtime.describe | 38 | 363 | 773 | 0 |
| workspace.open | 19 | 22,111 | 56,018 | 2 |

Remaining tools total 15 calls with zero non-success in this window. The top reported error was `workspace.read / WORKSPACE_PATH_DENIED / workspace_executor` (34 calls); **do not assume all 34 are the same physical cause without the corresponding error messages**. This audit independently reproduced an unsupported native Windows no-follow open currently misclassified as a path denial. Other issues: `workspace.get` has 10 `WORKSPACE_NOT_FOUND` and four `TOOL_FAILED` outcomes; transient missing objects are not necessarily bugs.

## Code correction and verification

`services/runtime/crates/ordivon-runtime-core/src/universal/workspace/file_io.rs` now distinguishes `std::io::ErrorKind::Unsupported` as `ToolUnavailable`, including root opening and beneath-root resolution. A true directory ACL/path denial remains `WorkspacePathDenied`. **No unsafe Windows path traversal fallback was introduced.**

- Rust `cargo fmt --all -- --check`: PASS on Linux, and PASS on a current-main Windows clone.
- `cargo test --locked --offline -p ordivon-runtime-core unsupported_secure_open_is_unavailable_not_path_denied --lib`: **1 passed**, 444 filtered out, on Linux.
- Gateway official `packaging/windows/verify_release.py`: **38 exact native SDK tools, name+input/output digest PASS**.
- Gateway focused native tests for surface/research/readiness: **25 passed**.
- Windows `cargo test --lib` attempt: **not PASS**; existing crate test modules assume Unix-only APIs and fail to compile on the Windows target (57 pre-existing portability errors). Linux passed the focused regression.

## Follow-up acceptance boundaries

1. Gateway/connector owner: compare the *authenticated installed* `tools/list`, source SDK list (38) and ChatGPT connection (36), preserving ingress authentication. Correct a demonstrated stale consumer surface at its publisher.
2. Runtime owner: native Windows secure handle-relative/no-follow opening remains **unimplemented**, so `workspace.read/content` cannot yet succeed there. Implement through mature Windows file-handle primitives with a symlink/junction race adversarial consumer before advertising read readiness; the current patch is truthful failure classification, **not a read implementation**.
3. S3/S4 optimization: prioritize measured `workspace.read` failure causes, `workspace.get/close` latency and expensive `workspace.exec` p95. Use existing Runtime trace/report and Gateway OTEL; measure end-to-end consumer success and resource costs before declaring performance gains.
4. Do not create an additional global tool/Skill registry, retry side-effectful calls from protocol errors, or promote `UNKNOWN` to `FALSE`.
