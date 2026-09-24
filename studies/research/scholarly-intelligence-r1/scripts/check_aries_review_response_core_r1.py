#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
RECEIPT = STUDY / "evidence/aries-review-response-core-r1.json"
BASELINE = STUDY / "evidence/aries-lifecycle-fork-baseline-r1.json"


def fail(m):
    raise SystemExit(m)


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return "sha256:" + h.hexdigest()


def count_jsonl(p):
    with p.open(encoding="utf-8") as f:
        return sum(1 for x in f if x.strip())


def main():
    r = load(RECEIPT)
    b = load(BASELINE)
    root = Path(r["snapshot"]["root"])
    if r.get("status") != "MATERIALIZED_REVIEW_RESPONSE_CORE_ANALYTICAL_VIEWS_PASS":
        fail("receipt standing drifted")
    if r.get("privacy", {}).get("reviewerProfilingAuthorized") is not False:
        fail("reviewer profiling boundary weakened")
    for rel in [
        "raw/review_replies.jsonl",
        "raw/LICENSE",
        "SNAPSHOT_MANIFEST_R1.json",
        "SCHEMA_CENSUS_R1.json",
        "ANALYTICAL_BUILD_RECEIPT_R1.json",
        "BASELINE_R1.json",
        "derived/jsonl/official_reviews.jsonl",
        "derived/jsonl/author_responses.jsonl",
        "derived/jsonl/reply_edges.jsonl",
        "derived/jsonl/manual_concern_review_links.jsonl",
        "derived/jsonl/concern_response_context_links.jsonl",
        "derived/jsonl/lifecycle_forks.jsonl",
        "derived/aries-review-response-core-r1.duckdb",
    ]:
        if not (root / rel).is_file():
            fail(f"missing {rel}")
    if (root / "raw/review_replies.jsonl").stat().st_size != 198981013 or sha(
        root / "raw/review_replies.jsonl"
    ) != r["source"]["sha256"]:
        fail("raw carrier drifted")
    if sha(root / "raw/LICENSE") != r["source"]["licenseFileSha256"]:
        fail("license drifted")
    for rel, key in [
        ("SNAPSHOT_MANIFEST_R1.json", "manifestSha256"),
        ("SCHEMA_CENSUS_R1.json", "schemaCensusSha256"),
        ("ANALYTICAL_BUILD_RECEIPT_R1.json", "analyticalBuildReceiptSha256"),
        ("BASELINE_R1.json", "baselineSha256"),
    ]:
        if sha(root / rel) != r["snapshot"][key]:
            fail(f"{rel} digest drifted")
    c = load(root / "SCHEMA_CENSUS_R1.json")
    exp = {
        "sourceReviewRecords": 23706,
        "sourceAuthorReplies": 32691,
        "relevantForums": 1720,
        "relevantOfficialReviews": 6380,
        "relevantAuthorResponses": 10464,
        "directAuthorResponses": 8488,
        "chainedAuthorResponses": 1976,
        "manualConcernRows": 196,
        "manualConcernExactReviewJoins": 196,
        "manualConcernForumMismatches": 0,
        "orphanReplyParents": 0,
        "concernResponseContextLinks": 270,
        "manualConcernsWithAnyResponse": 196,
        "manualConcernsWithPositiveRevision": 87,
        "manualConcernsWithBothBranches": 87,
    }
    for k, v in exp.items():
        if c["counts"].get(k) != v:
            fail(f"census drift {k}")
    if "do not prove that a response addresses that specific concern" not in c.get(
        "relationCeiling", ""
    ):
        fail("relation ceiling weakened")
    a = load(root / "ANALYTICAL_BUILD_RECEIPT_R1.json")
    if any(v != 0 for v in a["referential"].values()):
        fail("referential integrity failed")
    for row in a["files"]:
        if sha(root / row["path"]) != row["sha256"]:
            fail(f"analytical digest drift {row['path']}")
    for rel in [
        "official_reviews.jsonl",
        "author_responses.jsonl",
        "reply_edges.jsonl",
        "manual_concern_review_links.jsonl",
        "concern_response_context_links.jsonl",
        "lifecycle_forks.jsonl",
    ]:
        if count_jsonl(root / "derived/jsonl" / rel) != a["counts"][rel[:-6]]:
            fail(f"row count drift {rel}")
    for rel in ["official_reviews.jsonl", "author_responses.jsonl"]:
        with (root / "derived/jsonl" / rel).open(encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                obj = json.loads(line)
                if "writers" in obj or "readers" in obj:
                    fail(f"identity field leak {rel}:{i}")
    if (
        b.get("sourceSnapshotIdentity") != r["snapshot"]["identity"]
        or b["counts"]["manualConcernsWithBothBranches"] != 87
    ):
        fail("baseline drifted")
    if "no Response->Revision causal or semantic edge is asserted" not in " ".join(
        b.get("interpretationCeiling", [])
    ):
        fail("causal ceiling weakened")
    print(
        json.dumps(
            {
                "schemaVersion": 1,
                "kind": "ordivon.research.aries-review-response-core-acceptance",
                "standing": "PASS_ARIES_SAME_AUTHORITY_LIFECYCLE_FORK",
                "snapshotIdentity": r["snapshot"]["identity"],
                "manualConcerns": 196,
                "manualConcernsWithReviewResponseContext": 196,
                "manualConcernsWithPositiveRevisionCorrespondence": 87,
                "manualConcernsWithBothBranches": 87,
                "truthBoundary": "Pass proves exact source-review identity, reply topology, and separate concern-edit correspondence. It does not identify concern-specific response adequacy or a Response->Revision semantic/causal edge.",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
