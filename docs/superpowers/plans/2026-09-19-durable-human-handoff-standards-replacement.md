# Durable Human Handoff Standards Replacement — R1

This plan is the implementation companion to planning/human-handoff-lego-r1.json.

## Goal

Replace worker-held human waiting with provider-native browser-session persistence plus Temporal durable waiting. Retain only thin protocol adapters, exact effect/evidence fences, loopback human UI transport, Runtime reconciliation, and the existing OCI canary/promotion transaction.

## Sequence

1. Resolve the current Browserless stable image to an exact OCI digest and calculate pull/storage cost.
2. Materialize the candidate without changing production; run the existing paired Browser Security canary.
3. Prove provider-native session persistence/reconnect on the candidate. Do not add a local reconnect emulator.
4. Promote only through browserless_image_promotion.py after all existing security gates pass.
5. TDD the provider handoff so HUMAN_REQUIRED returns immediately after a durable session coordinate is committed.
6. Replace separate externally orchestrated human waiting with Temporal durable wait + exact handoff-bound Signal/Update.
7. Delete wait_for_human_provider_admission() and mode-specific lifecycle branching only after live acceptance.

## Non-goals

- Do not extract browser cookies or credentials.
- Do not reinterpret CAS as OAuth/OIDC.
- Do not modify Runtime Registry by hand.
- Do not add a new Ordivon session protocol when Browserless can own it.
- Do not weaken SEND ambiguity/effect fencing.
- Do not promote an unqualified OCI tag; production uses exact digests only.

## Verification gates

- exact Browserless version/digest and local image identity;
- storage headroom before pull;
- paired canary control/candidate receipt;
- reconnect/session persistence witness;
- focused TDD;
- Temporal workflow replay/restart tests;
- full Harness regression;
- production image-promotion receipt + Security reseal + fresh pool witness.
