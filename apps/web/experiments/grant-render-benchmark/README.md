# Grant table rendering benchmark

Opt-in isolated experiment, not an application or production dependency. The
fixture uses synthetic grant rows with identical fields and immutable array
updates. Four variants: React 19 baseline, explicit React.memo row, React
native compiler configured, and Solid 2 keyed For. Compiler coverage is not inferred from the plugin setting. The opt-in
compiler witness inspects the two actual fixture functions in a separate
unminified build, with a compiler-off negative control. All variants use the same semantic
table and preserve stable row/cell identity on updates.

Run from this directory with the existing Web mise Node/pnpm pin and a local
Chromium executable:

    mise exec -- pnpm install --frozen-lockfile --ignore-scripts
    mise exec -- pnpm typecheck
    mise exec -- pnpm compiler:witness
    ORDIVON_WEB_CHROMIUM_EXECUTABLE=/absolute/path/to/chromium mise exec -- pnpm benchmark

No lifecycle scripts or package Agent skills were approved. The package/lock
are isolated from the production Web package. This is a research candidate,
not an unconditional production gate.

Each variant/load gets five fresh pages, 100-row warmup then clear, five
measured mounts and 250 measured one-row updates. Rotate variant order each
repetition. Verify exact row identity, changed quota/revision and all
untouched rows outside the timed region. Nearest-rank P50/P95; a zero
measurement means below browser timing resolution. Build times are single
observations. gzip bytes use Node gzipSync, not network transfer sizes.
See evidence/20261124-r4.json for the original run and
evidence/20261124-r6-replay.json for the later same-source replay from an
independent workspace (same Agent, not independent reviewer). The second
execution retains source/tree/Job coordinates and does not overwrite the
first evidence. Both runs use identical benchmark input files.

The benchmark measures synchronous data update and DOM commit, not paint,
layout, request latency, virtualized lists, Agent token usage, real owner
events or overall application performance. One machine/run with uncontrolled
host contention is not a statistical claim about all devices. Do not promote
a framework solely from this result. The separate compiler witness only establishes cache generation for GrantRow
and App in this exact pinned fixture; it does not establish application-wide
coverage or theoretical superiority. A production choice needs the same
consumer semantics, lifecycle, accessibility, supply-chain qualification and
agent task/rework measurements. No duplicate production stack.
