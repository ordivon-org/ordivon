# Media meta-system scope R1

Date: 2026-09-20
Status: CURRENT SCOPE CORRECTION

## Decision

Media is not the universal owner of representation across Ordivon.

The previous phrase "structured mediation across Ordivon" was too broad because almost every tool, provider, UI, browser, log, metric and Agent result has some observer-facing representation. Treating that fact as Media ownership would make Media a mandatory global layer.

The corrected rule is task activation:

    source/client-native projection
        -> default

    explicit reusable/media-specific mediation need
        -> optional Media contract

    authored/editable production need
        -> Studio

## Media owns when selected

- medium-specific authored expression;
- reusable media assets and productions;
- cross-medium composition/transformation;
- media-specific projection contracts whose semantics matter to the task;
- editable production state;
- media QC/review preparation;
- selected-asset provenance/rights as needed by a production.

## Media does not own by default

- model/tool output formatting;
- Runtime/Host projections;
- dashboards/metrics/log views;
- generic Web UI state;
- browser/provider-native views;
- Game's ordinary presentation;
- repository/document views;
- every API response merely because a human can read it.

These remain with the source, client, provider, or consuming domain unless a concrete task intentionally activates Media.

## OMPC standing

OMPC-v0 remains useful research and an optional conformance/reference contract. It is not a universal inter-subsystem ABI.

## Studio standing

Studio remains a legitimate Media production capability. This scope correction is not a reason to delete real production machinery such as editable sources, timed text, rendering, inspection, QC, provenance and review workflows.

The anti-bloat rule applies above Studio: do not promote research concepts, observer projections or convenience views into a shared Media engine without cross-consumer pressure.
