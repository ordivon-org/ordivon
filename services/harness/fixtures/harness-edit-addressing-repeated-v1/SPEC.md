# Repeated-target configuration repair

`feature_flags.py` exposes two public functions:

- `alpha_enabled()` must remain `False`.
- `beta_enabled()` must return `True`.

The current defect is that both functions return `False` using identical return lines.
Repair **only** `feature_flags.py`. Preserve the public function names and keep
`alpha_enabled()` false while making `beta_enabled()` true.
