from __future__ import annotations

from datetime import date

from .constants import GH, REPO, WINDOWS


def normalize(raw: dict, history: set[str]) -> dict:
    if raw.get("kind") != "ordivon.github-trending-observation-r1":
        raise ValueError("input is not a declared GitHub Trending observation")
    day = date.fromisoformat(raw["snapshotDay"])
    if not raw.get("windows"):
        raise ValueError("no official Trending window observation")
    indexed: dict[str, dict] = {}
    observed_windows: set[str] = set()
    failures = raw.get("windowFailures", {})
    if (not isinstance(failures, dict) or
            any(k not in WINDOWS or not isinstance(v, str) or not v for k, v in failures.items())):
        raise ValueError("invalid source window failure details")
    for window in raw["windows"]:
        if not window.get("entries"):
            raise ValueError("empty official Trending window observation")
        if window["window"] in observed_windows:
            raise ValueError("duplicate official Trending window")
        observed_windows.add(window["window"])
        win = window["window"]
        if win not in WINDOWS or window.get("sourceUrl") != GH + "/trending?since=" + win:
            raise ValueError("not an official window URL")
        for item in window.get("entries", []):
            repo = item["repo"]
            if not REPO.fullmatch(repo):
                raise ValueError("invalid GitHub repository name")
            gain = item.get("newStars")
            if gain is not None and (type(gain) is not int or gain < 0 or item.get("sourceWindowLabel") != WINDOWS[win]):
                raise ValueError("star increment has wrong window or an unverified metric")
            c = indexed.setdefault(repo, {"repo": repo, "url": GH + "/" + repo, "officialTrending": [],
                                          "origin": raw["origin"]})
            c["officialTrending"].append({"window": win, "stars": gain, "label": item.get("sourceWindowLabel"),
                                           "sourceUrl": window["sourceUrl"], "retrievedAt": window["retrievedAt"],
                                           "sourceBodySha256": window.get("sourceBodySha256")})
    if observed_windows.intersection(failures):
        raise ValueError("source window cannot be observed and failed")
    coverage = {
        "observedWindows": [w for w in WINDOWS if w in observed_windows],
        "failedWindows": [w for w in WINDOWS if w in failures],
        "unobservedWindows": [w for w in WINDOWS if w not in observed_windows and w not in failures],
        "complete": observed_windows == set(WINDOWS),
        "failureNotes": {w: failures[w] for w in WINDOWS if w in failures},
    }
    for repo, value in indexed.items():
        api = raw.get("repositories", {}).get(repo, {})
        value["totalStars"] = api.get("totalStars")
        value["totalStarsSource"] = "GitHub REST repository metadata" if api.get("apiStatus") == "OK" else None
        value["licenseMetadata"] = api.get("licenseMetadata")
        value["metadataCurrentness"] = api.get("pushedAt")
        value["apiStatus"] = api.get("apiStatus", "UNVERIFIED")
        # Preserve the original upstream diagnostic for an actually observed API failure.
        # Do not turn an unavailable metadata lookup into a claim that the repo is absent.
        if value["apiStatus"] == "FAILED" and api.get("note"):
            value["apiFailureNote"] = str(api["note"])[:200]
        value["licenseVerification"] = "METADATA_ONLY_NOT_LICENSE_FILE"
        value["repeatedWithin7Days"] = repo in history
        value["recommendationDisposition"] = "REVIEW_CHANGE_BEFORE_REPEAT" if repo in history else "NEW_CANDIDATE"
        value["adoptionStanding"] = "DISCOVERY_ONLY"
    return {"kind": "ordivon.github-radar-candidates-r1", "snapshotDay": day.isoformat(),
            "observedAt": raw["observedAt"], "origin": raw["origin"],
            "sourceCoverage": coverage,
            "candidates": [indexed[k] for k in sorted(indexed)],
            "nonClaims": ["Official Trending display windows are not UTC rolling windows",
                          "No arbitrary GitHub API historical star delta inferred",
                          "Discovery candidates do not confer software installation or adoption"]}
