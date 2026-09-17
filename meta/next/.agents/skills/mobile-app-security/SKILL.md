---
name: mobile-app-security
description: Analyze an authorized Android or mobile application from package structure through static, native, runtime, and network evidence. Use for APK/AAB reverse engineering, mobile AppSec review, JADX/apktool analysis, ABI and native-library triage, ADB/emulator setup, Frida-assisted observation, WebView or hybrid-app inspection, and correlation of application-generated network traffic. Prefer evidence-backed reconstruction over assumptions, and keep static findings distinct from runtime-confirmed behavior.
compatibility: Requires access to the target package or source. Individual phases use available Android SDK, JADX/apktool, ELF tooling, emulator/device, instrumentation, proxy, or mobile-security scanners when present; unavailable tools do not invalidate phases that can be completed independently.
license: MIT
---

# Mobile App Security

Use this procedure to understand an authorized mobile application as one connected system rather than as unrelated decompiler output, HTTP requests, and runtime logs.

## Evidence model

Maintain four separate claim classes throughout the analysis:

1. **Package fact** — directly observed from the APK/AAB, manifest, resources, DEX, native libraries, signatures, or hashes.
2. **Static interpretation** — inferred from recovered code or configuration but not yet executed.
3. **Runtime observation** — witnessed on the exact device/emulator/app build under test.
4. **Backend observation** — witnessed at the network/API boundary under the exact session, request, and environment tested.

Do not promote one class into another without evidence. In particular, decompiled code is not proof that a branch executed, HTTP 403 is not proof that a service is dead, and an emulator process exit is not proof that the application behaved correctly.

## 1. Bind the target

Record the package path, SHA-256, file size, package/application ID, version, signing identity if available, analysis date, and the authorized test boundary. Preserve the original sample read-only when practical.

Create a case-local evidence directory rather than modifying the original package during discovery. Keep tool versions and relevant environment identity with each generated result.

## 2. Classify before decompiling deeply

Establish the minimum execution and architecture facts first:

- package type: APK, split APK set, AAB, IPA, or other container;
- min/target SDK and Android version constraints;
- supported ABIs from `lib/<abi>/` and native-library names;
- DEX count and major package namespaces;
- activities, services, receivers, providers, exported components, intent filters, and permissions;
- WebView, Weex, React Native, Flutter, Unity/IL2CPP, Cordova, or other hybrid/runtime indicators;
- embedded certificates, network-security configuration, assets, remote bundle loaders, and update mechanisms.

Use package-native tools such as `aapt`/`apkanalyzer`, `apktool`, `jadx`, `unzip`, `file`, `readelf`, and `strings` when available. Automated scanners such as MobSF are useful triage accelerators, not substitutes for checking the underlying evidence.

### ABI admission check

Before provisioning an emulator, compare the package ABIs with the guest ABI and any available native translation layer. Record the result explicitly:

```text
package ABI set
  ∩ executable guest/native-bridge ABI set
  != empty
```

If that condition is not established, do not interpret installation failure as an application defect. Prefer a compatible ARM guest/device or a separately verified translation environment.

## 3. Reconstruct the static architecture

Build a compact map from Android entry points to business/network/native boundaries:

```text
Android component
  -> Java/Kotlin/DEX path
  -> hybrid/JS bridge when present
  -> JNI/native boundary when present
  -> request/auth/session wrapper
  -> remote service
```

Prioritize code that controls:

- initialization and remote configuration;
- authentication/session state;
- request signing, device identity, risk-control, or anti-abuse parameters;
- certificate and hostname verification;
- root/debug/emulator detection;
- WebView/JavaScript bridges and URL/deep-link handling;
- local storage of credentials or sensitive state;
- exported IPC surfaces;
- dynamic code/native-library loading;
- QR/deep-link/custom-scheme parsing;
- fallback and retry paths.

For every important static hypothesis, retain the class/method/resource path or decompiler location that supports it.

## 4. Inspect native boundaries separately

For each relevant `.so` file, record ABI, ELF type, architecture, exported/imported symbols, JNI names, hardening signals, linked libraries, and notable strings. Map Java/Kotlin native declarations to JNI exports or registration tables where possible.

Escalate to a disassembler/decompiler only for code that materially blocks the investigation. A useful native-analysis progression is:

```text
file/readelf/nm/strings
  -> JNI/library-load map
  -> focused disassembly/decompilation
  -> runtime observation for ambiguous paths
```

Avoid bulk decompilation when a smaller boundary can answer the question.

## 5. Prepare a compatible runtime

Verify rather than assume:

- emulator/device architecture;
- Android/API level;
- boot completion;
- ADB connectivity;
- package installation result;
- package process identity;
- required Google services or vendor dependencies;
- time, locale, network, proxy, and certificate state relevant to the experiment.

Capture the exact install error if installation fails. Distinguish package/ABI incompatibility, signing/version conflicts, SDK policy, missing split packages, storage failure, and runtime crash.

## 6. Observe the application dynamically

Start with low-interference evidence:

- `logcat` around install/start/navigation;
- process and loaded-library inventory;
- activity/task state;
- filesystem changes available within the authorized environment;
- WebView/hybrid runtime logs and remote bundle requests;
- crash traces and native tombstones where applicable.

Use Frida/Objection or equivalent instrumentation only where it answers a specific hypothesis. Favor observation points at narrow boundaries such as method arguments/results, JNI crossings, library loads, request construction, certificate validation, and WebView bridge calls. Record script/source, target build, process, timestamp, and observed output so the result is reproducible.

Dynamic instrumentation changes the runtime. Mark those observations as instrumented and cross-check important conclusions with a less invasive path when feasible.

## 7. Reconstruct network behavior from the application

For an authorized test environment, correlate proxy/packet/application logs with the static request path. Capture enough of the request context to explain behavior without treating credentials as ordinary report text.

For each material endpoint, record:

- scheme/host/path/method;
- application-generated headers and parameter classes;
- session/auth/device/signature dependencies;
- request-body encoding or wrapper layers;
- response status and relevant response shape;
- retry/fallback behavior;
- TLS/pinning behavior as observed.

When a hand-built request differs from the application, compare the exact application-generated request before concluding that the server blocks the client. A bare `403` commonly establishes only that the tested request was rejected.

## 8. Correlate hybrid application layers

For WebView/Weex/other hybrid applications, keep the native shell and remotely loaded frontend as separate versioned subjects. Preserve remote HTML/JS bundle digests and compare later fetches for drift.

Trace bridge edges explicitly:

```text
frontend action
  -> JS/native bridge call
  -> Android/native implementation
  -> request wrapper
  -> backend
```

This avoids attributing remotely changeable frontend behavior to the APK binary itself.

## 9. Security review lenses

Apply only the lenses relevant to the target:

- exported-component and IPC exposure;
- deep-link/custom-scheme validation;
- WebView/JS bridge exposure;
- insecure local storage;
- transport/TLS configuration;
- authentication/session/token handling;
- hardcoded secrets and sensitive logging;
- weak cryptographic use;
- unsafe dynamic code/library loading;
- root/debug/emulator controls and their actual security role;
- native memory-safety/hardening indicators;
- backend authorization assumptions visible from the client.

Automated findings are hypotheses until the affected code path, configuration, or runtime behavior is verified.

## 10. Close with an evidence matrix

For each significant conclusion include:

| Field | Required content |
| --- | --- |
| Claim | Narrow statement being made |
| Evidence class | package / static / runtime / backend |
| Exact subject | package digest, file, process/build, request/session, or remote asset digest |
| Evidence | command/output/path/log/capture reference |
| Confidence | confirmed / supported / unresolved |
| Missing test | what would change or strengthen the conclusion |

Retain unresolved boundaries explicitly. The objective is a reproducible model of the application, not a forced conclusion for every branch.
