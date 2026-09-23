# Ordivon Capital LEGO Architecture R1 — executable plan

Status: PLANNING / ISOLATED WORKSPACE
Truth role: planning projection, not Capital or provider truth
Source revision: `8a5127a96272fe1d157cd636ac3b73942cb2d469`

## Objective

Turn the already-working Capital domain into explicit registered LEGO circuits without rebuilding a finance framework. Preserve the seven current source owners, provider truth, Runtime physical execution, Host continuity, Network transport ownership, and the current production-write block.

R1 active scope is **W0–W5 + W7**. W6 is intentionally deferred and must not block R1.

## Frozen baseline

- Source owner: `domains/capital`
- Source-owner domains: Markets / Trading / Portfolio / Risk / Research / Governance / Accounting
- Lane: `NON_LIVE`
- Production external financial write: `BLOCK_NOT_GRANTED`
- Portfolio risk budget: `UNSET`
- Private account data admission: `NOT_ADMITTED`
- Gateway need not expose a `capital.*` capability.

## Execution DAG

```text
W0 Truth/Vocabulary
   C00 ─┬─ C01
        └─ C02
              │
W1 Registry   R01 → R02 → R03
                          │
W2 Contracts       T01 T02 T03 T04
                     \  |  |  /
                         T05
                       /     \
W3 Read circuits Q01→Q02→Q03→Q04→Q05
                                      \
W4 Skills                              S01→S02/S03
                       \
W5 Effects             E01→E02→E03→E04→E05→E06→E07
                                              │
                                              └→S04

W7 Verification  V01 + V02 + V03 → V04 → V05

W6_DEFERRED  P01 → P02 → P03
             BLOCKED_BY_AUTHORITY / not part of R1 completion
```

## Waves

| Wave | Goal | Exit gate |
|---|---|---|
| W0 | Freeze current truth and LEGO vocabulary | no contradictory current-state projection |
| W1 | Machine-readable Capital LEGO Registry | every active LEGO registered; stale/candidate owners fail closed |
| W2 | Typed composition contracts | authority/effect/evidence assumptions mechanically composable |
| W3 | Read-only circuit compiler | 3 real read-only circuits dogfooded |
| W4 | Advisory Skill UX | Skills select circuits but own no finance truth/authority |
| W5 | Non-live effect circuit | Decision→Authorize→Reserve→Effect→Observe→Reconcile→Account closes under fault injection |
| W6 deferred | Future external-write requirements | remains unreachable until independent authority changes |
| W7 | Cross-cutting verification | hermetic CI + R1 acceptance |

## Executable modules

### W0 — Freeze current truth and vocabulary before adding machinery.

#### C00 — CapitalTruthFreeze

- **State:** `READY`
- **Owner:** capital
- **Kind:** contract-freeze
- **Responsibility:** Freeze current Capital source owner, seven domain owners, current protocol v2 identities, NON_LIVE lane, BLOCK_NOT_GRANTED production authorization, UNSET owner risk budget, current provider/private-reality admission standing, and the rule that provider reality outranks workflow/engine/local-ledger state.
- **Depends on:** none
- **Files:** `domains/capital/planning/current-truth-r1.json`, `domains/capital/tests/test_current_truth_surfaces.py`
- **Must not own:** new business semantics; live-write authority
- **Authority boundary:** Projection/freeze only; source configs/contracts and external providers remain authoritative.
- **Acceptance:**
  - Machine-readable current truth agrees with canonical configs/contracts and current source-owner taxonomy.
  - Any contradictory present-tense architecture claim fails a repository test.
  - No planning artifact changes production authorization or private-data admission.
- **Next action:** Build exact current-state projection from existing Capital authorities.

#### C01 — CurrentnessHistorySplit

- **State:** `READY_AFTER_C00`
- **Owner:** capital
- **Kind:** documentation-boundary
- **Responsibility:** Separate present-tense current standing from chronological historical progression so agents cannot mistake superseded clock/provider/runtime observations for current truth.
- **Depends on:** `C00`
- **Files:** `domains/capital/docs/CURRENT_STATE.md`, `domains/capital/docs/history/`, `domains/capital/docs/ARCHITECTURE.md`
- **Must not own:** provider currentness; runtime observation truth
- **Authority boundary:** Documentation projection only.
- **Acceptance:**
  - ARCHITECTURE contains one non-contradictory current-state section.
  - Historical observations move behind explicit HISTORY/provenance labels without deleting evidence.
  - Current-state values are mechanically checked against C00 projection.
- **Next action:** Implement only after dependencies pass.

#### C02 — FunctionalLegoFreeze

- **State:** `READY_AFTER_C00`
- **Owner:** capital
- **Kind:** domain-decomposition
- **Responsibility:** Freeze the 12 functional LEGO vocabulary: Observe, Normalize, Validate, Measure, Model, Counterfactual, Decide, Authorize, Reserve, Effect, Reconcile, Account; map each to the seven source-owner domains without replacing native domain names.
- **Depends on:** `C00`
- **Files:** `domains/capital/planning/functional-lego-map-r1.json`
- **Must not own:** new universal finance ontology; renaming source-owner packages
- **Authority boundary:** Analytical/composition projection; seven domains remain source owners.
- **Acceptance:**
  - Every current executable Capital component maps to one or more functional LEGOs.
  - Every LEGO names a canonical source owner and explicit non-responsibilities.
  - No source package is renamed merely to match LEGO vocabulary.
- **Next action:** Implement only after dependencies pass.

### W1 — Create the Capital LEGO Registry as a projection over existing owners.

#### R01 — CapitalLegoRegistrySchema

- **State:** `READY_AFTER_C02`
- **Owner:** capital
- **Kind:** typed-registry-contract
- **Responsibility:** Define a machine-readable registry schema for executable Capital LEGO metadata: identity, source owner, input/output contracts, authority requirements, effect class, replay class, evidence obligations, side effects, risk tier, status, and implementation binding.
- **Depends on:** `C02`
- **Files:** `domains/capital/schema/capital-lego-registry-v1.schema.json`, `domains/capital/contracts/capital-lego-registry-v1.json`
- **Must not own:** runtime scheduling; gateway routing; provider permission truth
- **Authority boundary:** Metadata contract only; implementation and external authorities remain separately owned.
- **Acceptance:**
  - Schema represents every active quantitative/control/adapter/reconciliation component without semantic loss.
  - Authority/effect fields are mandatory for effect-capable entries and explicit NONE for pure entries.
  - Registry schema cannot itself grant authority.
- **Next action:** Implement only after dependencies pass.

#### R02 — RegistryPopulation

- **State:** `READY_AFTER_R01`
- **Owner:** capital
- **Kind:** registry-materialization
- **Responsibility:** Populate the registry from current Markets/Trading/Portfolio/Risk/Research/Governance/Accounting implementations and current contracts/configs.
- **Depends on:** `R01`
- **Files:** `domains/capital/config/capital_lego_registry.json`
- **Must not own:** candidate-tool promotion; implicit live capability
- **Authority boundary:** Registry indexes current owner facts; it does not supersede source/config/contracts.
- **Acceptance:**
  - All active source API components that participate in Capital circuits have registry entries.
  - Retired and candidate-only components are explicitly marked RETIRED or CHALLENGER and cannot appear as active owners.
  - Every entry links exact implementation path and source-owner domain.
- **Next action:** Implement only after dependencies pass.

#### R03 — RegistryVerifier

- **State:** `READY_AFTER_R02`
- **Owner:** capital
- **Kind:** verification
- **Responsibility:** Fail closed on missing implementation paths, undeclared authority/effects, owner mismatches, stale schema identities, or active references to retired compatibility surfaces.
- **Depends on:** `R02`
- **Files:** `domains/capital/scripts/check-capital-lego-registry`, `domains/capital/tests/test_capital_lego_registry.py`
- **Must not own:** business policy
- **Authority boundary:** Static consistency checker only.
- **Acceptance:**
  - Registry verifier runs hermetically in capital:verify.
  - Deleting/renaming a bound implementation without registry update fails.
  - Marking an effectful LEGO as pure/no-effect is caught by explicit fixture tests.
- **Next action:** Implement only after dependencies pass.

### W2 — Add typed composition, authority, effect and evidence contracts plus assume-guarantee checking.

#### T01 — LegoContractEnvelope

- **State:** `READY_AFTER_R03`
- **Owner:** capital
- **Kind:** typed-contract
- **Responsibility:** Define a common composition envelope around domain-native input/output contracts without forcing all financial payloads into one schema.
- **Depends on:** `R03`
- **Files:** `domains/capital/contracts/lego-composition-envelope-v1.json`
- **Must not own:** domain payload schemas; universal event ontology
- **Authority boundary:** Cross-owner composition envelope only.
- **Acceptance:**
  - Envelope carries legoId, contract identities/digests, input provenance, output identity and boundary metadata.
  - Domain-native payload remains opaque/typed by its own contract.
  - Pure transforms can compose without Runtime/Host-specific fields.
- **Next action:** Implement only after dependencies pass.

#### T02 — AuthorityRequirementContract

- **State:** `READY_AFTER_R03`
- **Owner:** capital-governance
- **Kind:** authority-contract
- **Responsibility:** Represent what authority a LEGO consumes: public-read, private-read, simulated-effect, demo/test, live qualification, production-write; bind owner/provider authority references without embedding secrets.
- **Depends on:** `R03`
- **Files:** `domains/capital/contracts/capital-authority-requirement-v1.json`
- **Must not own:** credential bytes; provider IAM grants; Runtime credential storage
- **Authority boundary:** Requirement declaration only; grants remain owner/provider/Runtime CredentialAuthority truth.
- **Acceptance:**
  - Every registry entry has an explicit authority requirement.
  - Public/read-only LEGOs cannot silently compile into write-capable authority.
  - Production-write requirement remains unsatisfied while production-authorization is BLOCK_NOT_GRANTED.
- **Next action:** Implement only after dependencies pass.

#### T03 — EffectClassContract

- **State:** `READY_AFTER_R03`
- **Owner:** capital-governance
- **Kind:** effect-contract
- **Responsibility:** Classify NONE, LOCAL_STATE, SIMULATED_EXCHANGE_ORDER_EFFECT, DEMO_EXTERNAL_WRITE, LIVE_QUALIFICATION_WRITE, PRODUCTION_FINANCIAL_WRITE and define reversibility/reconciliation obligations.
- **Depends on:** `R03`
- **Files:** `domains/capital/contracts/capital-effect-class-v1.json`
- **Must not own:** effect execution; generic Runtime effect framework
- **Authority boundary:** Capital semantic effect classification only; Runtime remains physical executor.
- **Acceptance:**
  - Every effect class states commit point, ambiguity behavior, reconciliation oracle and whether reservation is required.
  - UNKNOWN external outcome can never map directly to successful accounting mutation.
  - Production class cannot be admitted by registry metadata alone.
- **Next action:** Implement only after dependencies pass.

#### T04 — EvidenceObligationContract

- **State:** `READY_AFTER_R03`
- **Owner:** capital-research
- **Kind:** evidence-contract
- **Responsibility:** Define pre/post evidence obligations per LEGO and circuit: provenance/currentness, model standing, policy result, provider receipt, authoritative reality, reconciliation, accounting receipt.
- **Depends on:** `R03`
- **Files:** `domains/capital/contracts/capital-evidence-obligation-v1.json`
- **Must not own:** scientific truth by declaration; provider truth
- **Authority boundary:** Evidence requirement semantics only.
- **Acceptance:**
  - Positive claims name exact evidence obligations and limitations.
  - Model outputs retain inventory/validation standing through composition.
  - Effect circuits require post-effect authoritative reality and reconciliation evidence.
- **Next action:** Implement only after dependencies pass.

#### T05 — AssumeGuaranteeCompositionChecker

- **State:** `READY_AFTER_T01_T04`
- **Owner:** capital
- **Kind:** composition-verifier
- **Responsibility:** Check that adjacent LEGO assumptions are discharged by upstream guarantees, especially authority, currentness, model-use restrictions, effect class and reconciliation obligations.
- **Depends on:** `T01`, `T02`, `T03`, `T04`
- **Files:** `domains/capital/src/ordivon_capital/governance/composition_contract.py`, `domains/capital/tests/test_composition_contract.py`
- **Must not own:** workflow scheduling; decision optimization
- **Authority boundary:** Static/deterministic composition admission; not execution authorization.
- **Acceptance:**
  - Invalid compositions fail before physical execution.
  - A read-only circuit cannot accept an effectful LEGO.
  - A model prohibited for trade sizing cannot satisfy an automatic-sizing assumption.
  - Provider reality remains an external assumption that local accounting cannot discharge.
- **Next action:** Implement only after dependencies pass.

### W3 — Compile and dogfood read-only Capital circuits.

#### Q01 — CapitalCircuitIR

- **State:** `READY_AFTER_T05`
- **Owner:** capital
- **Kind:** circuit-ir
- **Responsibility:** Define a small DAG IR for Capital cognitive circuits: nodes reference registered LEGOs; edges bind typed outputs to inputs; circuit carries goal, frozen context, authority set, evidence obligations and terminal claim type.
- **Depends on:** `T05`
- **Files:** `domains/capital/contracts/capital-circuit-v1.json`
- **Must not own:** agent chain-of-thought; generic workflow engine; Runtime Job lifecycle
- **Authority boundary:** Capital composition plan only; Runtime/Host own execution/continuity.
- **Acceptance:**
  - IR is declarative and bounded to Capital composition.
  - Circuit cannot invent unregistered LEGO implementations.
  - Cycles are rejected for R1 except explicit Observe-after-Effect represented as separate DAG nodes.
- **Next action:** Implement only after dependencies pass.

#### Q02 — ReadOnlyCircuitCompiler

- **State:** `READY_AFTER_Q01`
- **Owner:** capital
- **Kind:** compiler
- **Responsibility:** Compile read-only goals into admitted registered LEGO DAGs using explicit supplied goal/context/authority facts; first supported families are market observation, portfolio risk, and counterfactual analysis.
- **Depends on:** `Q01`
- **Files:** `domains/capital/src/ordivon_capital/circuit/compiler.py`, `domains/capital/tests/test_circuit_compiler.py`
- **Must not own:** autonomous investment objective; risk-tolerance inference; effect selection
- **Authority boundary:** Composition selection only; it does not approve investment actions.
- **Acceptance:**
  - Compiler emits only effectClass NONE/LOCAL_STATE circuits in R1.
  - Missing risk budget remains explicit UNSET rather than inferred.
  - Same normalized goal/context produces deterministic circuit identity.
- **Next action:** Implement only after dependencies pass.

#### Q03 — CircuitExecutorAdapter

- **State:** `READY_AFTER_Q02`
- **Owner:** capital
- **Kind:** execution-adapter
- **Responsibility:** Execute compiled pure/read-only circuit nodes through existing Python/domain entrypoints and Runtime where needed, preserving node receipts and artifacts without creating a Capital scheduler.
- **Depends on:** `Q02`
- **Files:** `domains/capital/src/ordivon_capital/circuit/runner.py`, `domains/capital/tests/test_circuit_runner.py`
- **Must not own:** durable Runtime Job truth; Host continuity; parallel scheduler
- **Authority boundary:** Thin domain runner/adapter; Runtime owns physical execution.
- **Acceptance:**
  - Runner is deterministic for pure local nodes and delegates physical processes to Runtime rather than duplicating process truth.
  - Node failures stop dependent nodes and produce bounded receipts.
  - No external write-capable path exists in W3.
- **Next action:** Implement only after dependencies pass.

#### Q04 — CircuitReceipt

- **State:** `READY_AFTER_Q03`
- **Owner:** capital
- **Kind:** evidence-binding
- **Responsibility:** Materialize circuit-level receipt that binds circuit digest, node receipts, input evidence, claim boundaries and unresolved obligations.
- **Depends on:** `Q03`, `T04`
- **Files:** `domains/capital/contracts/capital-circuit-receipt-v1.json`, `domains/capital/src/ordivon_capital/circuit/receipt.py`
- **Must not own:** provider truth; semantic truth beyond evidence
- **Authority boundary:** Evidence aggregation only.
- **Acceptance:**
  - Receipt never equates successful node execution with financial truth.
  - Unresolved evidence obligations remain explicit.
  - Receipt can be content-addressed and replay-compared.
- **Next action:** Implement only after dependencies pass.

#### Q05 — ReadOnlyDogfoodCircuits

- **State:** `READY_AFTER_Q04`
- **Owner:** capital
- **Kind:** consumer-e2e
- **Responsibility:** Dogfood at least three current circuits: public market observation/quality, portfolio exposure+risk report, and explicit counterfactual+pre-trade evidence completeness.
- **Depends on:** `Q04`
- **Files:** `domains/capital/acceptance/capital-circuit-readonly-r1.json`
- **Must not own:** trade recommendation; external effect
- **Authority boundary:** Read-only acceptance evidence.
- **Acceptance:**
  - Three circuits complete from registered LEGOs only.
  - Outputs match direct current implementations for fixed fixtures/observations.
  - No circuit requires production/private write authority.
- **Next action:** Implement only after dependencies pass.

### W4 — Expose project-scoped advisory Capital Skills over registered circuits.

#### S01 — CapitalSkillBoundary

- **State:** `READY_AFTER_Q05`
- **Owner:** skills+capital
- **Kind:** skill-contract
- **Responsibility:** Define project-scoped Capital Skills as advisory circuit-discovery/invocation guidance, never as financial truth, policy, credential or execution authority.
- **Depends on:** `Q05`
- **Files:** `domains/capital/contracts/capital-skill-boundary-v1.json`, `domains/capital/tests/test_capital_skill_boundary.py`
- **Must not own:** financial truth; write authority; hidden strategy
- **Authority boundary:** Advisory instructions only.
- **Acceptance:**
  - Skills reference registry/circuit contracts rather than hardcoding private implementation knowledge.
  - Skill removal does not remove Capital executable semantics.
  - Explicit skill text states that effect admission remains Governance/provider-owned.
- **Next action:** Implement only after dependencies pass.

#### S02 — CapitalObserveSkill

- **State:** `READY_AFTER_S01`
- **Owner:** skills+capital-markets
- **Kind:** skill
- **Responsibility:** Provide project-scoped guidance for selecting public/private-read observation circuits while preserving explicit admission boundaries.
- **Depends on:** `S01`
- **Files:** `.agents/skills/capital-observe/SKILL.md`
- **Must not own:** credential discovery; provider write
- **Authority boundary:** Advisory selection of registered observation circuits.
- **Acceptance:**
  - Public observation path works without credentials.
  - Private observation refuses when admission/current permission facts are absent.
  - No secret location is embedded in Skill text.
- **Next action:** Implement only after dependencies pass.

#### S03 — CapitalRiskCounterfactualSkill

- **State:** `READY_AFTER_S01`
- **Owner:** skills+capital-risk-portfolio
- **Kind:** skill
- **Responsibility:** Guide exposure/risk/counterfactual circuit selection and preserve the distinction between measurement, scenario projection and recommendation.
- **Depends on:** `S01`
- **Files:** `.agents/skills/capital-risk/SKILL.md`
- **Must not own:** risk appetite inference; scenario ranking
- **Authority boundary:** Advisory analysis composition only.
- **Acceptance:**
  - UNSET risk budget remains visible.
  - Counterfactual outputs are not promoted to recommendations.
  - Model standing/use restrictions are surfaced.
- **Next action:** Implement only after dependencies pass.

#### S04 — CapitalReconcileSkill

- **State:** `READY_AFTER_E05`
- **Owner:** skills+capital-trading-accounting
- **Kind:** skill
- **Responsibility:** Guide exact re-entry into reconciliation/accounting-resolution circuits after an already-existing effect or ambiguous outcome; never initiate an effect.
- **Depends on:** `S01`, `E05`
- **Files:** `.agents/skills/capital-reconcile/SKILL.md`
- **Must not own:** order submission; blind retry
- **Authority boundary:** Advisory recovery/reconciliation guidance only.
- **Acceptance:**
  - Skill requires existing effect identity/provider evidence.
  - UNKNOWN directs to reconciliation/no-mutation rather than resend.
  - Accounting resolution follows authoritative reconciliation standing.
- **Next action:** Implement only after dependencies pass.

### W5 — Compile the already-admitted non-live effect/reconciliation/accounting circuit and destroy it with failure injection.

#### E01 — NonLiveEffectCircuitIR

- **State:** `READY_AFTER_T05`
- **Owner:** capital-trading
- **Kind:** effect-circuit
- **Responsibility:** Extend Capital circuit IR with existing admitted SIMULATED_EXCHANGE_ORDER_EFFECT only, preserving explicit Decision→Authorize→Reserve→Effect→Observe→Reconcile→Account stages.
- **Depends on:** `T05`
- **Files:** `domains/capital/contracts/capital-nonlive-effect-circuit-v1.json`
- **Must not own:** demo/live/production writes; generic effect engine
- **Authority boundary:** Capital non-live semantic plan; Runtime/provider own physical realization.
- **Acceptance:**
  - Only current non-live effect class is admitted.
  - Each effect node requires reservation and reconciliation obligations.
  - Circuit identity binds decision, intent and authority inputs.
- **Next action:** Implement only after dependencies pass.

#### E02 — ReservationCompositionContract

- **State:** `READY_AFTER_E01`
- **Owner:** capital-accounting
- **Kind:** accounting-contract
- **Responsibility:** Bind effect identity to durable reservation/post/void semantics using current SQLite accounting owner and deterministic identity rules.
- **Depends on:** `E01`
- **Files:** `domains/capital/contracts/capital-reservation-v1.json`, `domains/capital/tests/test_reservation_composition.py`
- **Must not own:** settlement truth; venue truth
- **Authority boundary:** Local accounting commitment only.
- **Acceptance:**
  - Reservation is durable and idempotent across restart.
  - Terminal reservation cannot be reopened from stale provider state.
  - UNKNOWN reconciliation preserves pending state.
- **Next action:** Implement only after dependencies pass.

#### E03 — NonLiveEffectAdmissionCompiler

- **State:** `READY_AFTER_E02`
- **Owner:** capital-governance
- **Kind:** admission-compiler
- **Responsibility:** Compile registered non-live circuit authority/evidence/policy facts into an admitted or denied effect proposal using current Governance rules.
- **Depends on:** `E02`
- **Files:** `domains/capital/src/ordivon_capital/governance/nonlive_effect_circuit.py`, `domains/capital/tests/test_effect_admission.py`
- **Must not own:** provider permission; Runtime admission
- **Authority boundary:** Domain semantic admission only; Runtime separately admits physical Job.
- **Acceptance:**
  - ExternalFinancialWriteAllowed remains false.
  - Only SIMULATED_EXCHANGE_ORDER_EFFECT can pass in W5.
  - Missing/ambiguous authority or evidence fails closed.
- **Next action:** Implement only after dependencies pass.

#### E04 — ProviderNeutralSimulatedAdapter

- **State:** `READY_AFTER_E03`
- **Owner:** capital-trading
- **Kind:** provider-adapter
- **Responsibility:** Define the minimal provider-neutral simulated-exchange adapter contract required by the existing non-live effect matrix, leaving Nautilus rc4 as historical challenger evidence rather than canonical owner.
- **Depends on:** `E03`
- **Files:** `domains/capital/src/ordivon_capital/trading/simulated_effect.py`, `domains/capital/tests/test_simulated_effect.py`
- **Must not own:** real venue semantics; OMS framework; production broker adapter
- **Authority boundary:** Bounded simulated provider mechanics.
- **Acceptance:**
  - FILL/PARTIAL_FILL_SLICES/CANCEL/DENY/UNKNOWN_AFTER_SUBMISSION are representable.
  - Adapter returns provider episode evidence, not final accounting truth.
  - Historical Nautilus matrix remains differential evidence only.
- **Next action:** Implement only after dependencies pass.

#### E05 — EffectReconciliationCircuit

- **State:** `READY_AFTER_E04`
- **Owner:** capital-trading+accounting
- **Kind:** reconciliation
- **Responsibility:** Compose provider episode/reality through current FIX lifecycle normalization into NO_MUTATION / VOID_PENDING_TRANSFER / POST_PENDING_TRANSFER accounting resolution.
- **Depends on:** `E04`, `E02`
- **Files:** `domains/capital/src/ordivon_capital/governance/nonlive_effect_circuit.py`, `domains/capital/tests/test_effect_reconciliation_circuit.py`
- **Must not own:** provider repair; blind resend
- **Authority boundary:** Cross-owner reconciliation seam only.
- **Acceptance:**
  - Broad snapshot absence never proves no-effect.
  - Positive execution and proven zero-effect produce distinct accounting instructions.
  - Contradiction/missing terminal history retains/requires recovery.
- **Next action:** Implement only after dependencies pass.

#### E06 — NonLiveFailureDestroyer

- **State:** `READY_AFTER_E05`
- **Owner:** capital-verification
- **Kind:** fmea-fault-injection
- **Responsibility:** Inject response loss, duplicate admission, partial fill, stale snapshot, missing fills, contradictory terminal history, restart and replay to falsify effect/reconciliation/accounting laws.
- **Depends on:** `E05`
- **Files:** `domains/capital/tests/test_nonlive_effect_destroyer.py`, `domains/capital/destroyer/nonlive-effect-failure-matrix-r1.json`
- **Must not own:** new recovery semantics
- **Authority boundary:** Verification only.
- **Acceptance:**
  - No ambiguous case becomes a blind resend.
  - No stale provider fact reopens terminal accounting history.
  - Replay/idempotency and restart cases retain exact effect identity.
- **Next action:** Implement only after dependencies pass.

#### E07 — NonLiveDogfoodAcceptance

- **State:** `READY_AFTER_E06`
- **Owner:** capital
- **Kind:** consumer-e2e
- **Responsibility:** Run one full registered non-live circuit from frozen Decision through accounting resolution and emit a single bounded acceptance artifact.
- **Depends on:** `E06`
- **Files:** `domains/capital/acceptance/capital-nonlive-circuit-r1.json`
- **Must not own:** live-write claim
- **Authority boundary:** Non-live acceptance only.
- **Acceptance:**
  - All stages are registry-backed and contract-checked.
  - Physical execution success is not used as semantic completion.
  - External financial writes remain false before and after the run.
- **Next action:** Implement only after dependencies pass.

### W6_DEFERRED — Freeze future external-write requirements only; remain blocked until owner/provider authority changes.

#### P01 — ProductionEffectContractFreeze

- **State:** `BLOCKED_BY_AUTHORITY`
- **Owner:** capital-governance+trading
- **Kind:** deferred-contract
- **Responsibility:** Specify, but do not implement or activate, the additional requirements for DEMO/LIVE_QUALIFICATION/PRODUCTION effect classes: fresh provider permission, account eligibility, capital mandate, risk budget, reconciliation health, credential separation and explicit production authorization.
- **Depends on:** `E07`
- **Files:** `domains/capital/planning/production-effect-requirements-r1.json`
- **Must not own:** permission grant; credential creation; provider-side agreement acceptance
- **Authority boundary:** Deferred requirements only.
- **Acceptance:**
  - Requirements are explicit and machine-checkable.
  - Current BLOCK_NOT_GRANTED state keeps production path unreachable.
  - No provider write adapter is selected merely by planning.
- **Next action:** Implement only after dependencies pass.

#### P02 — ProviderWriteAdapterQualification

- **State:** `WAIT_FOR_REAL_CONTRACT`
- **Owner:** capital-trading
- **Kind:** deferred-experiment
- **Responsibility:** When a real admitted write contract exists, compare provider-native SDK/FIX/broker candidates against the exact adapter contract; select the smallest qualified owner and retain alternatives as challengers.
- **Depends on:** `P01`
- **Files:** `future qualification evidence only`
- **Must not own:** automatic framework adoption; credential policy
- **Authority boundary:** Future provider mechanics qualification.
- **Acceptance:**
  - Runs only after prerequisite authority facts are current.
  - Candidate must preserve identity/reconciliation/effect guarantees.
  - No generic OMS is adopted without active contract need.
- **Next action:** Implement only after dependencies pass.

#### P03 — ProductionAdmissionGate

- **State:** `BLOCKED_BY_AUTHORITY`
- **Owner:** capital-governance
- **Kind:** deferred-admission
- **Responsibility:** Materialize production effect admission only after owner-native production authorization and all provider/risk/reconciliation prerequisites are independently current.
- **Depends on:** `P01`, `P02`
- **Files:** `future source only after authorization`
- **Must not own:** owner consent; provider permission
- **Authority boundary:** Future production domain admission only.
- **Acceptance:**
  - Absent authorization is a hard structural block, not a warning.
  - Read-only/non-live circuits remain usable independently.
  - Authorization changes require explicit evidence and do not retroactively reinterpret historical circuits.
- **Next action:** Implement only after dependencies pass.

### W7 — Cross-cutting architecture, information-flow, reliability, CI and R1 acceptance.

#### V01 — ArchitectureBoundaryChecks

- **State:** `READY_AFTER_R03_T05`
- **Owner:** capital+repo-mechanics
- **Kind:** repo-verification
- **Responsibility:** Add narrow repository checks enforcing Capital ownership/dependency laws: Markets no upward imports, candidate tools not canonical dependencies, Gateway/Runtime/Host do not absorb Capital semantics, Skills remain advisory.
- **Depends on:** `R03`, `T05`
- **Files:** `domains/capital/tests/test_architecture_boundaries.py`
- **Must not own:** generic dependency framework
- **Authority boundary:** Repository mechanics only.
- **Acceptance:**
  - Known forbidden edges fail targeted fixtures.
  - No capital.* Gateway capability is required for domain correctness.
  - Candidate-only tool paths cannot enter canonical runtime imports.
- **Next action:** Implement only after dependencies pass.

#### V02 — InformationFlowAudit

- **State:** `READY_AFTER_T02`
- **Owner:** capital-security
- **Kind:** information-flow-verification
- **Responsibility:** Trace credentials/private account data/provider endpoint material through source→transform→store→channel→sink and prove that read-only observation, Skills, evidence and logs do not widen secret/effect authority.
- **Depends on:** `T02`
- **Files:** `domains/capital/planning/information-flow-r1.json`, `domains/capital/tests/test_information_flow_boundaries.py`
- **Must not own:** secret vault; provider IAM
- **Authority boundary:** Information-flow proof only.
- **Acceptance:**
  - Executor credentials remain excluded from observer paths.
  - Repository/evidence contains no secret bytes.
  - Seeing private data does not imply write authority.
- **Next action:** Implement only after dependencies pass.

#### V03 — FmeaFtaCapitalCircuitAudit

- **State:** `READY_AFTER_Q04_E05`
- **Owner:** capital-verification
- **Kind:** reliability-analysis
- **Responsibility:** Run FMEA/FTA over read and effect circuits for stale data, clock drift, provider outage, response loss, duplicate effect, reconciliation contradiction, ledger corruption and registry drift.
- **Depends on:** `Q04`, `E05`
- **Files:** `domains/capital/planning/fmea-fta-r1.json`
- **Must not own:** new controls without demonstrated gap
- **Authority boundary:** Analysis/evidence only.
- **Acceptance:**
  - Each top event maps to existing control or named gap.
  - Unsafe interaction paths are distinguished from component failures.
  - Findings either change a boundary/test or record justified no-change.
- **Next action:** Implement only after dependencies pass.

#### V04 — CapitalVerifyIntegration

- **State:** `READY_AFTER_ALL_ACTIVE`
- **Owner:** capital
- **Kind:** ci-integration
- **Responsibility:** Integrate registry/contracts/circuit/boundary tests into hermetic capital:verify while keeping provider qualification separate and node-local.
- **Depends on:** `Q05`, `E07`, `V01`, `V02`, `V03`
- **Files:** `domains/capital/mise.toml`, `mise.toml`, `.github/workflows/ci.yml`
- **Must not own:** credential-bound provider evidence in hermetic CI
- **Authority boundary:** Verification orchestration only.
- **Acceptance:**
  - Hermetic CI has no credentials/network/provider binaries as hidden prerequisites.
  - Provider-qualification marker remains separate.
  - Current source suite and new architecture gates pass together.
- **Next action:** Implement only after dependencies pass.

#### V05 — CapitalLegoR1Acceptance

- **State:** `READY_AFTER_V04`
- **Owner:** capital
- **Kind:** release-acceptance
- **Responsibility:** Produce one acceptance record proving registry completeness, contract composition, read-only circuit dogfood, non-live effect closure, boundary checks and explicit production-write non-admission.
- **Depends on:** `V04`
- **Files:** `domains/capital/acceptance/capital-lego-architecture-r1.json`, `domains/capital/docs/CAPITAL_LEGO_ARCHITECTURE_R1.md`
- **Must not own:** future production standing
- **Authority boundary:** R1 source/evidence acceptance only.
- **Acceptance:**
  - Acceptance names exact commit/tree and test evidence.
  - Production authorization remains BLOCK_NOT_GRANTED unless independently changed by its owner.
  - Deferred W6 nodes remain deferred and are not counted as incomplete R1.
- **Next action:** Implement only after dependencies pass.

## Parallelization

Initial parallel set: `C01`, `C02`.

After W1, the four W2 contracts `T01–T04` can run in parallel. W3 read-circuit work and W5 non-live effect work share `T05` but then diverge. Skills `S02/S03` can proceed once the read-only circuit family is stable; `S04` deliberately waits for effect reconciliation.

## Critical path

1. `C00`
2. `C02`
3. `R01`
4. `R02`
5. `R03`
6. `T01`
7. `T02`
8. `T03`
9. `T04`
10. `T05`
11. `Q01`
12. `Q02`
13. `Q03`
14. `Q04`
15. `Q05`
16. `S01`
17. `E01`
18. `E02`
19. `E03`
20. `E04`
21. `E05`
22. `E06`
23. `E07`
24. `V03`
25. `V04`
26. `V05`

## Explicit non-goals

- CapitalAgent god-object
- Capital-specific Gateway database or workflow engine
- Capital-specific Runtime scheduler
- new universal finance ontology
- generic OMS/backtest/risk engine without an active contract
- provider-secret registry inside Capital
- automatic risk-tolerance inference
- scenario ranking/recommendation hidden inside Portfolio
- live/production write adapter before independent authority admission
- duplicate Network route/VPN selector
- duplicate provider/account truth store
- generic Effect framework inside Runtime for Capital

## R1 completion

R1 is complete when W0–W5 and W7 pass their acceptance gates. W6 remains deferred by design. A future change to production authorization is a separate owner-native event and cannot be inferred from this plan, a passing test, a compiled circuit, or successful simulated execution.
