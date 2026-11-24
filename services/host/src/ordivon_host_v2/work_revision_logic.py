"""Pure Work revision arithmetic; caller validates the exact BIGINT domain."""

def next_work_revision(expected_revision: int) -> int:
    """Advance a Host Work CAS revision without exceeding PostgreSQL BIGINT.

    pre: 1 <= expected_revision < 2**63 - 1
    post: __return__ == expected_revision + 1
    post: 2 <= __return__ <= 2**63 - 1
    post: __return__ > expected_revision
    """
    return expected_revision + 1

