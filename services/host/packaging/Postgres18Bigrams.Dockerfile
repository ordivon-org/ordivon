# PostgreSQL 18 upstream base + pinned pglayers OCI LEGO for pg_bigm 1.2.
# No custom extension compiler, package manager, or replacement search server.
# Source: https://github.com/pglayers/pglayers
# Resolved immutable OCI index digest for linux/amd64/linux/arm64.
FROM postgres:18
COPY --from=ghcr.io/pglayers/pgx-pg_bigm@sha256:07042dbf6bf83f47686abcf8452fbb732142fb2bc7bea8406ac1ce8b6e35ef68 \
    /lib/pg_bigm.so /usr/lib/postgresql/18/lib/pg_bigm.so
COPY --from=ghcr.io/pglayers/pgx-pg_bigm@sha256:07042dbf6bf83f47686abcf8452fbb732142fb2bc7bea8406ac1ce8b6e35ef68 \
    /share/extension/ /usr/share/postgresql/18/extension/
