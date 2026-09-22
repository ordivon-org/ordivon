# Top-three upstream extraction notes

Checked 2026-09-17. These notes record design provenance; the Ordivon Skill remains an independent Agent Skills package and does not import upstream control-plane instructions.

## zhaoxuya520/reverse-skill

Upstream: https://github.com/zhaoxuya520/reverse-skill

Useful procedures extracted:

- APK classification and reverse-analysis flow using JADX/apktool;
- explicit handoff from APK analysis to native `.so` analysis;
- Frida-assisted Java/native runtime observation;
- separate JS/frontend and HTTP-capture/replay paths;
- evidence-first reverse-engineering progression.

Not adopted:

- the repository-wide router as Ordivon routing authority;
- `ACTION REQUIRED`, `NOW`, bootstrap, identity, or mandatory self-routing instructions;
- assumptions that upstream-selected tools or paths are installed locally;
- bulk-vendoring of the upstream package.

Reason: Ordivon already owns Skill discovery/admission and Runtime/tool authority. Third-party procedural content remains advisory.

## mukul975/Anthropic-Cybersecurity-Skills

Upstream: https://github.com/mukul975/Anthropic-Cybersecurity-Skills

This is a community repository rather than the Anthropic organization repository. Relevant mobile-security procedures include Android static analysis with MobSF, mobile penetration-test structure, Android component/intent review, runtime analysis, API/session review, storage review, deep-link review, and certificate/TLS testing.

Useful procedures extracted:

- MobSF as automated static triage while retaining manual verification;
- manifest/exported-component/permission/network-configuration review;
- static + dynamic + backend/API coverage as distinct stages;
- OWASP mobile-testing style coverage of storage, transport, authentication, cryptography, and platform surfaces.

Not adopted:

- the entire large skill corpus;
- domain metadata that is not needed by the Agent Skills portable core;
- any procedure unrelated to the current mobile-security capability.

## NVIDIA/SkillSpector

Upstream: https://github.com/NVIDIA/SkillSpector

SkillSpector is used conceptually and, when installed, operationally as an intake scanner for third-party Agent Skills. It is not treated as a source of mobile reverse-engineering procedure.

Key integration rules:

- consume JSON plus exit code rather than prose output;
- inspect individual issue severities and analysis completeness, not only the aggregate risk score;
- scan single Skill packages when full per-issue evidence is required;
- treat scanner output as evidence feeding local admission/review, never as instruction authority or a semantic trust oracle;
- preserve exact package digest/revision so an approval cannot silently transfer to changed bytes.

An initial Runtime `git clone` path was unavailable because that execution environment could not reach `github.com:443`. The study later acquired source archives through a separate retrieval path and preserved exact research provenance locally: `reverse-skill` commit `7e2097fd90d25c2f976f6eba26d6c00aa88051df`, `Anthropic-Cybersecurity-Skills` commit `54a798831d2266a3ca61ce68a7acb80b81160d57`, and `SkillSpector` commit `c13f70ebf14905912c616a58c9a8cb8112ef94a4`. The archives remain research inputs rather than trusted installed packages.

A deterministic SkillSpector 2.11.2 `--no-llm` scan of upstream `reverse-skill/skills/apk-reverse` returned score 51 / `HIGH` / `DO_NOT_INSTALL`, including prompt-injection, data-exfiltration, and privilege-escalation signals. The Ordivon `mobile-app-security` derivative intentionally retains useful analysis methodology without adopting the upstream package's scripts or control-plane instructions.
