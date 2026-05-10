# Red-Team Remediation Plan — 2026-05-10

> **This is a plan, not a receipt.** No implementation has been executed.
> All findings are classified, scoped, and prioritized. Awaiting execution.

**Authority**: `proposal`
**Status**: `proposed`
**Phase**: `CI-SelfCalibration`
**Owner**: `ordivon-core-maintainer`
**Derived from**: Red-team audit Round 1 (10 probes) + Round 2 (3 deep exploits)
**Debt refs**: DEP-REDTEAM-RT09-DEBT-INTEGRITY, DEP-REDTEAM-RT11-CHECKER-INTEGRITY

---

## 1. Freeze Reality — What the Audit Found

```
Round 1: 10 probes across 9 attack surfaces
  ✓ 7 resisted attack
  ⚠ 3 warnings (low severity)
  ✗ 0 bypasses (RT-02 was false alarm — bad test payload)

Round 2: 3 deep exploits on confirmed gaps
  ⚠ 1 warning (Debt suppression — WARNING, not blockable by current checkers)
  ✗ 1 bypass (Checker blind spot — exclusion list modification succeeded)
  ⚠ 1 warning (Schema self-validation — low severity)

Confirmed gaps: 2 HIGH severity
  RT-09: Debt JSONL has no entry-level integrity protection
  RT-11: Checker source can be modified to create blind spots
```

### What Resisted Attack (evidence of system strength)

```
Registration gate      — adding unregistered file → BLOCKED by atomic-governance
Generated view verify  — poisoning _registry-stats.md → DRIFT DETECTED by --check
Registry corruption     — invalid doc_type/authority → caught by ordivon-verify
Dual-checker sync       — schema-first prevents desync (single source)
Safe-context resistance — agentic patterns still fire despite safe words on same line
False READY detection   — freshness + truth protocol warn on doc mutation
Exclusion collision     — exact paths, no glob abuse possible
```

---

## 2. Gap Classification

### RT-09: Debt Ledger Entry Integrity (HIGH)

```
What: Changing debt status OPEN→CLOSED with no evidence
      ordivon-verify did NOT block — verification-debt checker
      validates ledger structure, not entry-level integrity.

Attack chain:
  1. Open debt JSONL file
  2. Change "status": "OPEN" → "status": "CLOSED"  
  3. Add vague "resolution": "resolved by system update"
  4. Save
  5. ordivon-verify → READY (no detection)

Root cause: JSONL ledgers are plain text. No checksum, no audit
trail per entry, no signature. The verification-debt checker
verifies the ledger EXISTS and has valid STRUCTURE, but not
that individual entries haven't been tampered with.

Disposition: A3 — System redesign needed.
  Not A1 (can't just "fix the data" — need mechanism)
  Not A2 (can't just "refine the checker" — checker has no
         way to verify entry integrity without a baseline)
  Not A4 (should not be deferred — this is a real gap now)

Threat model: Attacker with repo write access can close debts
silently. CI will not detect. Reviewers may not notice a
single-field change in a JSONL diff.
```

### RT-11: Checker Source Blind Spot (HIGH)

```
What: Adding an entry to GOVERNED_EXCLUSIONS in
      scripts/check_atomic_governance.py successfully hid
      an unregistered file from detection.

Attack chain:
  1. Open checker source file
  2. Add file path to GOVERNED_EXCLUSIONS dict
  3. Create unregistered file at that path
  4. Atomic governance gate → PASS (file excluded from scan)
  5. ordivon-verify → READY

Root cause: Checker Python source code has no integrity
verification. Authority sets (GOVERNED_EXCLUSIONS, SAFE_FILES,
SCAN_EXCLUDE_PREFIXES) are inline constants in Python files.
Modifying them is a git-tracked change, but no automated CI job
verifies that these sets haven't been expanded to create blind spots.

Disposition: A3 — System redesign.
  A2 (refine checker): Add a self-check that verifies exclusion
    lists haven't grown beyond a known baseline. This catches
    the attack but doesn't prevent the class of attack.
  A3 (redesign): Extract authority sets (exclusions, safe files,
    scan exclude prefixes) to governed JSON schemas, similar to
    what was done for VALID_DOC_TYPES → document-types.json.
    Then add integrity verification on those schemas.
```

### RT-03: Schema Self-Validation (LOW)

```
What: document-types.json accepts empty string, whitespace-only,
      and nonsense values as valid doc_types.

Severity: LOW — no registered entries currently use these bogus
types, and adding one would require a registry modification
that is git-tracked and reviewable.

Disposition: A2 — Add JSON Schema validation or Python-level
  guard that rejects empty/whitespace-only doc_type values.
  This is a defense-in-depth improvement, not an urgent fix.
```

---

## 3. Remediation Sequence

### Wave 1: Checker Integrity (RT-11 → A3)

```
Step 1: Extract all authority sets from checker Python files
  to governed schemas:

  scripts/check_atomic_governance.py:
    GOVERNED_EXCLUSIONS → docs/governance/schemas/governed-exclusions.json

  checkers/agentic-patterns/run.py:
    SAFE_FILES → docs/governance/schemas/agentic-safe-files.json

  checkers/protected-paths/run.py:
    SAFE_FILES → docs/governance/schemas/protected-safe-files.json
    SCAN_EXCLUDE_PREFIXES → docs/governance/schemas/scan-excludes.json

Step 2: Add schema integrity verification to governance-self-check CI job:
  - Each schema file must be valid JSON
  - Each schema file must have a known baseline (checksum or git-based)
  - New entries require explicit approval (detected as "schema growth")

Step 3: Checkers load from schemas instead of inline constants
  (Same pattern as VALID_DOC_TYPES → document-types.json)

Step 4: CI verifies checker integrity:
  - All authority sets match their schemas
  - No checker has inline constants that duplicate schema content

Verification:
  - Modify exclusion in schema → CI detects schema change
  - Modify checker to bypass schema → CI detects checker-schema mismatch
  - Modify both in same commit → git diff is reviewable
```

### Wave 2: Debt Integrity (RT-09 → A3)

```
Step 1: Add per-entry content hash to debt JSONL:
  Each entry gets a "content_hash" field computed from
  the entry's key fields (debt_id, status, description,
  resolution if present).

Step 2: Add CI job that verifies debt hashes:
  - Recompute hash for each entry
  - Compare with stored hash
  - BLOCK if any hash mismatch

Step 3: Extend to lesson-ledger.jsonl (same vulnerability class)

Step 4: Document that this provides tamper-EVIDENCE, not tamper-PROOF.
  An attacker with repo write access can recompute the hash.
  The defense is that the hash change itself is detectable in git diff.
  Combined with CI verification, this creates a two-layer defense.

Verification:
  - Modify debt status → hash mismatch → CI BLOCKED
  - Modify debt status + recompute hash → git diff shows both changes
```

### Wave 3: Schema Hardening (RT-03 → A2)

```
Step 1: Add value validation to document-types.json schema loading:
  - Reject empty strings
  - Reject whitespace-only strings  
  - Reject strings matching common injection patterns (<, >, ', ", --)

Step 2: Add to _load_valid_doc_types() in both checkers
  (automatically applied since both load from schema)

Verification:
  - Add "" to schema → checker rejects it
  - Add "   " to schema → checker rejects it
```

---

## 4. Scope Boundaries

```
What this plan covers:
  ✓ RT-09 (debt integrity), RT-11 (checker integrity), RT-03 (schema validation)

What this plan does NOT cover:
  ✗ Git-level security (repo write access is the trust boundary)
  ✗ Supply chain attacks (dependency verification)
  ✗ Infrastructure security (CI runner integrity)
  ✗ Human review process (PR review is assumed to work)

What is out of scope for now:
  - RT-06 (exclusion list modification via git — covered by RT-11 fix)
  - Full content-addressable storage for all governance artifacts
  - Cryptographic signatures on JSONL entries
  - External audit trail system

Assumption: Attacker has repo write access (can push commits).
  At this trust level, the defense is: make tampering DETECTABLE,
  not impossible. Git history + CI gates + human review together
  create a multi-layer defense.
```

---

## 5. Execution Order

```
1. RT-11 (checker integrity)    ← Blocks the biggest attack surface
   Extract authority sets to schemas
   Add schema integrity CI check

2. RT-09 (debt integrity)       ← Second priority
   Add content hashes to debt/lesson ledgers
   Add hash verification CI check

3. RT-03 (schema validation)    ← Low priority, defense-in-depth
   Add value validation to schema loader
```

---

## 6. READY Disclaimer

```text
This is a plan, not a receipt. No implementation has been executed.
All gaps remain OPEN until the corresponding debt entries are CLOSED
with evidence. READY (if achieved after implementation) does not
authorize merging, deployment, or release.
```
