# Wave 3 Domain / Service Source Acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: `domains/game`, `domains/capital`, `services/host`.

| Owner | Frozen source | Rewritten source | Import merge | Bundle SHA-256 |
| --- | --- | --- | --- | --- |
| Game | `a4fdaa065f8daee963154c4647a920c6bc9e75a5` | `8a8b0b446226d0ac157768766ef995c1f78eeef3` | `1d2ed01ae6314ecfcceab03c6300a39b54b76dc2` | `e76f442113e9f7154ce2309816ffa5095797d2b0bb0acab864aff1b1ed3780a1` |
| Capital | `918fd86a3ebe69bb0e05835d7e4c656731da0833` | `3e6eee8bfde4f9628bb0125ad4a8d70a34276017` | `2471d0bc12b28cd95691d836ab6ed2737daeb68c` | `b331e281b4ade25e33205fbb71fa4f78f91b2fa7415e9a609c4a76bf6f47b946` |
| Host | `a95a8e112edfbe85582ff8e6fa25bb268038ea48` | `ba7e33b5784e5a1699f27786fad27e5b1d7e9157` | `d0db7f346305442d13931ab4b5e80c4c0ca6ed9e` | `21af43c3d139a2e1ebfe8215f59ba239de943583c716f574ad5d23fbab0db256` |

All three bundles independently reproduced the exact rewritten SHA, commit map and source/subtree tree identity.

## Owner-native verification

- Game: Node 26.9.0 / pnpm 12.4.2; owner test and cold-start passed; deterministic cold-start surface reported 584 passed; Playwright and real browser E2E passed with exact replay comparison and reload recovery.
- Capital: Python 3.14.7; Ruff passed; 201 tests passed. No financial-write production cutover is implied.
- Host: Python 3.14.7; Ruff passed; 18 tests passed and 18 environment-dependent tests skipped on the hermetic surface. PostgreSQL/live-consumer proof remains separate.

Source co-location does not transfer Game, Capital, or Host authority to the repository root.
