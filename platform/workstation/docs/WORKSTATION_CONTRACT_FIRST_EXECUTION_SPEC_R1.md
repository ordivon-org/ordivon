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
