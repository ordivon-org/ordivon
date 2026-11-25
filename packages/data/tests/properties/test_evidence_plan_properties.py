"""Metadata admission precedes the entire selected batch's file observations."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

PACKAGE = Path(__file__).resolve().parents[2]
ROOT = PACKAGE.parents[1]
sys.path.insert(0, str(PACKAGE / "src"))
from ordivon_data.local_evidence import LocalEvidenceBinding
from ordivon_data.odps_projection import project_catalog

SOURCE = json.loads(
    (
        ROOT / "catalogs/data-products/experimental-episode-corpus-r1/odps.json"
    ).read_bytes()
)
PATH_PROP = "corpusManifestRelativePath"
DIGEST_PROP = "corpusManifestSha256"
PORT = "episode-corpus-manifest-json"


@given(
    st.integers(min_value=2, max_value=6),
    st.integers(min_value=0, max_value=5),
    st.sampled_from(
        ["digest", "missing", "duplicate", "absolute", "parent", "nul", "surrogate"]
    ),
    st.booleans(),
)
@settings(max_examples=160, derandomize=True, database=None, deadline=None)
def test_invalid_declaration_never_starts_any_bound_file_observation(
    count, target, defect, reverse
):
    products = []
    bindings = []
    for index in range(count):
        product = copy.deepcopy(SOURCE)
        version = str(index)
        product["version"] = version
        for prop in product["customProperties"]:
            if prop["property"] == PATH_PROP:
                prop["value"] = version + ".json"
            if prop["property"] == DIGEST_PROP:
                prop["value"] = hashlib.sha256(version.encode()).hexdigest()
        products.append(product)
        bindings.append(
            LocalEvidenceBinding(
                product["id"],
                PORT,
                PATH_PROP,
                DIGEST_PROP,
                Path("/unused"),
                port_version="1.0.0",
                product_version=version,
            )
        )
    props = products[target % count]["customProperties"]
    digest = next(p for p in props if p["property"] == DIGEST_PROP)
    path = next(p for p in props if p["property"] == PATH_PROP)
    if defect == "digest":
        digest["value"] = "0" * 63
    elif defect == "missing":
        props.remove(digest)
    elif defect == "duplicate":
        props.append(digest.copy())
    else:
        path["value"] = {
            "absolute": "/escape.json",
            "parent": "../escape.json",
            "nul": "a\x00b",
            "surrogate": "a\ud800b",
        }[defect]
    if reverse:
        products.reverse()
        bindings.reverse()
    with patch(
        "ordivon_data.local_evidence.scoped_sha256",
        side_effect=lambda path, *args, **kwargs: (
            hashlib.sha256(path.stem.encode()).hexdigest(),
            "observed",
        ),
    ) as observe:
        try:
            project_catalog(
                [json.dumps(p).encode() for p in products], bindings=tuple(bindings)
            )
        except ValueError:
            pass
        else:
            raise AssertionError("invalid declaration admitted")
        observe.assert_not_called()
