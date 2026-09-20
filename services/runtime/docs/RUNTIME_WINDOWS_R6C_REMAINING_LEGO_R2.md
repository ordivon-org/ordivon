# Native Windows R6c Remaining LEGO Plan R2

Status: C1/C2 PASS; C3/C4/C5 pending
Date: 2026-09-19
Candidate service: OrdivonRuntimeR6Candidate
Candidate node: windows-main-r6-candidate
Candidate endpoint: 127.0.0.1:18997
Production endpoint 127.0.0.1:8897 remains out of scope until final cutover.

## LEGO C1 — crash / SCM recovery

Verified on 2026-09-20 against release 00ae7525ff0d444f91f6250d5f055c635c0e092e: **PASS**.

Bound crash witness:
- harness Job job-01a0bd5c-d89e-7e31-9db5-7e331c9bfa67;
- candidate PID 18528 -> 13248;
- old PID absent after recovery;
- SCM state returned to Running;
- authenticated runtime.describe before/after reported the same native windows-main-r6-candidate node.

Later repeated faults advanced SCM to its third 60-second recovery action. The final C2 run
therefore also exercised candidate PID 5180 -> 7032 under the longest configured restart delay.

Authority owner:
- Windows SCM owns service failure detection and restart timing.

Fault:
- terminate only the candidate service process, never the live Linux Runtime.

Current candidate SCM recovery policy:
- restart after 5 seconds on the first failure;
- restart after 15 seconds on the second failure;
- restart after 60 seconds on the third and subsequent failures;
- failure counter reset period is 86400 seconds.

Acceptance harness rule:
- the recovery observation window must cover the longest configured SCM delay plus startup/probe margin;
- the current harness uses 90 seconds and records that value in its evidence;
- a fixed 30-second window is invalid because repeated acceptance faults legitimately advance SCM to the 60-second action.

Required evidence:
1. bind candidate PID before the fault;
2. cause an unambiguous non-graceful exit;
3. observe the candidate endpoint become unavailable or service process identity disappear;
4. observe SCM return the service to RUNNING;
5. bind a different process identity after restart;
6. authenticated MCP runtime.describe succeeds from the restarted process.

Acceptance:
- all six observations belong to one causally bound experiment.

Non-evidence:
- a lost external probe Attempt by itself;
- HTTP 401 without proof that a crash actually occurred;
- SCM configuration read-back without failure injection.

## LEGO C2 — active Job reconciliation

Verified on 2026-09-20 against release 00ae7525ff0d444f91f6250d5f055c635c0e092e: **PASS**.

Final authority-correct witness:
- acceptance harness Job job-01a0bd75-b54d-78a2-b6f6-1197f29c0007;
- prepared source created by the real limited service identity;
- target Workspace ws-r6c-native-recovery-1aaa4fb800bd424f;
- target Job job-01a0bd75-b93e-7a91-a921-2887b415179d;
- target Attempt attempt-01a0bd75-b93e-7a91-a921-289b1a392b9b;
- Runtime PID 5180 -> 7032;
- recovery observation window 90s, covering the configured 60s final SCM action;
- target terminal state succeeded, delivery committed;
- stdout R6C_ACTIVE_JOB_DONE;
- exact replay returned the same Job and Attempt identities;
- replaySameJob = true;
- post-fault Doctor Job job-01a0bd77-0258-7153-81ae-77d1d655757a reported
  integrityCheck=ok, violationCount=0, recoveryRequiredAttempts=0, migration 6.

A previous 60-second-window run also proved that the Windows Job Object target completed while
the Runtime service was down, and exact replay later returned the same Job/Attempt. The only
failure in that run was the obsolete fixed 30-second SCM observation timeout.

Authority owner:
- Runtime Registry/Attempt reconciliation owns physical execution truth after restart.

Setup:
- admit one candidate-owned Windows Job whose target remains live long enough to overlap a Runtime
  service crash.

Fault:
- crash the candidate Runtime service process while that Job is nonterminal.

Required evidence:
1. exact Job and Attempt identities are durable before the fault;
2. restart does not create a second Job for the same client request;
3. the surviving/terminated Windows Job Object state is observed by the restarted Runtime;
4. terminal classification is based on durable/native evidence, not guessed from transport loss;
5. global/workspace capacity is released only after terminal evidence is committed;
6. exact request replay returns the same Job identity.

Acceptance:
- no duplicate dispatch and no speculative success/failure classification.

Acceptance-tooling residual, not a C1/C2 blocker:
- two earlier fixture workspaces remain as missing-worktree Registry records:
  ws-r6c-native-recovery-509dae846b9c48b0 and ws-r6c-native-recovery-db1bd49be2f34721;
- workspace.list isolates both as dirty_probe issues because their Git worktree metadata was
  removed when an earlier acceptance fixture source was re-materialized;
- workspace.close(force=true) currently fails before reaching its documented recovered_missing
  disposition because it performs a Git probe against the missing worktree;
- do not repair this by direct SQLite mutation. Fix the generic workspace.close missing-worktree
  reconciliation path in a later Runtime release.

## LEGO C3 — WSL independence

Authority owner:
- Windows SCM / OrdivonRuntimeR6Candidate owns candidate lifecycle and observation;
- the interactive Windows user that owns the Lxss registration owns WSL distribution lifecycle;
- Microsoft wsl.exe remains the mechanism, but it must run under the owning user identity.

Preflight evidence on 2026-09-20:
- archlinux is registered as WSL2 in an interactive-user hive;
- limited candidate service identity can invoke wsl.exe but sees no user-owned running distributions;
- elevated Runtime authority is LocalSystem and direct wsl.exe execution fails with
  WSL_E_LOCAL_SYSTEM_NOT_SUPPORTED;
- therefore neither Runtime service authority is the correct owner for destructive user-WSL
  lifecycle operations;
- frozen C3/C4 preflight v2 digest:
  sha256:d7abdf588bb0efd418c8b311626e6446511bd25169ecb8ae2e7328fb53e8d481.

Precondition:
- observation of windows-main must not depend on a WSL-hosted Windows provider;
- the fault-injection command must run under the interactive user identity that owns archlinux.

Experiment:
1. prove candidate RUNNING and authenticated MCP reachable from the native Windows control plane;
2. under the owning interactive-user authority invoke exact wsl.exe --terminate archlinux;
3. from that same user authority prove archlinux is offline;
4. independently prove candidate SCM state remains RUNNING and authenticated MCP remains reachable;
5. repeat later with wsl.exe --shutdown only after all WSL-dependent work has an explicit
   disposition.

Important:
- terminating WSL can interrupt the current live Linux Runtime and other conversations. Therefore
  C3 destructive execution is deferred until the candidate can become the observation/control
  carrier for the acceptance itself and all active WSL-dependent work has an explicit disposition.

Acceptance:
- Windows-main remains available while WSL is genuinely offline.

## LEGO C4 — cold boot / auto start

Pre-reboot baseline frozen on 2026-09-20 for exact release
00ae7525ff0d444f91f6250d5f055c635c0e092e:
- structured-release receipt digest
  sha256:120eb79f9fe5e8a0dee3206b82f412f8ce8b23a303409ccd5957d98e3fe13360;
- candidate-manifest digest
  sha256:aa998de651709323e7b480f0554257291b7f502f561c338940c01e0b6da40db3;
- preflight v2 evidence digest
  sha256:d7abdf588bb0efd418c8b311626e6446511bd25169ecb8ae2e7328fb53e8d481;
- Windows boot witness 2026-09-20T13:02:10.5000000+08:00;
- Runtime service was Running / Auto with PID 7032 when the baseline was frozen.

This is only the before-reboot side of C4. It does not turn the earlier reboot into an exact-00ae
cold-boot witness because 00ae was deployed after that boot.

Authority owner:
- Windows boot + SCM AUTO_START.

Required evidence:
1. service is configured AUTO_START before reboot;
2. exact candidate artifact/config digests are recorded;
3. after a real Windows reboot, SCM reports a new boot/process identity and RUNNING;
4. MCP runtime.describe reports the same node/config identity;
5. Registry reconciliation completes without duplicate dispatch.

Safety:
- a real reboot is a host-wide destructive operation. It is deferred until active conversations,
  Runtime workspaces and other host workloads have an explicit recovery disposition.

Acceptance:
- no interactive login, WSL startup, Task Scheduler wrapper or manual command is required.

## LEGO C5 — final cutover and carrier deletion

Authority owner:
- release/cutover operation owns the single production transition.

Preconditions:
- C1 and C2 PASS;
- C3 PASS;
- C4 PASS or an explicitly accepted equivalent boot witness;
- production source/main has absorbed the accepted candidate chain without unresolved concurrent
  changes;
- full Windows/Linux regression gates pass on the exact release commit.

Cutover:
1. make accepted native Windows build windows-main;
2. verify production MCP/tool catalog and native node projection;
3. verify Host/clients can reach the new authority;
4. mark WSL-hosted Windows provider unreachable;
5. delete the WSL Windows control-plane carrier, obsolete watchdog/supervisor material and retired
   EF6 workflow artifacts only after claimant checks.

Terminal condition:
- no production semantic depends on the old WSL-hosted Windows control path.

## Dependency graph

C1 crash recovery
       |
       +------+
       |      |
       v      v
C2 reconciliation   C3 WSL independence
       |              |
       +------+-------+
              |
              v
          C4 cold boot
              |
              v
        C5 final cutover
              |
              v
     compatibility deletion

C1 and C2 are now closed by native candidate evidence. C3 and C4 remain deliberately gated
because they can disrupt unrelated active work. Production 8897/windows-main remains untouched.
