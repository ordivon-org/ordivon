# Experience State Spec

Use this shared state vocabulary for product-facing widgets and pages.

## Allowed States

- `loading`
  - The system is actively fetching or computing a result.
  - Use only while a request is in flight.
- `ready`
  - A real result payload was received and can be rendered.
- `empty`
  - The request succeeded and the source of truth returned no rows or no artifact.
- `unavailable`
  - The feature or source is not currently exposed to the product surface.
  - Use when the backend route is not reachable, not mounted, or intentionally not exposed.
- `error`
  - A request failed unexpectedly after the product surface attempted to load a real result.

## Rules

- Never collapse `error` into `empty`.
- Never collapse `error` into `loading`.
- Never collapse `error` into `null`.
- `empty` is only valid after a successful response with no data.
- `unavailable` is preferred when the backend or product surface is not presently available.
- Use explicit user-facing copy that states which source could not be reached.

## Short Examples

- Recommendations route returned `200` with `[]` -> `empty`
- Reports route returned `500` -> `error`
- History page has no dedicated API yet -> `unavailable`
- Analyze request pending -> `loading`
- Audit events returned successfully -> `ready`
