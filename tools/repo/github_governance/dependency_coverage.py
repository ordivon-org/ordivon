from __future__ import annotations


def update_for(config: dict, ecosystem: str) -> dict:
    matches = [
        row
        for row in config.get("updates", [])
        if row.get("package-ecosystem") == ecosystem
    ]
    if len(matches) != 1:
        raise AssertionError(f"{ecosystem}: expected exactly one root update entry, got {len(matches)}")
    return matches[0]

def configured_dirs(row: dict) -> set[str]:
    if "directories" in row:
        return set(row["directories"])
    if "directory" in row:
        return {row["directory"]}
    return set()
