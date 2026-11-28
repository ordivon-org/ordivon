from __future__ import annotations


def active_rooted_codeowners(source: str) -> dict[str, tuple[str, ...]]:
    """The repository's literal-root CODEOWNERS profile, not string mentions.

    GitHub treats comments as inert and the LAST matching rule as effective.
    The root-governance contract accepts only a default '*' rule first and
    later exact, rooted paths with assigned owners. A new wildcard/pattern
    grammar requires a source-bound owner test, not a guessed parser.
    """
    explicit: dict[str, tuple[str, ...]] = {}
    for lineno, line in enumerate(source.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        pattern = fields[0]
        owners = tuple(field for field in fields[1:] if not field.startswith("#"))
        if not owners or any(
            not (
                owner.startswith("@")
                and len(owner) > 1
                or "@" in owner
                and not owner.startswith("@")
            )
            for owner in owners
        ):
            raise AssertionError(f"CODEOWNERS line {lineno} has no valid owner")
        if pattern == "*":
            if explicit:
                raise AssertionError(
                    "CODEOWNERS catch-all after explicit roots overrides them"
                )
            continue
        if (
            not pattern.startswith("/")
            or any(token in pattern for token in "*?[]!\\")
            or any(
                segment in (".", "..", "") for segment in pattern.strip("/").split("/")
            )
            or pattern in explicit
        ):
            raise AssertionError(
                f"CODEOWNERS unsupported, ambiguous or duplicate root rule: {pattern}"
            )
        # A later broad root may override ownership of an earlier narrower
        # root. This existing contract forbids ambiguous explicit overlaps;
        # it does not attempt to reimplement GitHub's complete glob engine.
        if any(
            pattern.startswith(existing) or existing.startswith(pattern)
            for existing in explicit
            if existing.endswith("/")
        ):
            raise AssertionError(
                f"CODEOWNERS overlapping explicit root rule: {pattern}"
            )
        explicit[pattern] = owners
    return explicit
