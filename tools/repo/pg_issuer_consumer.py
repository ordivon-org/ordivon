"""Original Harness PG issuer test consumer: source-only evidence locator.

This does not grant Runtime/Host permissions.  Only the actual, unique,
ignored native PostgreSQL test consuming the original Harness issuer is
an admissible test-only dependency. A file move inside the PG effect
domain does not change the business consumer or the required verification.
"""

from __future__ import annotations

import re
from pathlib import Path

RUNTIME_PG_CORE_ROOT = "services/runtime/crates/ordivon-runtime-core/src/pg_admission/"
ORIGINAL_HARNESS_PG_ISSUER_TEST = (
    "pg18_original_harness_store_real_issuer_same_job_late_revoke"
)


def locate_original_harness_issuer_source(repo: Path) -> str:
    """Find one actual Rust PG18 Harness issuer consumer by test behavior.

    Renaming or moving the test module must not change the consumer edge.
    A broad owner-pair wildcard, symlink, duplicated/fake test, or a missing
    executable test is not an authorized way to suppress verification.
    """
    core = repo / RUNTIME_PG_CORE_ROOT
    if not core.is_dir() or core.is_symlink():
        raise ValueError("unapproved original Harness test-only source seam")
    pattern = re.compile(
        r"(?m)^\s*fn\s+"
        + re.escape(ORIGINAL_HARNESS_PG_ISSUER_TEST)
        + r"\s*\("
    )
    matches: list[str] = []
    for candidate in sorted(core.rglob("*.rs")):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        source = candidate.read_text(encoding="utf-8")
        found = list(pattern.finditer(source))
        for match in found:
            # Tests here run by the original libtest Cargo owner. The test
            # annotation must belong to THIS function, not another test.
            annotations = source[max(0, match.start() - 220):match.start()]
            annotations = annotations.rsplit("}", 1)[-1]
            if not (
                re.search(r"#\[test\]", annotations)
                and re.search(r"#\[ignore\s*=", annotations)
            ):
                continue
            # Preserve the genuine Harness publisher + Python module lookup
            # inside this one issuer behavior, not a coincidental import in
            # another Rust test file.
            body = source[match.start():].split("\n#[test]", 1)[0]
            if all(
                fragment in body
                for fragment in (
                    'root.join("services/harness/tests/original_pg_issuer_native_fixture.py")',
                    'root.join("services/harness/src")',
                    'root.join("services/harness")',
                )
            ):
                matches.append(candidate.relative_to(repo).as_posix())
    if len(matches) != 1:
        raise ValueError("unapproved original Harness test-only source seam")
    return matches[0]
