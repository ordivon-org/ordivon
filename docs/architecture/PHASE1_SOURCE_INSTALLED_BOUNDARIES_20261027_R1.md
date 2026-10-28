# Phase 1: exact source versus installed evidence (2026-10-27)

This source-only, read-only observation supplement belongs alongside the existing exhaustive source-classification projection. It is NOT another authority, registry, LEGO definition, physical rename, authorization or deployment decision.

## Windows Runtime

The running Windows service OrdivonRuntimeR6Candidate (SCM PID 7240 at observation) declares a release directory named by exact source commit 5b8c17c16c3374be607e598bb76bcf9851c3b674. That commit is a real local Git commit object. The release directory contains ordivon-deployment-manifest.json, whose commit claim equals its directory name. Six of six listed executable files were individually hashed on native Windows; every observed disk SHA-256 matched the release manifest. The Runtime broker's declared SCM executable is likewise a matched file from this release.

**Qualification:** observed SCM image declaration + release-manifest consistency + on-disk binary digest. This is NOT a reproducible-build proof, a loaded process-memory measurement or a consumer semantic/effect acceptance. The Gateway, PostgreSQL 18 and Sunshine Windows services are separate named observations.

## Linux process and source boundaries

Runtime PID 221 maps to /usr/local/libexec/ordivon/ordivon-runtime, observed executable SHA-256 6e5d2f0f605fac0dc60a082a1cec101dca5a998975c6abace1aa71e2395c95db. The Runner executable SHA-256 is 4ec04ea1400797aa3f0b9ab1afde277f9cfd0c51a844390009ee39135fed17a6.

The file /var/lib/ordivon/deployed-head claims Git commit a432136e8a134039f1f0de1e836f5e2886070b02, which exists as a local Git object. The exact link from this claim to the running Runtime binary has NOT been independently established.

Host, Skills, two Gateway and three Temporal worker systemd units have native process witnesses. Both Gateway processes use the same Python **interpreter** digest; that says nothing about equivalence of loaded Gateway source, configuration or their consumers.

## Agent-friendly naming without moving bytes

Alias keys (e.g. execution.transactional.windows-release, interfaces.capability-routing.linux-process) are non-authoritative display names. The source identity is an exact Git commit + path + object mode/OID; the installed identity is node + service + observed file digest. Unknown relation, ambiguous alias, time-incompatible observation and unobserved consumer must remain UNKNOWN, never coerced to proof or permission.

Source file: evidence/PHASE1_SOURCE_INSTALLED_BOUNDARIES_20261027_R1.json. References to native Runtime observation Jobs are embedded there. No service config, secrets, SCM or production Git files were modified by collecting the evidence.
