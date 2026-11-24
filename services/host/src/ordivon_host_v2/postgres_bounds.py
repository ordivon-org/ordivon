"""Physical PostgreSQL bound and exact V1 JSON/JCS numeric contract."""

POSTGRES_BIGINT_MAX = (1 << 63) - 1
# RFC 7493 / 8785 and JavaScript interoperable integer identity.
HOST_WIRE_INT_MAX = min(POSTGRES_BIGINT_MAX, (1 << 53) - 1)
