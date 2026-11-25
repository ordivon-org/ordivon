"""Independent lexical/authorization boundary tests; native checks run separately."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pg_test_lease import DSN_NAMES, LEASE, LeaseError, targets, verify_leases

TOKEN = "a" * 64
VALID = "host=/tmp/owned-pg dbname=ordivon_paper user=postgres"


def test_no_database_developer_lane():
    assert verify_leases({}) == ()


@pytest.mark.parametrize("token", [None, "", "a" * 63, "g" * 64, "A" * 64])
def test_unleased_dsn_rejected_before_connect(token):
    env = {DSN_NAMES[0]: VALID}
    if token is not None:
        env[LEASE] = token
    with pytest.raises(LeaseError, match="provisioner-issued"):
        verify_leases(env)


@pytest.mark.parametrize(
    "dsn",
    [
        "",
        "host=localhost dbname=ordivon_paper user=postgres",
        "host=127.0.0.1,127.0.0.2 dbname=ordivon_paper user=postgres",
        "host=/tmp/owned-pg dbname=postgres user=postgres",
        "host=/tmp/owned-pg dbname=ordivon_paper",
        "host=/tmp/owned-pg dbname=ordivon_paper user=postgres port=0",
        "host=/tmp/owned-pg dbname=ordivon_paper user=postgres hostaddr=127.0.0.1",
        "service=somewhere",
        VALID + " options='-c search_path=private'",
        VALID + " connect_timeout=0",
    ],
)
def test_ambiguous_targets_rejected_before_connect(dsn):
    with pytest.raises(LeaseError):
        verify_leases({DSN_NAMES[0]: dsn, LEASE: TOKEN})


@pytest.mark.parametrize("key", ["PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS", "PGPORT"])
def test_ambient_libpq_routing_cannot_override_explicit_target(key):
    with pytest.raises(LeaseError, match="ambient"):
        verify_leases({DSN_NAMES[0]: VALID, LEASE: TOKEN, key: "unexpected"})


def test_all_targets_preflight_before_first_connection():
    with pytest.raises(LeaseError, match=DSN_NAMES[1]):
        verify_leases({DSN_NAMES[0]: VALID, DSN_NAMES[1]: "service=other", LEASE: TOKEN})


@settings(max_examples=100, derandomize=True, deadline=None)
@given(
    port=st.integers(min_value=1, max_value=65535),
    suffix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=20),
)
def test_explicit_loopback_and_private_socket_round_trip(port, suffix):
    dbname = "ordivon_" + suffix
    for host in ("127.0.0.1", "/tmp/" + suffix):
        dsn = f"host={host} port={port} dbname={dbname} user=postgres"
        ((name, params),) = targets({DSN_NAMES[0]: dsn, LEASE: TOKEN})
        assert name == DSN_NAMES[0]
        assert params == {"host": host, "port": str(port), "dbname": dbname, "user": "postgres"}


def test_native_marker_is_not_inferred_from_db_name():
    import os

    env = dict(os.environ)
    if not any(name in env for name in DSN_NAMES):
        pytest.skip("provisioner-owned native PostgreSQL target absent")
    receipt = verify_leases(env)
    assert {name for name, oid in receipt if oid > 0} == {name for name in DSN_NAMES if name in env}
    original = env[LEASE]
    env[LEASE] = ("b" if original[0] == "a" else "a") + original[1:]
    with pytest.raises(LeaseError, match="lease mismatch"):
        verify_leases(env)
