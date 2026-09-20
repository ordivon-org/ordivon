# n8n integration service authority

## Ownership

- **Operations v2** owns the n8n service desired state: the official OCI image digests, rootless Podman/Quadlet lifecycle, dedicated service identity, PostgreSQL consumer admission, rootless Podman secrets, and local exposure boundary.
- **Workstation v2** may materialize an n8n CLI for operator convenience, but that host-native package is not the service runtime authority.
- PostgreSQL cluster and backup ownership remains the shared Operations PostgreSQL substrate. n8n owns only its dedicated role/database contents.
- Temporal remains the durable multi-stage workflow authority. n8n is the external application/API integration plane, not a Temporal or Runtime replacement.
- Ordivon Runtime remains the authority for local physical execution evidence.

## Runtime topology

The production-style local service is rootless and containerized:

```text
systemd --user (n8n, linger)
        |
        +-- ordivon-n8n-pod.service
              |
              +-- ordivon-n8n.service
              |     official n8n image, digest pinned
              |
              +-- ordivon-n8n-runners.service
                    official distroless runner image, digest pinned
```

The Pod uses rootless `pasta` with a deterministic private network. Only `127.0.0.1:5678` is published to the host. The task broker (5679) and runner launcher (5680) remain private in the shared Pod network namespace.

The container gateway `10.89.10.1` is mapped by pasta to host loopback, allowing the n8n container to reach PostgreSQL at `127.0.0.1:55434` without exposing PostgreSQL beyond host loopback.

## Pinned images

- n8n 2.36.7 main image: `ghcr.io/n8n-io/n8n@sha256:770da605a7dfdda55838fb2b66b701435690ffcce5d3067585fc7e3cb17b168f`
- n8n 2.36.7 distroless runners: `ghcr.io/n8n-io/runners@sha256:f171bd9b3bb8e4668f2ec4293307043987140b26ebc2f7d8ec81b6738953a7e1`

Both use `Pull=never` at service start. Ansible pulls an exact digest only when it is absent from the dedicated n8n rootless image store.

## Secret state

`/etc/n8n/n8n-secrets.env` is the root-only durable recovery source (`root:root`, `0600`). It contains:

- PostgreSQL password;
- n8n credential-encryption key;
- external task-runner authentication token.

Ansible admits those values into three rootless Podman secrets. Non-secret container settings live in `/etc/n8n/n8n-container.env`, intentionally separate from the legacy host-native `/etc/n8n/n8n.env` so a failed first cutover can restore the old service without consuming container-only addresses. The main container receives all three. The runner receives only its runner-auth token. The root-only recovery source is never mounted into either container.

The n8n database and `N8N_ENCRYPTION_KEY` form one recovery domain: restoring the database without the matching encryption key does not restore encrypted n8n credentials.

## PostgreSQL

- database: `n8n`
- role: `n8n`
- role is non-superuser, cannot create roles/databases, and cannot bypass RLS;
- authentication is SCRAM-SHA-256;
- PostgreSQL remains bound to `127.0.0.1:55434` plus its pre-existing Unix socket.

## Apply

```bash
ansible-playbook -i ansible/inventory.ini ansible/n8n.yml --syntax-check
ansible-playbook -i ansible/inventory.ini ansible/n8n.yml
```

The playbook performs a bounded cutover from the deprecated host-native service. The official image runs with a read-only root filesystem; only persistent `/home/node/.n8n` and an ephemeral tmpfs at `/home/node/.cache` are writable. If the first rootless readiness check fails, it stops the failed Pod and restores the legacy service when that service was active before cutover. After successful readiness, the legacy system unit is disabled and removed.

## Acceptance

A completed cut requires all of the following on the same node:

1. `ordivon-n8n-pod.service`, `ordivon-n8n.service`, and `ordivon-n8n-runners.service` are active in the `n8n` user manager.
2. Rootless Podman runs the exact pinned main and distroless runner images.
3. `http://127.0.0.1:5678/healthz` returns HTTP 200.
4. `http://127.0.0.1:5678/healthz/readiness` returns HTTP 200, proving database-aware readiness.
5. Host port 5678 is bound only to `127.0.0.1`; 5679 and 5680 have no host listener.
6. Runner launcher health is reachable from the main container over pod-private loopback.
7. The main container can reach an external HTTPS API through rootless pasta networking.
8. PostgreSQL remains loopback-only and its original Unix socket remains alive.
9. `pgBackRest check` remains healthy after cutover.
10. A second Ansible apply is idempotent and does not rotate secrets or restart PostgreSQL without a setting change.

`scripts/verify-n8n-rootless.sh` performs the local runtime acceptance probes.

## Ordivon integration boundary

n8n is a **replaceable integration provider**, not an Ordivon semantic authority. E2Es should not embed n8n workflow IDs or node IDs into domain contracts. The next integration layer should expose provider-neutral invocation/status/result identities, with Temporal owning durable orchestration and Runtime owning local execution evidence.
