# Provider: Network v2

- Source repository: `/root/projects/ordivon`\n- Owner path: `platform/network`
- Observed monorepo revision: `dac057c6668c83e085bb3ae3b910866fd349b4eb`
- Current standing: `LOCAL_WSL_GRADUATED`; independent standard-Linux reference lane graduated
- Role: network composition and verification capability provider
- Migration mode: canonical modular-monorepo owner; legacy standalone carrier is retirement-only

## Capability model

`Requirement -> classify network problem -> select mature mechanism -> compose isolated realization -> falsify failure modes -> emit evidence`

Current provider composes mature DNS/proxy/tunnel/probe/telemetry mechanisms rather than implementing a new network stack.

## Important boundary

Network capability does not own consumer business policy, application retries, consumer cutover, Runtime management ingress, or Windows/WSL bootstrap.

## Activation

Load when a real task needs network reachability, path selection, isolation, tunnel/proxy composition, network fault testing or corresponding evidence.
