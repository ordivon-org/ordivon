"""Bounded DCAT 3 discovery projection; not a JSON-LD/RDF conformance engine.

Only exact, explicitly scoped local file distributions can be byte-checked.
Missing, remote, malformed and unbound data remain UNKNOWN rather than FAIL.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_distribution(
    distribution: dict[str, Any], allowed_roots: tuple[Path, ...], verify_local: bool
) -> dict[str, Any]:
    result = {
        "id": distribution.get("@id"),
        "title": distribution.get("dct:title"),
        "format": distribution.get("dct:format"),
        "declaredDigest": distribution.get("dct:identifier"),
        "uri": None,
        "verification": "NOT_CHECKED" if not verify_local else "UNKNOWN",
        "reason": "metadata_only" if not verify_local else "unbound",
    }
    access = distribution.get("dcat:accessURL")
    if isinstance(access, dict):
        result["uri"] = access.get("@id")
    if not verify_local:
        return result
    uri = result["uri"]
    if not isinstance(uri, str):
        result["reason"] = "no_access_url"
        return result
    parts = urlsplit(uri)
    if (
        parts.scheme != "file"
        or parts.netloc not in ("", "localhost")
        or parts.query
        or parts.fragment
    ):
        result["reason"] = "unsupported_uri_or_authority"
        return result
    # A file URI must have an absolute path and no ambiguous authority.
    if not parts.path.startswith("/"):
        result["reason"] = "nonabsolute_file_uri"
        return result
    path = Path(unquote(parts.path)).resolve()
    if not any(path.is_relative_to(root.resolve()) for root in allowed_roots):
        result["reason"] = "outside_explicit_scope"
        return result
    if not path.is_file():
        result["reason"] = "local_file_unavailable"
        return result
    declared = result["declaredDigest"]
    if (
        not isinstance(declared, str)
        or len(declared) != 71
        or not declared.startswith("sha256:")
    ):
        result["reason"] = "sha256_not_bound"
        return result
    hexdigest = declared[7:]
    if any(c not in "0123456789abcdef" for c in hexdigest):
        result["reason"] = "sha256_not_bound"
        return result
    observed = _sha256(path)
    result["observedDigest"] = "sha256:" + observed
    result["verification"] = "VERIFIED" if observed == hexdigest else "FALSIFIED"
    result["reason"] = "digest_match" if observed == hexdigest else "digest_mismatch"
    return result


def inspect_catalog(
    catalog_path: Path,
    *,
    verify_local: bool = False,
    allowed_roots: tuple[Path, ...] = (),
) -> dict[str, Any]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    # This checks the known compact JSON-LD projection shape; it is not RDF validation.
    if catalog.get("@type") != "dcat:Catalog" or not isinstance(
        catalog.get("dcat:dataset"), list
    ):
        raise ValueError("not a supported DCAT compact JSON-LD Catalog projection")
    products = []
    for dataset in catalog["dcat:dataset"]:
        if not isinstance(dataset, dict) or "dcat:Dataset" not in (
            dataset.get("@type")
            if isinstance(dataset.get("@type"), list)
            else [dataset.get("@type")]
        ):
            raise ValueError("catalog includes a non-Dataset entry")
        distributions = dataset.get("dcat:distribution", [])
        if not isinstance(distributions, list):
            raise TypeError("dataset distributions are not a list")
        products.append(
            {
                "id": dataset.get("dct:identifier"),
                "title": dataset.get("dct:title"),
                "version": dataset.get("dcat:version"),
                "policy": dataset.get("odrl:hasPolicy"),
                "distributions": [
                    inspect_distribution(item, allowed_roots, verify_local)
                    for item in distributions
                ],
            }
        )
    return {
        "sourceCatalog": str(catalog_path.resolve()),
        "catalogId": catalog.get("@id"),
        "profile": "dcat-3-compact-jsonld-projection",
        "scope": "bounded_discovery_not_domain_truth_or_rdf_conformance",
        "products": products,
    }
