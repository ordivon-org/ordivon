# Step 3 Capability Prep - 2026-04-18

## Goal

Prepare Step 3: turn capability modules from useful facades into stable product contracts.

## Why Step 3 Comes Next

After Step 2, ownership of the major truth modules is clearer.

That means capability modules can now be normalized without still fighting large truth-location uncertainty.

## Recommended Step 3 Tasks

1. Define input/output contracts for the top capabilities:
   - analyze
   - recommendations
   - reviews
   - reports
   - dashboard
   - validation

2. Remove placeholder response fields where possible.

3. Normalize response shapes:
   - stable ids
   - timestamps
   - lifecycle fields
   - governance fields
   - metadata blocks

4. Decide where capability contracts should live:
   - `capabilities/contracts/*`
   - or `apps/api/app/schemas/*` plus thin adapters

5. Add capability-level tests that assert contract shape rather than only import success.

## Main Risks

- capability modules becoming another ad-hoc translation layer
- route schemas and capability outputs drifting apart
- business objects leaking directly into API responses without a contract layer

## Completion Signal For Step 3

Step 3 is complete when:

- top capabilities have stable request/response structures
- UI/API callers no longer depend on incidental field naming
- capability tests protect contract shape over time
