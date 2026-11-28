# Artifact testing reform R17

Authority: existing TESTING_UPSTREAM_ADOPTION_R1, Standing R2.1, R16 and
Host #32831/#32904. No new testing service, registry or separate CI authority.
Preserve native format consumers; evidence validity is not line coverage.

## Thought / Logic / Capability
| Thought | Logic | Reuse |
|---|---|---|
| Independent oracle | required claims, UNKNOWN, native identity | existing finite models + independent Hypothesis relations |
| Generative/adversarial testing | JSON, nested identity, resource closure | Hypothesis shrinking and pytest |
| Metamorphic testing | key ordering, Unicode encoding, chunk partition | standard JSON/stream/hashlib |
| Stateful model | receipt commit/replay, input drift and corruption | Hypothesis RuleBasedStateMachine + actual filesystem ReceiptFence |
| Differential testing | independent native parsers and consumers | existing WARC/GLB/Office/GeoPackage native lanes |
| Fault injection / mutation | false PASS, ignored witness, type confusion | scoped mutant experiment; mutmut candidate after compatibility qualification |
| Current qualification | declared native method and actual consumer | tool_identity, historical witness immutable |
| Environment classification | execution authority, unavailable tooling | existing integration marker, strict markers/config |
| Regression selection | property and consumer, not file count | existing owner CI/pytest; R16 #2834 |
| Release acceptance | exact source, installed generation, native result | Runtime receipt, Temporal replay, OCI and real consumer |

References: Hypothesis https://hypothesis.readthedocs.io/en/latest/stateful.html ;
pytest https://docs.pytest.org/en/stable/example/markers.html ;
metamorphic survey https://doi.org/10.1109/TSE.2016.2532875 ;
oracle survey https://doi.org/10.1109/TSE.2014.2372785 ;
mutmut https://mutmut.readthedocs.io/en/latest/ .

## Minimal executable obligations
I=(profile, exact subject/contract, generated inputs/actions, source cut, method);
O=(independent oracle, minimized counterexample, native evidence, test status);
S=(existing receipt states, immutable input/role bytes);
pre=selected real owner, bounded generated domain, source/tool identity;
post=counterexamples reproducible, valid controls pass, no false complete;
inv=UNKNOWN != FAIL, replay cannot silently execute again, invalid JSON rejected,
type-distinct receipt inputs never alias, historical evidence not rewritten;
eff=private tests and native admitted execution; c=bounded examples/steps and
measured wall time; epsilon=not exhaustive arbitrary JSON or concurrent crash
proof; prov=source SHA, lock, test/job receipt; unfold=existing shared
json_validation, claim_coverage, native_identity, file_stream, glb_closure,
ReceiptFence, native adapters.

P0 adopt Hypothesis only in test group (rolling compatible >=6), strict marker
and config recognition. Deterministic CI 100 examples per generative property,
small finite domains may exhaust early; state machine 40 examples x15 steps
maximum, no claim of exact executed example count. Source equality is not a
test oracle. Retain ordinary regression cases with distinct properties.
P0 reject Python JSON nonstandard constants and type-confused/corrupt receipt
replay. Preserve valid existing JSON receipt wire schema and key order
equivalence; no attestation of hostile same-principal storage writes.
P1 qualify mutation engine against current Python 3.15 separately; do not
introduce blocking global mutation score. Scoped falsifiers are not a complete
mutation campaign. P1 R16 native split and rolling-vs-historical qualification,
actual rich GLB and GeoPackage receipts. P1 Runtime effect delegation for
OCI and Temporal replay; native environment failures remain distinct.
P2 run consumer-driven release gates and targeted extended property/fuzz
budgets based on actual faults; no arbitrary coverage target or test deletion.
