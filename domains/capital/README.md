# Ordivon Capital

Ordivon Capital is Ordivon's **financial-domain composition and control package**. It owns financial semantics that have no more natural external owner; it does not own generic task/workflow composition, transport, physical execution, provider truth, or settlement truth.

## Stable architecture

Capital has seven source-owner domains:

- Markets — public/provider observation, normalization, market sensors;
- Trading — private/provider reality, intent projection, feasibility, effect and execution reconciliation;
- Portfolio — caller-supplied counterfactual transformations;
- Risk — exposure, dependence/tail-risk measurement and registered risk-budget evaluation;
- Research — quantitative inventory, prospective validation, monitoring and evidence persistence;
- Governance — financial policy/admission and financial semantic lowering;
- Accounting — durable local reservation/post/void/idempotency mechanics.

The twelve functional LEGO roles are Observe, Normalize, Validate, Measure, Model, Counterfactual, Decide, Authorize, Reserve, Effect, Reconcile and Account. `Decide` remains a boundary rather than a general autonomous investment-decision engine.

## R2 composition boundary

R2 separates financial meaning from generic composition mechanics:

```text
Financial Circuit Spec
        ↓
Capital financial semantic lowering
        ↓
Ordivon Cognitive Circuit / Authority Obligations
        ↓
owner-native Capital functions
        ↓
provider/local reality
        ↓
Capital reconciliation / accounting
```

`packages/composition` owns generic Cognitive Circuit DAG validation, composition gates, authority/verification obligation binding and interface compatibility/currentness mechanics. Capital retains financial registry standing, financial authority/effect taxonomy, use restrictions, Reserve/Effect/Reconcile/Account invariants, domain acceptance and financial truth boundaries.

## Truth and authority laws

- Provider/account/broker/custody reality is authoritative for external financial facts.
- Workflow success, tests, protocol acknowledgements and local accounting state cannot independently establish an external financial effect.
- A policy allow, Composition gate, Skill, Runtime success or authority-obligation binding does not mint provider/effect authority.
- External-effect ambiguity is reconciled rather than blindly replayed; `UNKNOWN` is no-mutation until authoritative evidence resolves it.
- Owner risk appetite is never inferred. An `UNSET` registered risk budget stays `UNSET`.
- Local accounting is not venue execution, settlement finality, legal ownership or withdrawability.

## Current state

`docs/CURRENT_STATE.md` and `generated/current-state-r2.json` are generated rebuildable projections. Run:

```bash
./scripts/build-current-state-r2
./scripts/build-current-state-r2 --check
```

Machine-readable authority files remain authoritative over projections. Historical progression remains under `docs/history/` and frozen `evidence/` / `fixtures/` surfaces.

## Circuits

Current declarative R2 circuit specifications are under `circuits/`:

- `public-market-observation-r2.json`
- `portfolio-risk-analysis-r2.json`
- `counterfactual-analysis-r2.json`
- `nonlive-effect-qualification-r2.json`

They are financial specifications, not workflow/scheduler state.

## External-owner policy

Prefer standards, mature implementations and provider-native reality. Current narrow owners are tracked by `config/external_owner_census.json`; candidates/challengers do not become canonical merely because they are installed. `config/capital_lego_registry.json` is the machine catalog of current Capital LEGO bindings and standing.

## Verification

Required CI is hermetic and authority-free:

```bash
mise run capital:verify
```

Provider/node-bound qualification remains separate:

```bash
mise run //domains/capital:verify:provider
```

The split does not turn hermetic tests into provider reality and does not widen private/demo/live/production authority.
