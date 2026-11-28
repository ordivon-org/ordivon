"""Pure Work revision arithmetic; caller validates the exact V1 JSON integer domain."""

def next_work_revision(expected_revision: int) -> int:
    """Advance a Host Work CAS revision without exceeding the interoperable JSON safe integer bound.

    pre: 1 <= expected_revision < 2**53 - 1
    post: __return__ == expected_revision + 1
    post: 2 <= __return__ <= 2**53 - 1
    post: __return__ > expected_revision
    """
    return expected_revision + 1

