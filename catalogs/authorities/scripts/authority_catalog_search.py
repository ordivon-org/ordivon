"""Pure lexical discovery scoring over prebuilt authority index entries.

No filesystem reads, currentness mutation, or task-local verdicts.
"""

from __future__ import annotations

import re


def tokens(text: str) -> list[str]:
    # Discovery treats punctuation and taxonomy separators as token boundaries.
    # Exact identifiers/aliases are scored separately, so semantic lookup benefits
    # from matching `bill-of-materials` with `bill of materials` and similar forms.
    return re.findall(r"[a-z0-9]+", text.casefold())


def normalized_text(text: str) -> str:
    return " ".join(tokens(text))


QUERY_MODIFIERS = {
    "current",
    "latest",
    "official",
    "standard",
    "standards",
    "specification",
    "specifications",
    "spec",
    "framework",
    "version",
    "edition",
    "guideline",
    "guidelines",
    "guidance",
}


def significant_query_tokens(query: str) -> list[str]:
    raw = tokens(query)
    meaningful = [token for token in raw if token not in QUERY_MODIFIERS]
    return meaningful or raw


def score_entry(entry: dict, query: str) -> int:
    q = query.casefold().strip()
    qtokens = significant_query_tokens(query)
    if not qtokens:
        return 0

    identifier = entry["id"].casefold()
    title = entry["title"].casefold()
    aliases = [x.casefold() for x in entry["aliases"]]
    topics = [x.casefold() for x in entry["topics"]]
    domains = [x.casefold() for x in entry["domains"]]
    issuer = entry["issuer"].casefold()

    qnorm = normalized_text(query)
    title_norm = normalized_text(title)
    alias_norms = [normalized_text(x) for x in aliases]
    field_tokens = {
        "identifier": set(tokens(identifier)),
        "title": set(tokens(title)),
        "aliases": set(t for value in aliases for t in tokens(value)),
        "topics": set(t for value in topics for t in tokens(value)),
        "domains": set(t for value in domains for t in tokens(value)),
        "issuer": set(tokens(issuer)),
    }
    all_tokens = set().union(*field_tokens.values())
    matched = {token for token in qtokens if token in all_tokens}
    coverage = len(matched) / len(set(qtokens))

    # Discovery fails closed for multi-token semantic queries: every meaningful
    # query token must be represented by the candidate. Generic query modifiers
    # such as `latest` or `standard` are ignored for this gate. This prevents
    # unknown named entities from receiving plausible-looking partial matches.
    if len(set(qtokens)) > 1 and coverage < 1.0:
        return 0

    score = 0
    if q == identifier:
        score += 1000
    if qnorm in alias_norms:
        score += 700
    if qnorm and qnorm in title_norm:
        score += 350
    if qnorm and any(qnorm in value for value in alias_norms):
        score += 250

    for token in qtokens:
        if token in field_tokens["identifier"]:
            score += 90
        if token in field_tokens["title"]:
            score += 55
        if token in field_tokens["aliases"]:
            score += 45
        if token in field_tokens["topics"]:
            score += 60
        if token in field_tokens["domains"]:
            score += 25
        if token in field_tokens["issuer"]:
            score += 15
        if token not in all_tokens:
            score -= 80

    if coverage == 1.0 and len(set(qtokens)) > 1:
        score += 200
    return max(score, 0)
