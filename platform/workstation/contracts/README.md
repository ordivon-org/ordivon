# Standards-first contracts

This directory contains interoperability contracts, not a new Ordivon middleware product.

- **CloudEvents 1.0** is the event envelope at integration boundaries. An envelope claim is distinct from a specific HTTP binding/media type; adapters must state which binding they actually validate.
- **AsyncAPI 3.0** describes asynchronous producer/consumer contracts without requiring Kafka/NATS.
- **OpenAPI** remains the contract format for synchronous HTTP APIs when a real API exists; no placeholder API is invented here.
- **Transactional Outbox** is a per-domain persistence pattern. A domain commits its state change and outbox record in the same PostgreSQL transaction, then a relay/integration edge publishes it. Consumers remain idempotent.
- **Temporal Nexus** is preferred for durable application-to-application operations where both sides are Temporal applications.
- **OpenTelemetry** owns telemetry semantics and propagation.

Authority rule: contracts standardize transport/interoperability; they do not grant domain permission or external-effect authority.
