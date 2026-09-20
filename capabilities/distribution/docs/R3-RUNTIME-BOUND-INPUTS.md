# Distribution v2 R3 — Runtime-Bound Evidence Inputs

R3 does not add a Distribution-specific resolver to Runtime. It consumes the mature Runtime `workspace.execBound` contract instead.

The Runtime operator configuration now includes a dedicated named InputAuthority `distribution-r3-evidence` rooted at `/var/lib/ordivon/distribution-input-authorities/r3`. Callers cannot select arbitrary host paths through this interface; they name the authority, one relative object, its expected SHA-256 digest, and its presentation-relative path. Runtime freezes exact bytes into Job-owned input state and presents them read-only under `ORDIVON_INPUT_ROOT`.

`scripts/admission_bound.py` therefore refuses to run without `ORDIVON_INPUT_ROOT` and accepts provider/effect-authority evidence only by relative path beneath that Runtime-provided input root. The Workspace intent and code remain separately source-state-bound by Runtime admission.

This closes the R2 gap where a controller could merely type a `sourceRef` string into an envelope. It still does not make Runtime the semantic authority for provider capability or user consent: the named authority root is only a physical provenance boundary. Future producer workflows must decide which provider observation or effect-authority objects are admissible into that root.
