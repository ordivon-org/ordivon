# Chaoxing Auto-Sign Assistant R2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or execute inline with the same RED→GREEN→REFACTOR and verification gates. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current MVP into a crash-safe, test-discoverable, current read-side-capable Chaoxing monitoring assistant with durable identity/session/activity state and explicit safe execution boundaries.

**Architecture:** Keep the existing ports-and-adapters core. First harden recovery/idempotence so an interrupted submission is verified before any retry. Then add a real Chaoxing HTTP read client implementing both SessionPort and DiscoveryPort over a shared `requests.Session`, with domain-session probing, course/class normalization, and active-activity normalization. Keep submission as a separate adapter; no location/QR/face/presence-proof spoofing is introduced.

**Tech Stack:** Python 3.11+, sqlite3, unittest, requests>=2.31.0, pycryptodome>=3.19.0. No GUI dependency in the daemon/core path.

**Spec:** `experiments/chaoxing-autosign-mvp/README.md` plus the normalized lifecycle in `knowledge/lessons/chaoxing-source-map-evolution-r2.md`.

## Global Constraints

- Use Ordivon Skill MCP Superpowers workflow.
- Every new behavior or bug fix follows RED → verify RED → minimal GREEN → verify GREEN → refactor.
- No completion claim without a fresh full verification run.
- Preserve `account_id + course_id + class_id + activity_id` as the durable logical activity key; acquisition surface remains metadata/provenance, not a reason to duplicate one logical activity.
- Never automatically resubmit an activity whose prior external-effect outcome is uncertain; verify first.
- Unknown activity kinds fail closed.
- Location, QR, face/photo and other presence-proof requirements remain `USER_VERIFICATION_REQUIRED`.
- Credentials are never committed to Git. Runtime configuration comes from environment/secret material.
- Real network tests are opt-in; default test suite is deterministic and offline.

---

## File Structure

- `experiments/chaoxing-autosign-mvp/chaoxing_mvp/models.py` — domain enums/value objects and result invariants.
- `experiments/chaoxing-autosign-mvp/chaoxing_mvp/ledger.py` — SQLite activity ledger and recovery state.
- `experiments/chaoxing-autosign-mvp/chaoxing_mvp/engine.py` — scan/process/recovery orchestration.
- `experiments/chaoxing-autosign-mvp/chaoxing_mvp/chaoxing_http.py` — real read-side session/course/activity adapter.
- `experiments/chaoxing-autosign-mvp/chaoxing_mvp/config.py` — environment configuration without storing secrets in repo files.
- `experiments/chaoxing-autosign-mvp/chaoxing_mvp/runner.py` — monitor/backoff lifecycle.
- `tests/test_chaoxing_autosign_mvp.py` — core/recovery tests.
- `tests/test_chaoxing_http_adapter.py` — HTTP adapter contract tests using fake response/session objects.
- `tests/__init__.py` — make root `unittest discover` recurse into tests.
- `experiments/chaoxing-autosign-mvp/requirements.txt` — runtime network dependencies only.

---

### Task 1: Make the repository's default test command truthful

**Files:**
- Create: `tests/__init__.py`
- Test: repository root discovery itself

**Interfaces:**
- Consumes: existing `tests/test_*.py` files.
- Produces: `python -m unittest discover -v` finds the same suite as `python -m unittest discover -s tests -v`.

- [ ] **Step 1: Verify the current failure**

Run:
```bash
python -m unittest discover -v
```
Expected current result: exit 5, `Ran 0 tests`.

- [ ] **Step 2: Minimal fix**

Create an empty `tests/__init__.py` so unittest recursively imports the directory as a package.

- [ ] **Step 3: Verify**

Run both:
```bash
python -m unittest discover -v
python -m unittest discover -s tests -v
```
Expected: both commands discover and pass the same test count.

- [ ] **Step 4: Commit**

```bash
git add tests/__init__.py
git commit -m "test: make root unittest discovery recurse"
```

---

### Task 2: Prevent duplicate submission after crash or uncertain delivery

**Files:**
- Modify: `tests/test_chaoxing_autosign_mvp.py`
- Modify: `experiments/chaoxing-autosign-mvp/chaoxing_mvp/ledger.py`
- Modify: `experiments/chaoxing-autosign-mvp/chaoxing_mvp/engine.py`

**Interfaces:**
- Consumes: `SubmissionPort.verify(ActivityIdentity) -> bool | None`.
- Produces: recovery-first processing for states `SUBMITTING`, `SUBMITTED`, `VERIFYING`, `UNKNOWN`.

- [ ] **Step 1: RED — write regression test for crash after external effect**

Add a submission adapter whose first `submit()` records the activity and raises a synthetic process/interruption exception before the engine can write `SUBMITTED`. Persist ledger state as `SUBMITTING`, instantiate a fresh engine over the same SQLite DB, then scan again. Assert `verify()` is called and `submit()` is **not** called a second time when verify returns True.

- [ ] **Step 2: Verify RED**

Run:
```bash
python -m unittest tests.test_chaoxing_autosign_mvp.ChaoxingAutoSignMvpTests.test_recovery_verifies_submitting_before_resubmit -v
```
Expected: FAIL because current engine re-enters `_process()` and calls submit again.

- [ ] **Step 3: GREEN — add recovery routing**

Add ledger helper:
```python
def recovery_required(self, identity: ActivityIdentity) -> bool:
    return self.get(identity).state in {
        ActivityState.SUBMITTING,
        ActivityState.SUBMITTED,
        ActivityState.VERIFYING,
        ActivityState.UNKNOWN,
    }
```

Add engine path before planning/submission:
```python
if self.ledger.recovery_required(activity.identity):
    self._recover_uncertain(activity, stats)
    return
```

`_recover_uncertain()` must call `verify()` first:
- True -> `CONFIRMED_SUCCESS`, never resubmit.
- False -> transition to `FAILED_RETRYABLE`; a later scan may retry.
- None -> remain `UNKNOWN`, notify once per state transition, never resubmit in that scan.

- [ ] **Step 4: RED/GREEN — add tests for verify False and None**

Tests must prove:
- False does not submit during the recovery scan and becomes retryable.
- None does not submit and remains unknown.

- [ ] **Step 5: Verify full core tests**

```bash
python -m unittest tests.test_chaoxing_autosign_mvp -v
```

- [ ] **Step 6: Commit**

```bash
git add tests/test_chaoxing_autosign_mvp.py experiments/chaoxing-autosign-mvp/chaoxing_mvp/{ledger.py,engine.py}
git commit -m "fix: verify uncertain sign attempts before retry"
```

---

### Task 3: Enforce result-state consistency

**Files:**
- Modify: `tests/test_chaoxing_autosign_mvp.py`
- Modify: `experiments/chaoxing-autosign-mvp/chaoxing_mvp/models.py`
- Modify: `experiments/chaoxing-autosign-mvp/chaoxing_mvp/engine.py`

**Interfaces:**
- Produces: semantic rejection is only trusted when the response parsed successfully; inconsistent result objects cannot accidentally cause terminal failure.

- [ ] **Step 1: RED**

Add test: `transport=OK`, `parse=FAILED`, `semantic=REJECTED` must not become `FAILED_TERMINAL`; expected `UNKNOWN`/retryable interpretation.

- [ ] **Step 2: Verify RED**

Current code checks `semantic REJECTED` before parse validity, so expected FAIL.

- [ ] **Step 3: GREEN**

Change decision order:
1. transport must be OK;
2. parse must be OK;
3. semantic accepted/rejected/ambiguous is interpreted only after parse success.

- [ ] **Step 4: Verify full core tests and commit**

---

### Task 4: Add real Chaoxing read-side HTTP adapter, test-first

**Files:**
- Create: `experiments/chaoxing-autosign-mvp/chaoxing_mvp/chaoxing_http.py`
- Create: `tests/test_chaoxing_http_adapter.py`
- Create: `experiments/chaoxing-autosign-mvp/requirements.txt`

**Interfaces:**
- Class: `ChaoxingReadClient(username: str, password: str, *, session=None, timeout_seconds: float = 10.0)`
- Implements:
```python
def ensure_domain_session(self) -> str
def list_courses(self, account_id: str) -> Sequence[CourseIdentity]
def list_active_activities(self, course: CourseIdentity) -> Sequence[Activity]
```
- Shared underlying `requests.Session`.

- [ ] **Step 1: RED — AES credential transform fixture**

Use a fixed local plaintext fixture and assert deterministic AES-CBC/base64 output using the currently observed key convention. No credentials from the user are stored.

- [ ] **Step 2: GREEN — `_encrypt_login_field`**

Use PyCryptodome (`Crypto.Cipher.AES`, `Crypto.Util.Padding.pad`), not a hand-written cipher.

- [ ] **Step 3: RED — login response contract**

Fake session sequence:
1. GET login bootstrap;
2. POST login returns `{status: true, url: ...}`;
3. redirect establishes `_uid` cookie;
4. domain probe returns a parseable course payload.

Assert `ensure_domain_session()` returns `_uid` only after the domain probe succeeds.

- [ ] **Step 4: GREEN — session bootstrap/login/domain probe**

Use timeouts on every request. Raise typed adapter errors for transport, login rejection, parse failure, missing `_uid`, and domain-probe failure.

- [ ] **Step 5: RED/GREEN — course normalization**

Fixture includes valid channels plus malformed/empty entries. Expected output preserves both `course_id` and `class_id`; malformed rows are skipped deterministically rather than crashing the entire scan.

- [ ] **Step 6: RED/GREEN — activity normalization**

Fixture includes active, expired and malformed activities. Normalize to `Activity` with:
- `activity_id`
- course/class identity
- raw upstream type in metadata
- end time
- user status
- acquisition surface `chaoxing-mobilelearn-v2`

Unknown upstream type maps to `ActivityKind.UNKNOWN` until independently classified. Do not guess presence-proof requirements from unsupported constants.

- [ ] **Step 7: Verify adapter tests**

```bash
python -m unittest tests.test_chaoxing_http_adapter -v
```

- [ ] **Step 8: Commit**

---

### Task 5: Add environment configuration and real monitor assembly

**Files:**
- Create: `experiments/chaoxing-autosign-mvp/chaoxing_mvp/config.py`
- Modify: `experiments/chaoxing-autosign-mvp/chaoxing_mvp/cli.py`
- Modify: `experiments/chaoxing-autosign-mvp/README.md`
- Modify: tests as needed

**Interfaces:**
- Environment variables:
  - `CX_USERNAME`
  - `CX_PASSWORD`
  - `CX_LEDGER_PATH`
  - `CX_POLL_SECONDS`
  - `CX_JITTER_SECONDS`
- No plaintext credential file is generated by the MVP.

- [ ] **Step 1: RED — config validation**

Missing username/password -> explicit configuration error before any network request.
Invalid numeric values -> explicit error.

- [ ] **Step 2: GREEN — immutable config object**

Create `AppConfig.from_env(mapping=os.environ)` for testability.

- [ ] **Step 3: RED/GREEN — CLI assembly**

Add `demo` and `monitor` subcommands. `monitor` wires one `ChaoxingReadClient` instance as both session and discovery ports, `DisabledSubmissionAdapter` by default, SQLite ledger and `MonitorRunner`.

- [ ] **Step 4: Verify**

`demo` must remain offline. `monitor --dry-run` must validate configuration and assemble without sending submission requests.

---

### Task 6: Review, full verification and integration gate

**Files:**
- Possibly modify based on review findings only through new RED/GREEN cycles.

**Interfaces:** none; this is a gate.

- [ ] **Step 1: Fresh full test run**

```bash
python -m unittest discover -v
```
Expected: all repository tests discovered, zero failures/errors.

- [ ] **Step 2: Compile check**

```bash
python -m compileall -q experiments/chaoxing-autosign-mvp tests
```
Expected exit 0.

- [ ] **Step 3: Synthetic E2E**

```bash
PYTHONPATH=experiments/chaoxing-autosign-mvp python -m chaoxing_mvp.cli demo
```
Expected: normal synthetic activity confirms; QR activity routes to user verification; no live request.

- [ ] **Step 4: Crash-recovery E2E test**

Run the dedicated recovery test twice against a temporary persistent SQLite ledger and verify the submission count remains one when remote verification reports success.

- [ ] **Step 5: Code review**

Review diff from the task base SHA through current HEAD for Critical/Important issues: duplicate external effects, session false-positive, identity collapse, secret persistence, missing timeouts, swallowed parse failures, and test holes. Any Important finding requires a failing regression test before fix.

- [ ] **Step 6: Git clean/status and final commit**

Only after Steps 1-5 provide fresh evidence.

---

## Self-Review

- Spec coverage: crash-safe recovery, current read-side session/course/activity discovery, identity, backoff, safe submit boundary, secrets and verification are all assigned to tasks.
- Placeholder scan: no TBD/TODO/"handle errors later" steps.
- Type consistency: `ChaoxingReadClient` implements the existing `SessionPort` and `DiscoveryPort`; engine/ledger interfaces remain stable except explicit recovery helpers.
- Scope: live presence-proof bypass work is excluded; read-side monitoring and ordinary authorized execution remain separable.
