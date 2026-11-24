# Workstation contract-first convergence — implementation spec R1

**SourceCut:** Ordivon GitHub `main` at `3b43977e682d8c7668f6371ffd998c7821e4312a` (2026-11-09).
**Natural Owner:** `platform/workstation`. **Status:** specification and phased implementation, not a deployment receipt.
**Consumer:** operators and Agents converging the actual Windows/WSL host, plus Runtime/Harness/domain consumers resolving node-local tools.
**Guiding choices:** DELETE unnecessary custom work → REUSE mature native mechanisms → COMPOSE → only a thin justified adapter. Do not create another policy engine, agent manager, registry, scheduler, or per-LEGO file tree.

## 1. Problem / observed counterexample

The same host has a real Windows-user `.wslconfig` with `memory=10GB`, `swap=0`, `sparseVhd=false`, while `ansible/host-substrate.yml` declares `memory=8GB`, `swap=6GB`, `sparseVhd=true` and targets one literal Windows-user pathname. A generic Linux-host playbook can therefore silently revert an independently changed Windows-user global WSL policy. This is a multiple-writer ownership error, not a reason to add an agent overseer.

Already existing `tests/test_workstation_consequences.py` also deliberately requires some observability services to remain cold. A model must not interpret every `inactive` service as a broken environment.

## 2. Outcome / non-goals

**Outcome:** a caller can reconcile *Linux distribution and systemd host state* without mutating Windows-user global `.wslconfig`; the actual user-scoped Windows host setting is observed from its native owner, not silently replaced from WSL. Later, if automatic Windows global WSL configuration becomes a necessary consumer requirement, choose one mature Windows-native configuration owner with an explicit user-context binding, readback and restart boundary.

**Non-goals:** no weak-model benchmarks, new agent roles, new orchestration engines, full ECC installation, universal architecture lint framework, blanket observability restarts, forced WSL shutdown, or changing the user's global WSL settings in this source-only slice.

## 3. Reference methods and selective adoption

- Matt Pocock Skills: `to-spec` fixes domain vocabulary and public test seam; `to-tickets` expresses blocking edges; `implement` and `tdd` deliver one vertical, observable change; `code-review` reviews after implementation. Source: https://github.com/mattpocock/skills
- ECC (`affaan-m/ECC`): reusable project-native checks and hooks, lean context and retained quality feedback. Adopt the method, **not** its complete hook/agent/registry surface. Source: https://github.com/affaan-m/ECC
- obra/superpowers: isolated git worktrees, executable plan, per-task RED/GREEN, systematic debugging and verification-before-completion. Source: https://github.com/obra/superpowers
- Ordivon canonical: `.agents/skills/recursive-lego-calculus/SKILL.md`, `docs/architecture/TESTING_UPSTREAM_ADOPTION_R1.md`, existing Owner-native `mise run verify`.

## 4. Existing boundaries / public test seam

```text
Windows-user global configuration: %UserProfile%/.wslconfig (native/user-scoped owner)
Linux distribution configuration: /etc/wsl.conf (Ansible Workstation)
Linux systemd manager settings: /etc/systemd/{system,user}.conf.d (Ansible Workstation)
                      ↓
Windows/WSL actual generation readback (native OS, activation on explicit restart)
                      ↓
Runtime target and principal observation → actual consumer acceptance
```

The first public seam is **the Ansible playbook execution surface**, not an invented WSL wrapper. Its task list must contain the Linux distro/systemd convergence but no writer to Windows-user global `.wslconfig`. Use Ansible native `--syntax-check`/`--list-tasks` and current pytest; an independent read-only native observation is required when claiming deployed state.

## 5. Typed R2.1 contract — responsibility, not source file

`ell = (I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`

| Coordinate | Typed interpretation |
| --- | --- |
| I | `HostTarget × LinuxHostDesiredState × WindowsGlobalObservation?` |
| O | `LinuxConvergenceEvidence × ScopedObservation`; no Windows global activation claim |
| S | `(GitSourceCut, LinuxDesired, LinuxObserved, WindowsUserGlobalObserved?, ActiveWSLGeneration?)` |
| pre | Ansible can access its Linux targets; a Windows global value is only comparable when actually observed with the appropriate Windows identity |
| post | Running the Linux host-substrate playbook does not write the Windows-user global `.wslconfig`; Linux-scoped operations retain their existing semantics |
| inv | `WriteSet(host-substrate) ∩ WindowsUserGlobalWSLConfig = ∅`; `UNKNOWN ≠ FALSE`; `source declared ≠ activated` |
| eff | Linux systemd config and Linux `/etc/wsl.conf` effects remain; Windows-global writes are excluded |
| c | `UNKNOWN(cost, observed runtime and adoption overhead not yet measured)` |
| epsilon | `UNKNOWN(abstraction, static Ansible source-to-external-effect refinement remains bounded by the native test seam)` |
| prov | Exact Ordivon source SHA, native Ansible source/command, observed Windows config where available, execution identity and timestamps |
| unfold | Native `ansible/host-substrate.yml`, `workstation/windows/workstation.dsc.yaml`, existing `tests/`, current Runtime target/identity readback |

A syntactic source check is **not** proof of arbitrary external side-effect non-interference. The proven scope is the retained Ansible task list and the observed files; independent runtime readback closes its physical seam.

## 6. Formal/operational obligations

- **WSL-W1 Single writer:** The Linux host playbook does not contain a Windows-global `.wslconfig` writer; positive control: `/etc/wsl.conf` and systemd tasks remain.
- **WSL-W2 Authority separation:** An actual `.wslconfig` value is not silently replaced by a historical Linux-sourced default. Changed Windows-user policy must require explicit Windows-scoped reconciliation.
- **WSL-W3 No false completion:** a successful playbook/syntax check does not imply WSL was restarted or its active generation changed.
- **WSL-W4 No accidental global observability restart:** inactive services are checked against the current Workstation `remain_cold` consumer test before proposing changes.
- **WSL-W5 Bounded external effect:** source-only phase does not apply Ansible, shut down WSL, restart services, alter Windows global configuration or deploy Cloudflare.

For W1–W3 prefer native Ansible and consumer tests over a new SMT model. Higher-consequence future replacement/restart paths may warrant TLA+/Quint or an existing R2.1 refinement when there is a precise state-machine failure; do not add formal artifacts without an implementable acceptance predicate.

## 7. Ordered task graph and precise implementation

| ID | Depends on | Change | Acceptance |
| --- | --- | --- | --- |
| T0 SourceCut | — | Pin current GitHub main, separate branch/Workspace, locate real consumer and existing tests | exact SHA, clean independent branch |
| T1 Spec | T0 | This doc: responsibility, assumption, counterexample, obligations, non-goals, dependencies | full typed contract, exact paths and test seam |
| T2 RED | T1 | Add consumer-facing test at Ansible task surface; require Linux tasks retained and Windows-global tasks absent | focused pytest fails on current source (before code changes) |
| T3 GREEN | T2 | Delete outdated Windows-global `.wslconfig` variables and tasks from Linux playbook, keep Linux/systemd functionality | focused test passes, native `ansible-playbook --syntax-check` and `--list-tasks` pass |
| T4 Verification | T3 | Focused source and consequence tests, Workstation native CI where environment permits, diff review and separate non-mutating live config read | no false PASS; SKIP/NOT_RUN explicit, source/installed/active kept distinct |
| T5 Future Windows-native realization | T4, real consumer | Select Windows-native DSC/WinGet-compatible owner for global WSL user profile only if managed convergence is actually required | exactly one user-scoped writer, explicit restart, independent Windows readback |
| T6 Consumer/tool expansion | T4, actual request | Reuse osquery/WinGet/DSC/Nix/Runtime instead of new inventory; strengthen identity-specific executable binding where observed gaps exist | real consumer under correct principal; distinct materialized/available/accepted |
| T7 Retirement | T4–T6 as applicable | Remove unused legacy providers, stale snapshots/docs, old alternate paths after observed consumer cutover | Git history retains provenance, no active writer or consumer left, scoped tests pass |

T5–T7 are **conditional successor work**, not permission to create planned services now. Existing cross-Owner branches and Workspaces are left untouched.

## 8. Method and completion rules

1. Implement the smallest *vertical* change that makes the negative control red, then green (Matt TDD / Superpowers).
2. Test with real Owner tooling, do not test code purely by duplicating internal functions; prefer externally observable task list + actual OS readback.
3. ECC-style automated feedback uses existing `mise`, `pytest`, Ansible and GitHub Actions; do not add a second check registry.
4. Review impact on all known consumers; if a plan contradicts a current source fact, record the ruling and update the plan instead of silently changing acceptance criteria.
5. Do not claim `MERGED`, `INSTALLED`, `LOADED`, `CONSUMED` from a commit or test alone. Only report observed standing.
6. For the Workstation P0 slice the completion contract is: T2 observed RED, T3 GREEN, native Ansible checks PASS, source diff reviewed, Git commit created. Production application is not implied.

## 9. Rollback, risks and unresolved boundary

A Git revert restores the former playbook source but **would also restore the unwanted Windows-global writer**; rollback must be explicitly reviewed against current Windows-user intent. There is no production activation/rollback operation in T0–T4. Existing `/etc/wsl.conf` remains managed from Ansible. Windows-native orchestration of `.wslconfig` is deliberately outside the first slice until a real user-scoped configuration consumer and appropriate native execution authority are selected.

**Most important risk:** Ansible static source/test success does not prove the complete active machine state; read actual Windows user config and the active WSL generation before any deployed acceptance statement.

## 10. Executed source-only slice (2026-11-09)

- RED: `uv run --locked python -m pytest -q tests/test_host_substrate_authority.py` failed on the original `.wslconfig` writer, as expected.
- GREEN: the same regression passed after removing the obsolete Windows global WSL configuration tasks and variables; Linux `/etc/wsl.conf` and systemd tasks remain.
- Focused check: `uv run --locked python -m pytest -q tests/test_host_substrate_authority.py tests/test_workstation_consequences.py tests/test_machine_inventory_contract.py tests/test_executable_probe.py` finished with **10 passed, 1 skipped** (the skipped test was not upgraded to a success claim).
- Native Ansible: `ansible-playbook --syntax-check` and `--list-tasks` passed. `ansible-playbook --check --diff` reported 9 tasks OK, 0 changed, 0 failed.
- External observation: the live Windows-user `.wslconfig` SHA-256 was `f94d463c69a40064d0734667a327912986adaaaf659dec7b9ab3a3a14c95ce98` both before and after Ansible check mode; no Windows host configuration was written or WSL restarted.
- Complete Workstation owner verification: `mise run verify` exited zero, including owner CI and installed-user consequence tests. This is a source/host check of the candidate, **not** mainline merge or deployed release evidence.


## 11. R2 theory-to-engineering decision map — mature mathematics, not a new calculus

**Current-source continuation:** first source cut `3b43977...` is historical
provenance for PR #1967; that PR **MERGED** on 2026-11-09 14:27:37 UTC,
merge commit `120bf398b6392f5e3dde91ab00b024282d3884cb`, with required GitHub
checks completed. The next bounded refinement starts from protected main
`a7d70e83945b7418f41b9636f0803d1544e84355`. Neither Git merge proves
installed generation nor current active Windows WSL instance.

### 11.1 Hoare logic, weakest preconditions and the frame boundary

For actual host convergence command `C`, write a *partial-correctness* obligation:

```text
{LinuxTarget ∧ SelectedPrincipal ∧ ValidInput}
  C = ansible-playbook host-substrate.yml
{LinuxDesiredConverged ∧ WindowsUserGlobalStatePreserved}
```

The latter conjunct is a **frame property**, not a desired-state value.
The frame should follow from non-overlapping owned write sets, not from
hardcoding this week's `memory=10GB` or `swap=0` into a Linux playbook:

`WriteSet(C) ∩ WindowsGlobalWSLConfig = ∅`.

Classical Hoare logic is about a specified command under specified operational
semantics and assumptions; it does not establish that an arbitrary plugin,
credential helper, source include or target environment cannot have an indirect
effect. This matters because an opaque Ansible `shell`, imported tasks, or
templated Windows destination would invalidate our current finite static frame.
They must therefore be **unqualified/UNKNOWN** until examined, not silently
allowed, not universally declared malicious. The production Windows-global
write owner is outside this Linux playbook.

**Adopted reference:** C. A. R. Hoare, *An Axiomatic Basis for Computer
Programming*, CACM 1969,
https://doi.org/10.1145/363235.363259.

### 11.2 Assume–guarantee algebra and behavioral substitutability

Model a retained responsibility as a contract `C=(I,O,A,G)`, with explicit
assumptions `A` and guarantees `G`. The Linux host Owner guarantees only
its owned target effects and records that Windows-global configuration is
outside its write frame. The Windows native user-context configuration
authority, when a real such consumer is selected, must have a separate
assumption about execution identity and guarantee about its own configuration.

Composition is sound only under compatible types, assumptions, guarantees,
principal/effect boundaries **and actual observation**; a syntactic matching
interface is insufficient. For provider replacement relative to existing
consumer obligations, a useful sufficient directional test is:

```text
ExistingAssumptions => CandidateAssumptions
CandidateGuarantees => ExistingGuarantees
CandidateEffects subseteq PermittedEffects
```

Those implications are subject to common variables, contract saturation,
environment assumptions and the observed semantic profile. Use the canonical
R2.1 contract algebra and existing composition skill; do not invent a second
`C` object registry or claim universal refinement from these shorthand
implications.

**Adopted reference:** Pacti documentation (composition, refinement, quotient,
merging), https://www.pacti.org/docs/getting_started/; NASA FRET
assume–guarantee realizability,
https://ntrs.nasa.gov/citations/20210024604; Liskov and Wing, *A Behavioral
Notion of Subtyping* (1994), https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf.

### 11.3 Refinement and observation semantics

Define an abstract contract relation `R_spec`, actual execution relation
`R_impl`, and owner-specific observation `Obs_c`. For a candidate
implementing a safety contract, the target is:

`Obs_c(Traces(R_impl)) subseteq Obs_c(Traces(R_spec))`

under stated assumptions, relevant stuttering/hidden-action semantics, and
source/environment currentness. Model checking the abstract relation does
**not** prove this trace inclusion for arbitrary Ansible modules or Windows
services. Current Workstation tests check a finite source-level class of
supported actions and an Ansible check-mode consequence on one host.
They do not establish live WSL restart, non-existent alternate writers, or
Windows native user-context authority.

### 11.4 Abstract interpretation, CEGAR and independent falsification

Use a supported-language source projection `alpha(Source)` of Ansible tasks
into abstract effects `E#`. A *soundness* claim would require
`Effects(Execute(Source)) subseteq gamma(E#)`; that premise is **not
established** by YAML parsing alone. Instead the next implementation slice
makes the supported subset explicit:

- Parse YAML with mature `PyYAML.safe_load` (no private YAML parser).
- Admit only the **known native module effects** in this Linux host playbook:
  file, copy, systemd_service, ini_file, debug.
- For path-bearing effects, require static Linux `/etc/systemd/` destinations or
  the exact per-distribution `/etc/wsl.conf`.
- Bind the existing loop variables to the finite declared Linux settings and
  `systemd-homed` service names.
- Reject unknown module, dynamic path, import/include, Windows target, or
  missing original Linux consumer from **this check's proof claim**. A new
  legitimate action is not forbidden in principle: its natural Owner may
  extend the contract with an explicit qualifying test.
- Use known bad edits as independent **negative controls**, not an LLM
  benchmark. Preserve a good source case to reject vacuous `always fail` checks.

Thus `PASS` means only that this exact source satisfies the closed,
conservatively selected *static task-frame predicate*. It is not global OS
noninterference. A failing negative control shows the check no longer detects
its own scoped bad case; use normal RED→GREEN diagnosis before release.

**Adopted references:** Cousot's abstract interpretation/abstraction
refinement research, https://www.di.ens.fr/~cousot/researchthemes.shtml; existing
Ordivon `.agents/skills/recursive-lego-calculus/SKILL.md` and
`tools/formal/RecursiveLegoRefinement.lean`.

### 11.5 Temporal logic: configuration versus active generation

For state `s=(Source, Desired, Materialized, Active, Accepted, Observed)`,
use separate claims:

```text
SAFETY:
  Always(ActiveAccepted =>
         CurrentNativeActiveObservationMatchesConsumerContract)

PROGRESS (conditional):
  Always(AdmittedQualifiedReconciliationAndFairResources =>
         Eventually(NewObservationOrExplicitBoundedBlocker))
```

The progress claim is conditional on availability and fairness, not an
unconditional promise of success. A new config file is not proof that WSL
has restarted; Microsoft explicitly separates global `.wslconfig`,
per-distribution `/etc/wsl.conf`, and VM restart/activation.
Use existing TLA+/TLC/Quint methods *only* for a real transition/recovery
defect requiring them; the current straightforward static write-frame change
does not justify a new model-checker service or artificial state system.

**Adopted references:** Leslie Lamport, *Specifying Systems*,
https://lamport.azurewebsites.net/tla/book.html; Microsoft WSL Settings,
https://learn.microsoft.com/en-us/windows/wsl/wsl-config.

### 11.6 Information hiding, DSM and consumer-rooted subtraction

By Parnas's information-hiding criterion, Workstation owns **how a local host
and node materialize generic settings**, not Windows user policy merely because
WSL makes its file reachable under `/mnt/c`. Domain owners retain
semantic results, Runtime retains physical execution truth, Host retains Work
collaboration state. A repository folder or an Agent is not a LEGO.

Use the already installed design-structure-matrix Skill on *observed*
dependencies if deciding a larger ownership split. An interface is worth
keeping when changing its implementation does not force consumer changes.
For obsolete writers or documents, invert the analysis: inspect live consumers,
possible indirect reads and source currentness, then delete the redundant
path. The existing axiom-free R2.1 retirement theorem remains conditional on
closed/current consumer evidence; absence in a path grep is not that evidence.

**Adopted reference:** D. L. Parnas, *On the Criteria To Be Used in Decomposing
Systems into Modules* (1972),
https://doi.org/10.1145/361598.361623.

### 11.7 Evidence economics: formal proof is property-scoped

Proof effort must be proportional to a **specific falsifiable property and
failure cost**. For this Workstation scope, the cheapest sound useful
sequence is:

`SourceSpec → Native YAML Structural Check → Negative Controls →
Ansible Syntax/List/Check → Current Windows/WSL Readback → Real Consumer`.

The source gate cannot substitute for the later readbacks; each has its own
version, toolchain, observer, assumptions and validity time. A final report
must explicitly distinguish `SOURCE_VALIDATED`, `PR_MERGED`,
`INSTALLED_CURRENT`, `ACTIVE_GENERATION_ACCEPTED`,
`DOMAIN_ACCEPTED`, and scoped `UNKNOWN`. These are evidence distinctions,
**not** a proposal for another universal state enum/database.

## 12. Upstream engineering methods — exact adopter and exclusion rules

- **Matt to-spec:** use already settled goals and name one public test seam;
  do not restart interviews. **Matt to-tickets:** ready-frontier dependencies,
  each ticket demonstrates independent consumer behavior. Wide mechanical
  migrations use expand–migrate–contract rather than layer-only tasks.
  **Implement-spec:** borrow sparse context pointers and integration-branch
  discipline; never copy a second subagent scheduler or GitHub issue authority.
  Source: https://github.com/mattpocock/skills
- **ECC:** event-driven feedback belongs in existing Owner tests, `mise`,
  GitHub Actions and actual Runtime/Harness boundaries; do not deploy the
  complete Claude hook/agent/memory system. Source:
  https://github.com/affaan-m/ECC.
- **Superpowers:** isolated source, TDD with an observed failing negative,
  systematic root-cause diagnosis, source/currentness verification before
  completion, reviewer who did not define the entire acceptance rule.
  Use current Runtime Workspace rather than another worktree manager.
  Source: https://github.com/obra/superpowers.
- **Ordivon canonical method:** `method-router` and `recursive-lego-calculus`
  already select relevant trusted methods; Host Space coordinates independent
  review, not execution, permission or semantic truth.

### Direct collision checks

Before changing a shared method, search current main for existing
`AGENT_CONTRACT_EXECUTION_SPEC_R1.md`, `AGENT_OUTCOME_*_SPEC*.md` and
ongoing Agent implementation branches. Those own system-wide guidance.
This document only specifies the **Workstation native consumer** and
does not create another whole-system Spec, second `AGENTS.md` or mandatory
methodological step for routine local edits.

## 13. Next vertical tracer bullet: WSL-W1 finite effect-frame strengthening

**T8 (depends on merged T4, real regression in T2):**

- **Agent-visible intent:** the Linux host playbook remains usable while its
  finite supported effect projection cannot silently contain a Windows-global
  write or an unexamined arbitrary command.
- **Existing Owner:** `platform/workstation`, existing
  `tests/test_host_substrate_authority.py`, `pyproject.toml`, `uv.lock`.
- **Native dependency:** add pinned PyYAML only as a normal Workstation test
  dependency; no custom YAML parser/checker daemon.
- **Deliverable:** replace the earlier literal-string acceptance with parsed,
  closed-source effect-frame predicates in the *existing test file*.
- **Negative oracles:** Windows-global INI path, dynamic file destination,
  `shell` action, imported tasks, and removal of the Linux `/etc/wsl.conf`
  consumer must all be rejected. The actual present playbook must pass.
- **Execution:** `uv run --locked python -m pytest -q
  tests/test_host_substrate_authority.py`; `ruff check`;
  `ansible-playbook --syntax-check`; `mise run verify`; GitHub CI and
  protected Merge Queue. Non-mutating Ansible `--check` may supplement
  source-only claims but is not automatically a deployment proof.
- **Proof limit:** absent arbitrary imported code, opaque shell or nonstandard
  modules in this exact source, the *finite source projection* has no
  Windows-user global file write. Real module/effect semantics, installation,
  unrelated writers, active Windows instance and domain consumers remain
  separate evidence.

**T9 (conditional real Windows consumer):** Observe the intended active user
and service identities separately using existing `probe_executables.ps1` and
native WSL settings/readback; compare source materialized and active state.
Never treat `not_on_path` under a service identity as globally not installed.
If no automatic global Windows configuration consumer is identified, stop
rather than inventing a config authority.

**T10 (conditional retirement):** For every remaining older provider/doc
candidate, use native Git/Host/current consumer evidence; retire the exact
redundant chain once current consumers are migrated. Avoid separate migration
framework, historical snapshot false authority, or machine-by-machine ceremony.

## 14. Cross-Agent coordination and independent challenge

Use the **existing** Host collaboration locations:
- `space:ordivon-capability-task-forum-r1:20261101`,
  `topic:ordivon-capability-task-forum-r1:03-refinement:20261101`,
  message sequence `25744`: ask for Windows-native consumer, independent
  R2.1 falsification and conflicts with current Owner source;
- `space:ordivon-whole-system-optimization-r1:20261002`,
  `topic:ordivon-whole-system-optimization:matt-v131-method-family-r1:20261005`,
  message sequence `25745`: selective upstream-method adoption and
  duplication detection.

Messages are **requests for review**, not peer approval or proof of a reply.
Only attribute findings to other Agents if there is an actual returned
message with the exact source/consumer evidence. Source modification, Work
semantics, Runtime execution and deployed acceptance remain with their
native authorities.


## 15. T9 independent Windows native identity/readback receipts (2026-11-09)

All three observations were **read-only** native Windows Runtime operations,
executed on the actual Windows node, not a Linux imitation of Windows PATH:

| Runtime Job / principal scope | Current observations | What this establishes |
| --- | --- | --- |
| `job-01a1c0f8-7202-7c61-a34a-dc9476f3715c`; `limited` service | `git` on PATH; `gh/mise/uv/pnpm` not on that service PATH | This principal's PATH lookup only; NOT global application absence |
| `job-01a1c0f8-cf8c-7271-b298-a9dc91d5e0f4`; `active_user` | `git/gh/mise/uv/pnpm` all on interactive-user PATH | Separate consumer identity has separate tool projection; NOT task authorization |
| `job-01a1c0f9-5c36-7793-9eef-16dece68322d`; `active_user` | Native `%UserProfile%/.wslconfig` exists, SHA-256 `f94d463c69a40064d0734667a327912986adaaaf659dec7b9ab3a3a14c95ce98`; selected settings: memory 10GB, processors 16, swap 0, sparseVhd false | Actual user-scoped Windows **file bytes** current at read time; installed/active WSL generation remains **UNKNOWN** |

These are **observations of two different Windows execution principals**.
Do not collapse their PATH sets, even though both execute on the same
machine. The active-user readback independently confirms the earlier Linux
mounted-file digest but does **not** prove that any already-running WSL VM
has activated those settings. No `wsl --shutdown`, service restart,
DSC apply, package install, global config write, or policy change was used.

**T9 status:** scoped identity-specific probe and native user-config
observation **completed**; native active-generation comparison and automated
Windows-global configuration convergence **not performed**, because they
require separate real consumer obligations and an explicit restart boundary.
Potential adjacent code stays with the installed `probe_executables.ps1`
and existing Windows/Runtime owners, not a second inspector.
