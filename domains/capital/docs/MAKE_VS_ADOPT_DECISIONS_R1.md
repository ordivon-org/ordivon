# Market Capital Make-vs-Adopt Decisions R1

| Contract | External candidate | Current winner / standing | Why |
|---|---|---|---|
| Execution-state reconciliation | NautilusTrader | No current external candidate admitted; bounded local baseline retained | rc4 passes the old effect matrix but fails the Python 3.14.7 gate; stable v1.231.0 passes Python 3.14.7 but fails the same DENY/risk-effect contract; rc5 remains pre-release and is not locally qualified. |
| Capital reservation resolution | NautilusTrader | Local seam retained | Different contract: Nautilus does not own Ordivon-to-TigerBeetle capital reservation semantics. |
| Descriptive historical ES | Riskfolio-Lib | Local thin composition retained | Current implementation is small NumPy-owned descriptive math; broad optimizer dependency surface adds no demonstrated benefit for this contract. |
| Autonomous portfolio optimizer | PyPortfolioOpt / Riskfolio-Lib | No adoption yet | No active local portfolio-construction contract exists. Freeze the actual requirement before benchmarking. |
| Broad research-data integration | OpenBB | No adoption yet | No active generic research-data platform contract in Market Capital; provider-private reality remains a different authority boundary. |
| Autonomous quant R&D workflow | Qlib / RD-Agent | Rejected by current language gate | Qlib evidence stops at Python 3.12 and RD-Agent testing evidence centers 3.10–3.11; neither qualifies for Python 3.14.7. |

## Rule demonstrated by this batch

The outcome is intentionally mixed. External code wins only where its measured or directly evidenced advantage matches the exact contract. Small local compositions are retained when they already delegate mechanics to mature primitives and an external framework would only increase trusted/dependency surface.

## Language-baseline override

Python 3.14.7 and Rust 1.98.1 are hard baseline requirements as of 2026-09-21.

- Nautilus rc4 executable evidence was collected on Python 3.12.13, so it is historical evidence only and cannot authorize adoption. A current candidate must be requalified on Python 3.14.7; source-build Rust qualification must use Rust 1.98.1.
- Qlib currently declares Python classifiers only through 3.12, so it fails the current language admission gate and is not adopted.
- A project that otherwise wins correctness/performance/maintenance comparisons still loses admission if it cannot run on the current latest stable language baseline.


## Candidate / owner correction

A package being importable is not capability evidence. During R1 the canonical environment contained NautilusTrader 1.231.0, but its v1 API differed materially from the rc4/v2-bound qualification harness. After a thin temporary API adaptation, the FILL, PARTIAL_FILL_SLICES, CANCEL and UNKNOWN scenarios matched the expected capital outcomes, while DENY did not: the engine reached AccountBalanceNegative(balance=-125150.125, currency=USDT) and the observed capital resolution became POST_PENDING_TRANSFER rather than the required VOID_PENDING_TRANSFER.

Therefore 1.231.0 was removed from the canonical dependency group and generic capability census. Historical rc4 tools were moved out of src/ordivon_capital/market into tools/nautilus_rc4. No Nautilus import remains in the Market core source tree.
