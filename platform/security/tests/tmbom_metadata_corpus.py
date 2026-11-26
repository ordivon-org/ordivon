"""Independent structural metadata fixtures; not a threat assessment."""

import copy


def base_document():
    return {
        "version": "1.0",
        "scope": {
            "title": "Synthetic document",
            "description": "Metadata only",
            "business_criticality": "low",
            "data_sensitivity": [],
            "exposure": "internal",
            "tier": "non_critical",
        },
        "trust_zones": [], "trust_boundaries": [], "actors": [],
        "components": [], "data_stores": [], "data_sets": [], "data_flows": [],
    }


def metadata_corpus():
    # Synthetic structural document only; this is not a threat assessment.
    base = base_document()
    fixtures = [("valid", base, True)]
    for name, keys, value, valid in (
        ("version-number", ("version",), 1, False),
        ("version-suffix", ("version",), "1.beta", False),
        ("version-three", ("version",), "1.2.3", True),
        ("title-unicode", ("scope", "title"), "文档 é", True),
        ("description-array", ("scope", "description"), [], False),
        ("description-empty", ("scope", "description"), "", True),
        ("frozen-boolean", ("frozen",), True, True),
        ("frozen-string", ("frozen",), "true", False),
    ):
        model = copy.deepcopy(base)
        parent = model
        for key in keys[:-1]:
            parent = parent[key]
        parent[keys[-1]] = value
        fixtures.append((name, model, valid))
    for key in ("version", "scope"):
        model = copy.deepcopy(base)
        del model[key]
        fixtures.append(("missing-" + key, model, False))

    return fixtures


def metadata_matrix():
    """120 abstract metadata coordinates with independently specified validity."""
    for version, version_valid in (
        ("1", True), ("2.3.4", True), ("0.0", True), ("v1", False), ("", False), (1, False),
    ):
        for description, description_valid in (
            ("", True), ("文档", True), ("abc", True), ([], False), (None, False),
        ):
            for frozen, frozen_valid in (
                (True, True), (False, True), ("true", False), (0, False),
            ):
                obj = base_document()
                obj["version"] = version
                obj["scope"]["description"] = description
                obj["frozen"] = frozen
                yield obj, version_valid and description_valid and frozen_valid
