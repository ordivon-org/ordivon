# M2 Platform / Capability Source Acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: `platform/workstation`, `capabilities/media`, `capabilities/artifact`.

All three preserved bundles independently reproduced the exact rewritten revision, byte-identical commit map, and source/subtree tree identity.

| Owner | Frozen source | Rewritten source | Import merge | Bundle SHA-256 |
| --- | --- | --- | --- | --- |
| Workstation | `1ee414a9fcf40ce69c8fe53235134e3f55a5eee7` | `530de8ad1f950c36a16149e8c541851e90265c82` | `dd8554a7f424b31be26862671cf953f2495b08ee` | `8dde62dbb16695c0230be95a1e5947b831a8e28c441800a82b184491ca6fe00f` |
| Media | `30f6d1228a4270a68cd715ca9a7b17742478958e` | `19aadb146b1bbb19cc6fbcb2ee9394188fc9aa40` | `6f760db03dad6df0da62f72710e58ac3b1b9aab7` | `d7aba6d66c2780dacfe22af66cfcaeadfacb45c3f7b3e82a984f0c40b945bfb2` |
| Artifact | `3762b3f033f1173aa93609c79284980610301d37` | `1bb82fc159fa95d51c62f254ae994538a8e9d979` | `3dc5afa7b3f24b94dfd46cd64dd4d66bc7377ea1` | `c63cf8387f4dda4bb1e4b7dfd6f106811d95ba33a0867bef0e9b957ddca46ed0` |

## Owner-native verification

- Workstation: Python 3.14.7, Ruff passed, 142 Python tests passed; Cloudflare provider 29 TypeScript tests plus Python/provider/policy/operations/Wrangler dry-run passed. A prior transient /tmp ENOSPC was falsified by an unchanged successful rerun.
- Media: Node 26.9.0, pnpm 12.4.2, Python 3.14.7, uv 0.12.16; 155 Python tests, typecheck, Vite build, Ruff, and cold-start passed.
- Artifact: Python 3.14.7 hermetic surface; Ruff passed; `pytest -m "not integration"` reached 100% with exit code 0. External integration remains a separate gate.

M2 demonstrates that one Git repository does not imply one environment, lockfile, runtime state, or release authority.
