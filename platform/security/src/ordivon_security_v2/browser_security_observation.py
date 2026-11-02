"""Pure classification and recursive comparison of public browser observations.

Observer failure is not subject drift. No external detector, transport or state
is owned by this package-local representation module.
"""

from __future__ import annotations


def classify_browser_security_observation_validity(
    observation: object,
) -> dict[str, object]:
    """Classify whether one public observation is usable for subject-drift comparison.

    Collector-side external observer failures are represented inside the public observation rather
    than by changing the witness schema. Security-v2 treats those failure sentinels as observation
    validity, not as browser subject evidence.
    """

    issues: list[dict[str, str]] = []

    def visit(value: object, path: str) -> None:
        if isinstance(value, dict):
            standing = value.get("standing")
            if isinstance(standing, str):
                normalized = standing.strip().upper()
                if normalized == "UNAVAILABLE":
                    issue = {
                        "path": path,
                        "standing": "OBSERVER_UNAVAILABLE",
                        "sourceStanding": normalized,
                    }
                    detail = value.get("detail")
                    if isinstance(detail, str) and detail.strip():
                        issue["detail"] = detail.strip()
                    issues.append(issue)
                elif normalized in {"ERROR", "FAILED"}:
                    issue = {
                        "path": path,
                        "standing": "DETECTOR_FAILED",
                        "sourceStanding": normalized,
                    }
                    detail = value.get("detail")
                    if isinstance(detail, str) and detail.strip():
                        issue["detail"] = detail.strip()
                    issues.append(issue)
            for key, child in value.items():
                visit(child, f"{path}.{key}")
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(observation, "$")
    if not issues:
        return {"standing": "VALID", "issues": []}
    standing = (
        "DETECTOR_FAILED"
        if any(issue["standing"] == "DETECTOR_FAILED" for issue in issues)
        else "OBSERVER_UNAVAILABLE"
    )
    return {"standing": standing, "issues": issues}


def _changed_json_paths(left: object, right: object, path: str = "$") -> list[str]:
    if type(left) is not type(right):
        return [path]
    if isinstance(left, dict):
        changed: list[str] = []
        for key in sorted(set(left) | set(right)):
            child_path = f"{path}.{key}"
            if key not in left or key not in right:
                changed.append(child_path)
            else:
                changed.extend(_changed_json_paths(left[key], right[key], child_path))
        return changed
    if isinstance(left, list):
        if len(left) != len(right):
            return [path]
        changed: list[str] = []
        for index, (a, b) in enumerate(zip(left, right)):
            changed.extend(_changed_json_paths(a, b, f"{path}[{index}]"))
        return changed
    return [] if left == right else [path]
