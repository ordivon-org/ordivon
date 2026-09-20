# Wave A / M4 Acceptance — 2026-09-12

**PASS** — Research E2E evidence is now a required input to portfolio construction.

The M4 target portfolio binds:

- GLEIF reference artifact SHA-256 `2d80c275722501b0e83f35bdc19472e9b9e56cb97e2f2931ab69c6d64e16575d`;
- SEC research artifact SHA-256 `bef0a2fd20f3ca73821fc52a383eafc957bcee3ab81d33eb45076c6bd49f8dcd`;
- research fiscal years AAPL=2025, MSFT=2026, NVDA=2026.

Missing or duplicate research evidence fails closed. Weights remain equal-weight validation weights, so M4 tests integration rather than alpha quality.

MLflow run: `735a3175cb6340ee9dd8044231aa8e9a`.
