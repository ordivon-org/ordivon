# Adapters

Adapters are thin translation/integration edges to mature external systems.

Rules:

- no adapter may silently become a second implementation of its upstream system;
- adapter contracts should be capability-oriented rather than tool-identity-oriented where practical;
- preserve upstream authority for generic state and lifecycle;
- isolate tool-specific details from domain profiles;
- deletion/replacement of an adapter should not change the domain ontology.

Expected families may include MCP/native tool adapters, workflow adapters, observability/provenance adapters and domain-validator adapters.
