# Module Card

- Module: Experience | Review Detail Surface
- Layer: Experience
- Role: Add a truthful review-focused detail surface on top of existing review-facing widgets so users can inspect review fact, execution refs, outcome signal, and feedback packet signal without leaving the current product shell.
- Current Value:
  - `PendingReviews` already shows a compact review-facing card with trace refs, outcome signal, knowledge hint count, and trace detail access.
  - `TraceDetailPanel` already exposes textual trace detail from the trace API.
  - Review write paths now produce real execution refs, outcome backfill, and persisted feedback packet ids.
- Remaining Gap:
  - There is still no review-focused detail surface that groups review fact, execution refs, outcome, and feedback packet in one place.
  - Users must infer the review chain from multiple small sections or raw API responses.
  - Missing relations are handled locally, but there is no dedicated review detail contract yet.
- Immediate Action:
  1. Add a review detail read contract and API endpoint.
  2. Add a small `ReviewDetailPanel` on the existing pending-reviews surface.
  3. Show only real fields:
     - review fact
     - review execution refs
     - latest outcome signal
     - feedback packet signal
  4. Keep honest missing states and trust-tier wording.
- Required Test Pack:
  - `pnpm --dir apps/web exec tsc --noEmit`
  - `python -m compileall ...`
  - unit:
    - review detail panel render smoke
    - honest missing copy assertions on review detail surface
  - integration:
    - `/api/v1/reviews/{review_id}` returns real review detail fields
    - pending review surface includes review detail panel hookup
  - failure-path:
    - missing execution refs stay missing
    - missing feedback packet stays not prepared yet
    - missing outcome stays unavailable
  - invariants:
    - review detail does not present outcome as closed loop completion
    - feedback packet stays derived, not truth or system learning
  - state/data:
    - detail surface fields must come from persisted review / audit / outcome / packet objects
- Done Criteria:
  - At least one review-facing surface can expand into a review-focused detail view.
  - The detail view groups review fact, execution refs, outcome, and feedback packet truthfully.
  - Missing relations remain honest.
  - Tests prove the detail contract and surface are real.
- Next Unlock:
  - `State | Trace Relation Hardening`
  - `Knowledge | Retrieval / Recurring Issue Aggregation`
  - `Infrastructure | Health / Monitoring`
- Not Doing:
  - Do not build a full reviews page.
  - Do not add a new graph/timeline visualization.
  - Do not invent review lifecycle semantics beyond existing truth.
  - Do not rewrite trace semantics.
