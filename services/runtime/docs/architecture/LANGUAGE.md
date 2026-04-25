# Ordivon Architecture Language

This is the shared vocabulary for all Ordivon/PFIOS architecture discussions,
audits, and refactoring proposals.  Every recommendation must be expressible
in these terms.  Generic words below are **banned from architecture output**
so the AI cannot hide behind vagueness.

---

## Generic Architecture Terms

| Term | Definition |
|------|------------|
| **Module** | A self-contained unit of code with a clear responsibility. Must be deletable without cascading breakage. |
| **Interface** | The contract a module exposes to callers. Defined by function signatures, not by class hierarchies. |
| **Implementation** | The code behind an interface. May be swapped without changing callers. |
| **Seam** | A point where two modules meet. Every seam is a place where behaviour can be replaced or tested in isolation. |
| **Internal Seam** | A seam inside a single deployment unit — e.g. passing a function reference instead of importing it. Testable without network or filesystem. |
| **External Seam** | A seam that crosses a process or network boundary — e.g. HTTP, database, filesystem. Requires integration testing. |
| **Adapter** | Code that translates between two interfaces. An adapter owns the translation; neither side knows about the other. |
| **Depth** | How many modules a piece of code depends on transitively. Lower depth = easier to test and delete. |
| **Leverage** | How many callers a module serves. High-leverage modules (e.g. Repository base class) must be more carefully tested. |
| **Locality** | Whether related code lives together. High locality = the thing you need to change is in one file, not scattered across five modules. |
| **Caller** | Code that invokes a function or method. The caller defines the context; the callee defines the contract. |
| **Call Site** | The exact line where a function is called. Each call site is a decision about what behaviour to invoke. |
| **Test Surface** | The set of seams a test exercises. A small test surface means fewer mocks and faster feedback. |
| **Variation** | A point where behaviour differs based on context (env, feature flag, runtime config). Every variation must be testable at its seam. |
| **Pass-through** | Code that does nothing but delegate to another module. Often a sign that two modules should be one. |
| **Deletion Test** | If you delete this module, what breaks? If the answer is "nothing I care about", the module is dead weight. |

---

## Ordivon-Specific Terms

| Term | Definition |
|------|------------|
| **Truth Source** | The single authoritative store for a domain entity. In Ordivon, this is always a SQLAlchemy ORM table, never DuckDB or a cache. |
| **Evidence** | Raw data (market quotes, model output, user feedback) before it enters governance. Evidence is not a decision. |
| **Receipt** | An immutable record that a governed action was attempted. Receipts are append-only. ExecutionReceipt is the canonical type. |
| **Governance** | The rule engine that gates every action. Governance reads Evidence, consults Policies, and emits a Decision. It does not execute. |
| **Hard Gate** | A governance decision that cannot be overridden by the caller. `deny` is a hard gate; `escalate` is a soft gate. |
| **State Machine** | An explicit, finite set of status transitions a domain entity may undergo. No transition is valid unless the machine permits it. |
| **Review** | A human or automated post-hoc assessment of a Recommendation's outcome. Reviews generate Lessons and Candidate Rules. |
| **Lesson** | A durable insight extracted from a Review. Lessons are stored facts, not executable policy. |
| **Knowledge Feedback** | The mechanism that delivers Lessons from past Reviews into future Analysis tasks. Read-only in the analysis path. |
| **Candidate Rule** | A proposed Policy derived from Lessons. Candidate Rules require explicit adoption before becoming active Policy. |
| **Policy** | An active governance rule. Policies are versioned and immutable once published. |
| **Pack** | A self-contained domain bundle (e.g. `packs/finance/`) that delivers a complete vertical slice: models + policies + tool refs + defaults. |
| **Harness** | The external runtime that executes model inference. Ordivon owns one harness at a time. Currently: the Hermes Bridge. |
| **Brain Runtime** | The Ordivon-side adapter that talks to the Harness. HermesRuntime is the current implementation. |
| **Harness Adapter** | The code that translates Ordivon task contracts into harness-specific protocol. `HermesClient` is the current adapter. |
| **Bridge** | The controlled HTTP service that wraps an external model API. The Bridge enforces safety invariants (no tools, no shell, no file write) that the harness adapter trusts. |

---

## Banned Architecture Words

These words are **not** banned from code or filenames.  They are banned from
**architecture audit output and refactoring recommendations** because they
are too vague to carry meaning.

| Banned Word | Why |
|-------------|-----|
| component | Means anything. Use Module, Seam, or Adapter. |
| service | Means anything. Use Module, Adapter, or Truth Source. |
| API | Too broad. Use Interface, Call Site, or External Seam. |
| boundary | Too vague. Use Seam (internal/external) or Hard Gate. |
| unit | Means nothing. Use Module or Test Surface. |
| manager | Means nothing. Use Repository, State Machine, or Adapter. |
| handler | Means nothing. Use Adapter or Implementation. |
| processor | Means nothing. Use Implementation or Pass-through. |
| engine | Means nothing. Use State Machine or Implementation. |
| platform | Too big. Use Module or Harness. |
| OS | Marketing. Use Module or Truth Source. |
| agent | Overloaded. Use Harness, Brain Runtime, or Bridge. |
| business logic | Means "I haven't identified the seam." Use Implementation or State Machine. |
