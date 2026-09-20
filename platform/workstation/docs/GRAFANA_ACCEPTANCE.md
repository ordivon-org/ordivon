# Grafana visualization acceptance

Date: 2026-09-12

## Standing

**OFFICIAL OCI GRAFANA ACCEPTED FOR PROMETHEUS + LOKI VISUALIZATION.**

Operations uses Grafana only as a visualization/query surface. Prometheus remains metrics authority and Loki remains log authority.

## Why the Arch package was retired

The installed Arch `grafana 13.2.1-1` binary could start and could provision the two declared datasources, but real datasource-proxy queries to both Prometheus and Loki returned HTTP 404 with `Unable to find datasource plugin`. The packaged service therefore did not satisfy the required visualization contract.

Operations did not patch Grafana internals, copy plugin files, or add a custom proxy.

## Accepted external component

The accepted image is the official Grafana 13.2.1 OCI image pinned by digest:

`docker.io/grafana/grafana@sha256:1dec240d14e232597dce9bfa56dae55f4397b138cdc91e3ee92ac6b157e2fc49`

Local image evidence:

- image ID: `8400f365c39767b0d0df30e3aeb0796f873c3acf89b28089745bfafd88d83c7c`;
- configured image user: `472`;
- runtime identity probe: `uid=472(grafana) gid=0(root)`.

## Acquisition path

Direct Docker Hub access from the host timed out. The image was acquired without changing ambient Runtime/Temporal routing:

1. Network v2 VPN carriers were probed from their existing network namespaces.
2. `surfpath-5779-177` returned a valid Docker Registry `401` challenge and sustained about 1.63 MB/s in a bounded transfer probe; the active OpenVPN carrier measured about 0.22 MB/s.
3. A temporary CONNECT bridge carried only the image-pull HTTPS flow through `surfpath-5779-177`. TLS remained end-to-end to Docker Hub.
4. Podman itself remained in the host namespace so its storage/cgroup semantics did not move into the VPN namespace.
5. The pull ran as a transient systemd service because Podman's overlay mount activity correctly conflicts with Runtime's executable path-topology witness when run directly under a Runtime Attempt.
6. The transient VPN bridge was removed after the pull.

The VPN carrier is therefore an acquisition transport, not a new Grafana runtime dependency.

## Isolated official-image E2E

Before production cutover the official digest was run on loopback `127.0.0.1:13000` with the same versioned datasource provisioning used by production.

Acceptance evidence:

- `/api/health` returned HTTP 200, Grafana version 13.2.1;
- `operations-prometheus` was provisioned as type `prometheus`, `readOnly=true`;
- `operations-loki` was provisioned as type `loki`, `readOnly=true`;
- Prometheus proxy query `up` returned HTTP 200 with live Operations series;
- Loki proxy labels returned HTTP 200 with live labels;
- acceptance result: `official-grafana-datasource-e2e=PASS`.

## Production composition

Grafana is managed by rootful Podman Quadlet and systemd:

- image: exact official digest above;
- network: host namespace;
- Grafana HTTP bind: `127.0.0.1:3000` only;
- persistent state: `/var/lib/ordivon-operations/grafana`;
- provisioning: `/etc/ordivon-grafana/provisioning`, read-only inside the container;
- Prometheus: `http://127.0.0.1:29091`;
- Loki: `http://127.0.0.1:3100`;
- anonymous access: Viewer only on loopback;
- datasource configuration: not editable in Grafana UI;
- plugin preinstall/automatic update and UI plugin administration are disabled; the read-only image supplies the accepted runtime.

The legacy Arch Grafana package is removed only after the OCI service passes health and both datasource proxy checks.

## Production acceptance

Final production acceptance passed after package retirement:

- `ordivon-grafana.service` is active with zero restarts;
- only `127.0.0.1:3000` is listening for Grafana;
- the Arch `grafana` package is absent;
- both provisioned datasources remain read-only;
- the Prometheus proxy returned two live `up` series;
- the Loki proxy returned four labels;
- no background plugin-installer failures were present after the accepted restart;
- a complete Ansible replay finished with `changed=0`, `failed=0`.
