# Artifact R19 — native test obligation qualification

Extends Standing R2.1, Execution Boundary R16, Testing Reform R17,
Convergence R18. Host #33059, #33119, #33184; crosscore #33069,
Host #2862 exact donor fba454b15e9520eb84c8377775c912ac40d760de
tests/conftest.py, Research #32948. Adopt Host's native discovery,
phase and subtest observation pattern, not its DB fixture logic.

## Thought / Logic / Capability crosswalk

The R18 16 business Logic and R15 12 release Logic modules remain the
authority. Refine these testing intersections without another scheduler.

| Logic | Mature capability | Acceptance |
|---|---|---|
| Obligation definition | profile, owner tests, risk taxonomy | named native vs portable vs historical |
| Source census | Git source + pytest native collection | every ordinary named test file discovered |
| Selection | native pytest markers | exact partition, duplicate and silent drop rejected |
| Independent oracle | pytest assertions/Hypothesis | content, transport and historical identity separate |
| Native execution | existing pytest/Runtime | no alternative runner or retries |
| Fixture generation | package-owned KiCad Python, Pillow | no managed ABI injection or ignored cache dependency |
| Phase observation | pytest TestReport/SubtestReport hooks | exact parent phases; subtests additional |
| Evidence normalization | structured receipt, existing Runtime stdout | incomplete/skip/xfail never PASS |
| Historical reproduction | unchanged exact digest assertions | drift remains failure, separate from current tool |
| Native method admission | veraPDF strict native JSON and batch | explicit normal completion vs operational absence |
| Consumer standing | existing Standing and receipt fence | UNKNOWN not content FAIL; #2773 prerequisite for VSA |
| Currentness/retirement | Git source, generation, native consumer | evidence qualified at observed source and tool cut |

References: https://docs.pytest.org/en/latest/reference/reference.html,
https://docs.pytest.org/en/9.0.x/how-to/subtests.html,
https://docs.verapdf.org/cli/validation/,
https://docs.kicad.org/doxygen-python-10.0/pcbnew_8py_source.html.
KiCad SWIG is deprecated: reuse existing package-owned generator only
as an isolated test fixture, not a new production integration. Future
IPC or exact static native fixtures should be considered when it is removed.

## Contract and execution

I=(exact owner source cut, lane, native inventory, tool prerequisites);
O=(native exit, selected and expected identity commitments, complete phase
counts, incomplete/invalid reports, subtests); S=transient native pytest
session and existing Runtime result artifacts. pre=trusted source,
strict native collection, exact intended marker predicate, no ambient
selector/plugin; post=expected==selected, deselected==discovered minus
expected, all required parents have successful setup/call/teardown,
no skip/xfail/error/duplicate, existing native runner exit succeeds.
inv=nonempty scope, no hidden named module, historical byte mismatch cannot
be made current PASS, no test execution substitution, no retries.
eff=existing native test effects only; c=actual observed durations;
epsilon=source census is bounded to ordinary Python names; no proof of
malicious trusted-source mutation, omitted test obligations never written,
or full environment/readset; prov=Git exact commit/Runtime job/stdout and
matching node-ID digests. Parent phase success does not erase a failed
subtest; invalid reports are separate from observed physical teardown.

Tasks: existing mise verify/queue portable, native current, historical
exact historical reproduction. Use explicit native pytest focused calls
for development (not full lane qualification). Clear PYTEST_ADDOPTS,
PYTEST_PLUGINS, disable implicit plugin autoload, explicitly load
Hypothesis. pytest>=9.2 for actual public SubtestReport contract.
No production dependency declaration changes. Do not rewrite old proof.

veraPDF projection uses existing strict JSON decoder, exact single-job
path/size, batch counts, normal job completion, boolean compliant and
integer failure counts with exit 0/1 consistency; launch/timeout,
failed parse, inconsistent report or pre/post subject drift are NOT_RUN.
No native report digest binding or full ABA proof; exact profile name
is observed, not an independent proof of the CLI's selected flavor.
V1 gate standing depends on #2773 shared UNKNOWN receipt change.
Actual CLI untagged PDF exit1 with six failed rules/checks, bad input
exit7 with failedParsingJobs1 and no validation; do not claim PDF/UA
human acceptance or PowerPoint export by the new Pillow fixture.

## Observed R19 implementation
- Reconciled R18 remote branch exact bbcf595b5093f7124556e634015f8a8ac4146673;
  #2851 merged. #2773 exact02bceef2 10 CI success CLEAN normal queue7.
- Actual canonical 4d85a831 -> 05a44835079e8a1449e2f785454d1901fbf26ffd,
  48 commits, clean ff-only, only Artifact Worker restart. Current
  Python gen80b60f04 unchanged, SDK1.37.0 Worker PID1017582.
  job-01a2154a-0086-71c3-b01f-5ed780a37dcf. Real production unsigned
  development workflow artifact-r19-production-receipt-development-20261126,
  29 history events,27 exact role digests,4 referrers, replay PASS,
  releaseReady=false, job-01a2154b-0045-7626-9c1e-d7182640498f.
- Baseline collect-only false green job-01a21545-162f-7478-8ff6-dc438007b5f5.
  Native 17 observer controls PASS and root route1PASS
  job-01a21547-3811-7354-8e94-f2bf38a46609. Full portable with hostile
  environment 538/538, no skips,108 subtests,679 discovered/141 outside
  lane, 23.74s job-01a21547-93ab-763d-bc71-0d72cbc3005c.
- Historic 5 selected,2 pass,3 fail Assimp and GDAL old byte mismatch,
  exact unchanged assertions job-01a21548-eaaa-73bd-b409-4c09e08747e5.
  Current native first 136 selected,133 pass,3 skip,24 subtests,
  212.50s, native exit0 but qualification INCOMPLETE exit1,
  job-01a21549-3a50-745a-b2d0-4433e7cca53a.
- Missing prerequisites were test coupling: system KiCad10.0.8 Python
  3.14.10 pcbnew actual; managed3.15.2 cannot import ABI. Existing
  generator moved to isolated native subprocess, exact fixture semantics.
  veraPDF1.30.2 installed, ephemeral cached PowerPoint PDF absent; native
  ordinary untagged Pillow PDF replaces only negative validator control.
  4PASS job-01a2154f-07ad-7632-ad24-383466748a82.
- Actual raw veraPDF exit1 vs exit7 job-01a2154e-7fe3-7334-9bb2-b2684eb2cfed.
  8 RED transport counterexamples plus2 controls job-01a21550-350b-758c-b18f-8a52a2f274a2;
  11PASS job-01a21550-9d2e-73e3-a517-2496b0f656c7; final 33 focused PASS
  including native parse failure and phase classification
  job-01a21551-e744-713a-b37d-88fa05975c4f.

## Priorities after this candidate
P0 complete existing #2773 and #2834 protected integration, then rebase
explicit OCI provider and actual qualified execution delegation, preserve
Worker security and existing Runtime owner. P0 repeat independent full
current-native and portable lanes on frozen source, retain terminal
receipts separately; historical lane deliberately remains incomplete
until exact tool bytes are recovered. P1 current rich GLB/GeoPackage
native evidence and historical subject retrieval by natural Game owner;
do not substitute approximate assets. P1 mutation/independent oracle
qualification and durable result readback using existing Runtime/Artifact
retention, not a new result registry.
