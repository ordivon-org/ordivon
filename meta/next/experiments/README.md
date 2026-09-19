# Experiments

This directory contains bounded experiment implementations and frozen protocol artifacts. It is not a general runtime or provider layer.

Experiment files may intentionally bind exact tool versions, executable paths, source digests, presentation material, or other environmental coordinates when those coordinates are part of the recorded experimental condition. Do not silently "modernize" such a file if its bytes or dependencies participate in a frozen protocol identity.

Use these rules:

- active experiment code should prefer repository-declared dependencies and explicit provider bindings;
- frozen protocol/reference implementations preserve their recorded bytes and environment assumptions unless a new protocol revision is intentionally created;
- a failed self-digest after editing is evidence that the file belongs to the frozen experimental subject, not a reason to update the digest in place;
- new experiments should separate reusable current tooling from frozen subject material where practical;
- experiment outputs belong under evidence only as point-in-time observations and must not become current runtime configuration.

When an old frozen experiment needs to be rerun under a different environment, create a new protocol/revision or an external compatibility execution environment. Do not mutate the historical subject merely to make it convenient on the current machine.
