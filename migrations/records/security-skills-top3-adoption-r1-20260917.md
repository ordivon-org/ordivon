# Security Skills Top-3 Adoption R1

Date: 2026-09-17

## Decision

This adoption round is intentionally limited to the three highest-star security-Skill candidates selected in the discovery pass:

1. `zhaoxuya520/reverse-skill` — reverse/mobile execution methodology source.
2. `mukul975/Anthropic-Cybersecurity-Skills` — broad cybersecurity procedure corpus; only the mobile/AppSec subset is mined here.
3. `NVIDIA/SkillSpector` — third-party Skill supply-chain scanner and intake evidence producer.

No fourth repository is admitted into this round.

## Boundary

The three upstreams serve different roles and are not installed as equivalent Skill packs.

| Upstream | Adopted role | Local form |
| --- | --- | --- |
| reverse-skill | APK/native/JS/network reverse-engineering workflow lessons | procedure extraction into `mobile-app-security` |
| Anthropic-Cybersecurity-Skills | mobile static/dynamic/AppSec coverage and MobSF-style triage lessons | procedure extraction into `mobile-app-security` |
| NVIDIA/SkillSpector | scanner for prompt/package/supply-chain risk before Skill admission | `skill-supply-chain-audit` procedure plus optional Harness-side evidence adapter |

The canonical portable content remains normal Agent Skills. Ordivon does not create a new security-Skill package format or let an upstream router become a second Ordivon control plane.

## Why reverse-skill is not bulk-vendored

The upstream APK procedure contains useful operational knowledge, but its repository also carries a master router, bootstrap assumptions, identity/journal conventions, and imperative self-routing/control language. Those overlap with Ordivon's existing Agent Skills discovery, Harness/Runtime authority, and provider/tool routing.

The useful method is therefore extracted while upstream control-plane semantics are rejected. This also provides a concrete dogfood case for the current local scanner categories such as self-routing, control-plane directives, and cross-Skill routing.

## Why the large cybersecurity pack is narrowed

The community `Anthropic-Cybersecurity-Skills` repository contains hundreds of procedures across many security domains. Installing the whole corpus would add unrelated offensive, incident-response, cloud, identity, and network procedures to the default Skill inventory without a demonstrated consumer.

R1 therefore takes only the methodological content needed for authorized mobile application analysis:

- Android package/manifest/static triage;
- MobSF-style automated static scanning with manual verification;
- dynamic analysis and instrumentation;
- component/intent/deep-link/WebView review;
- local storage, TLS/transport, authentication/session, and mobile API review;
- separation of static findings from runtime/backend confirmation.

## Why SkillSpector is not a trust oracle

SkillSpector has a natural role as a specialized scanner, not as the semantic owner of Skill trust. Its upstream integration surface exposes exit codes and machine-readable reports, including issue-level findings and analysis-completeness information.

Ordivon preserves these distinctions:

```text
SkillSpector evidence
  -> local review/admission input
  != TrustState
  != instruction authority
  != Runtime/tool authorization
```

A zero process exit under default upstream policy is not sufficient evidence for every local gate because SAFE and CAUTION can share that exit code, and aggregate summaries must not erase more severe individual findings or incomplete coverage. The Harness adapter therefore normalizes evidence rather than assigning trust.

## Local provenance and acquisition boundary

An initial isolated Runtime `git clone --depth=1` attempt failed on 2026-09-17 because that execution path could not connect to `github.com:443`. The study later acquired GitHub source archives through a separate retrieval path and preserved them under `/tmp/ordivon-security-skills-top3-20260917/`. This is an acquisition-path distinction, not an upstream repository failure.

The frozen local research inputs are:

| Upstream | Upstream commit recorded by archive | Local archive SHA-256 |
| --- | --- | --- |
| `zhaoxuya520/reverse-skill` | `7e2097fd90d25c2f976f6eba26d6c00aa88051df` | `6b4e525885ae3e38caa5b8fd8870186e37d088775fb65c1ac8a33731c8551bb3` |
| `mukul975/Anthropic-Cybersecurity-Skills` | `54a798831d2266a3ca61ce68a7acb80b81160d57` | `bfc6963f68d68968655c5276026dbe75f4d1354795679b2b00344852201a27e3` |
| `NVIDIA/SkillSpector` | `c13f70ebf14905912c616a58c9a8cb8112ef94a4` | `2b182a79e30a2acc81d77b9eb84cedf1b231265466f241aa37cabe554e3a40b4` |

These archives are research provenance, not automatically trusted installed Skills. The local adopted files remain independent Ordivon-authored derivatives. A representative deterministic SkillSpector 2.11.2 scan of upstream `reverse-skill/skills/apk-reverse` returned score 51, severity `HIGH`, recommendation `DO_NOT_INSTALL`, with seven active findings; this supports procedure extraction rather than wholesale installation.

## New portable Skills

### `mobile-app-security`

One cohesive evidence-first mobile analysis procedure covering:

```text
bind sample
  -> classify APK/AAB + ABI/runtime
  -> static architecture
  -> native/JNI boundary
  -> compatible emulator/device
  -> runtime observation
  -> application-generated network behavior
  -> hybrid frontend/bridge correlation
  -> evidence matrix
```

The ABI preflight is deliberate: it prevents an x86/x86_64 emulator from being treated as a valid runtime for an ARM-only APK unless a verified native translation layer is present.

### `skill-supply-chain-audit`

One intake procedure covering exact package identity, local deterministic checks, optional SkillSpector JSON evidence, issue/completeness interpretation, and the choice between reference-only, procedure extraction, exact vendoring, or tool adaptation.

## First dogfood target

`/root/projects/xby-analysis` is the first consumer. Existing evidence already exercises several important branches:

- APK package/static reconstruction;
- ARM-only `arm64-v8a` + `armeabi-v7a` native libraries;
- successful Android 9/API 28 x86_64 emulator boot and ADB connectivity;
- installation rejection with `INSTALL_FAILED_NO_MATCHING_ABIS`;
- Weex/hybrid frontend and request-wrapper reconstruction;
- protocol/fallback dynamic validation without yet claiming full APK runtime behavior.

The new Skill should classify that state as a runtime ABI admission failure, not an application crash or server failure.

## Acceptance criteria

R1 is acceptable when:

1. both new Skill packages satisfy the local Agent Skills parser/catalog;
2. local scanner evidence is preserved rather than bypassed;
3. SkillSpector integration, when present, is supplemental and fail-explicit on unavailable/incomplete/error states;
4. the xby dogfood produces the expected ARM-vs-x86 runtime diagnosis from existing evidence;
5. no upstream router, bootstrap, or trust semantics becomes an Ordivon authority.
