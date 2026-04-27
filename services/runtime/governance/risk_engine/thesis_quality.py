"""H-9C3: Deterministic thesis quality checks.

All checks are rule-based (length, patterns, wording) — no NLP/ML.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ── Constants ──────────────────────────────────────────────────────────

THESIS_MIN_LENGTH: int = 50

BANNED_THESIS_PATTERNS: tuple[str, ...] = (
    "just feels right",
    "feels right",
    "looks good",
    "probably pump",
    "should go up",
    "should go down",
    "vibes",
    "no specific thesis",
    "trust me",
    "yolo",
    "because i said so",
    "i think so",
    "let's see",
    "we'll see",
    "who knows",
    "idk",
    "just a hunch",
    "gut feeling",
    "hoping for",
    "praying for",
)

INVALIDATION_WORDS: tuple[str, ...] = (
    "unless",
    "invalid",
    "invalidate",
    "falsif",
    "if not",
    "stop if",
    "exit if",
    "cut if",
)

CONFIRMATION_WORDS: tuple[str, ...] = (
    "confirm",
    "confirmed when",
    "verif",
    "must hold",
    "must close",
    "needs to",
    "requires",
)


@dataclass(slots=True)
class ThesisQualityResult:
    """Result of thesis quality evaluation."""

    is_banned: bool = False
    banned_match: str | None = None
    is_too_short: bool = False
    lacks_verifiability: bool = False
    reasons: list[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return self.is_banned or self.is_too_short or self.lacks_verifiability


def check_thesis_quality(thesis: str) -> ThesisQualityResult:
    """Evaluate thesis quality against deterministic rules.

    Returns a ThesisQualityResult with:
    - is_banned: thesis matches a banned generic pattern → reject
    - is_too_short: thesis < 50 chars → escalate
    - lacks_verifiability: no invalidation/confirmation wording → escalate
    """
    result = ThesisQualityResult()
    lowered = thesis.lower().strip()

    # Check 1: Banned patterns
    for pattern in BANNED_THESIS_PATTERNS:
        if pattern in lowered:
            result.is_banned = True
            result.banned_match = pattern
            result.reasons.append(f"Thesis matches banned generic pattern: '{pattern}'.")
            break

    # Check 2: Minimum length
    if len(thesis.strip()) < THESIS_MIN_LENGTH:
        result.is_too_short = True
        result.reasons.append(
            f"Thesis is shorter than {THESIS_MIN_LENGTH} characters "
            f"({len(thesis.strip())} chars) — too short to be meaningful."
        )

    # Check 3: Verifiability (invalidation or confirmation language)
    has_invalidation = any(w in lowered for w in INVALIDATION_WORDS)
    has_confirmation = any(w in lowered for w in CONFIRMATION_WORDS)

    if not has_invalidation and not has_confirmation:
        result.lacks_verifiability = True
        result.reasons.append("Thesis lacks invalidation or confirmation criteria — not verifiable.")

    return result
