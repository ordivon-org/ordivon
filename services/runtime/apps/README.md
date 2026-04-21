# Apps

`apps/` is the concrete implementation root for the Experience Layer.

Allowed:

- web UI
- API routes and request adapters
- worker bootstrap and scheduling entrypoints
- auth and transport concerns

Not allowed:

- core domain rules
- risk policy truth
- prompt bodies
- hidden workflow orchestration spread across route handlers
