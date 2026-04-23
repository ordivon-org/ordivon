# Finance Pack Phase 2 Ownership Map

## Purpose

This map records the current intended ownership split while AegisOS continues
moving from a finance-seeded MVP to a generic system body with a finance pack.

## Finance-Pack-Owned

- analyze defaults and supported symbol or timeframe options
- analyze-surface labels and finance workflow copy
- finance-specific policy overlays and tool references
- finance market context inputs carried into workflow execution
- finance semantic wording that would otherwise leak into generic shell surfaces

## Core-Owned

- generic page roles and workspace sovereignty
- recommendation, review, trace, and health object shells
- governance action boundaries and approval semantics
- runtime resolution contracts
- scheduler, monitoring, and delivery infrastructure

## Keep-Out Rules

- generic web surfaces must not inline finance symbol or timeframe defaults
- API v1 routes must not regain ownership through compatibility service facades
- finance defaults may enter generic UI only through `packs/finance/*` helpers
- finance-specific behavior should be added by extending the pack, not by patching
  generic shell components
