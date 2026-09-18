# LEGO Candidate Lens Universe R1

Date: 2026-09-18
Status: ACTIVE RESERVE MAP / NOT ROUTABLE

## Purpose

The Lens Universe is the open discovery surface behind the active LEGO method set.

It records mature disciplines that may become useful analytical lenses, while separating:

- known to exist;
- plausibly relevant;
- type-checkable;
- prospectively useful;
- admitted active lens.

Only the last category is routable by LEGO Lens Router.

The canonical machine-readable reserve lives inside the existing Lens Registry:

knowledge/registries/lego-lens-registry-r1.json -> reservePool

This is not a second registry.

## Architecture

Academic/scientific universe
-> RESERVE POOL
-> Lens Compiler on a real method gap
-> CANDIDATE
-> SHADOW
-> PROSPECTIVE
-> Router admission
-> ACTIVE / MERGE / RETIRE / RESERVE

Router cannot select a reserve entry directly.
Reserve entries cannot carry a SkillRef.
Compiler cannot self-promote a candidate.

## Current reserve families

Strategic interaction:
- game theory;
- mechanism design;
- behavioral economics.

Operations and decision:
- queueing theory;
- operations research / optimization;
- decision analysis;
- forecasting / calibration.

Structure and dynamics:
- network science;
- system identification;
- applied category theory / compositionality.

Computation and formal structure:
- distributed systems;
- formal methods;
- program analysis;
- database theory / provenance.

Information and measurement:
- information theory;
- measurement science / metrology;
- psychometrics.

Human and social systems:
- HCI / human factors;
- cognitive science;
- sociology / institutional analysis.

Natural-system analogues with strict type-checking:
- ecology;
- epidemiology / contagion;
- statistical physics / complexity.

These last categories have especially high metaphor risk. Similar vocabulary is never sufficient.

## Candidate state law

RESERVE_ONLY means:
- worth rediscovering if a matching method gap appears;
- not yet justified for active routing;
- no Skill;
- no Router activation.

RESERVE_SHADOW_TESTED means:
- Lens Compiler completed a bounded shadow/type-check case;
- the candidate may have improved measurement or experiment design;
- evidence is still insufficient for active admission.

Queueing theory currently occupies this state.

## Promotion test

A reserve candidate progresses only when all are true:

1. Router produced NO_LENS_METHOD_GAP, not NO_LENS_SUFFICIENT.
2. A domain-native method does not already own the question adequately.
3. Compiler establishes primitive, assumption, operator, observability and decision-return fit.
4. The candidate produces unique value relative to nearest active lenses.
5. A real prospective case is declared.
6. Router admission concludes ACTIVE rather than MERGE/RETIRE/RESERVE.

## Core principle

The system now safely holds both:

Almost every mature discipline may contain a useful lens.

Almost no concrete problem should use many lenses at once.

The open Reserve Pool handles the first.
MSTS routing enforces the second.

Open Knowledge Universe + Closed Active Working Set + Frozen Minimal Core.

## Non-goals

- no encyclopedic catalog of every academic field;
- no prestige ranking of disciplines;
- no automatic Skill creation;
- no keyword-to-lens activation;
- no Wave N growth metric;
- no assumption that scientific maturity implies relevance to Ordivon;
- no metaphor promotion without operators and measurable return path.

Canonical references:
- docs/LEGO_LENS_ROUTER_R1.md
- docs/LEGO_LENS_COMPILER_R1.md
- knowledge/registries/lego-lens-registry-r1.json
- templates/LEGO_LENS_CARD_R1.md
