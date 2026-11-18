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

from .verification import digest_verdict


def _declared_sha256(distribution: dict[str, Any]) -> Any:
    """Read DCAT 3 SPDX checksum; retain legacy sha256 dct:identifier support.

    In W3C DCAT 3 dct:identifier identifies the Distribution, rather than
    declaring its content digest. Historical Ordivon frozen catalogs placed
    sha256:... there; those remain readable without rewriting old evidence.
    """
    legacy = distribution.get("dct:identifier")
    checksum = distribution.get("spdx:checksum")
    if checksum is None:
        return legacy
    if not isinstance(checksum, dict):
        raise TypeError("spdx:checksum must be an object")
    if checksum.get("@type") != "spdx:Checksum":
        raise ValueError("spdx:checksum must identify an SPDX Checksum")
    algorithm = checksum.get("spdx:algorithm")
    if algorithm != {"@id": "http://spdx.org/rdf/terms#checksumAlgorithm_sha256"}:
        # A different or unbound algorithm is not false evidence of SHA-256.
        return None
    typed_value = checksum.get("spdx:checksumValue")
    if (
        not isinstance(typed_value, dict)
        or typed_value.get("@type") != "xsd:hexBinary"
        or not isinstance(typed_value.get("@value"), str)
    ):
        raise ValueError("invalid SPDX hexBinary checksum value")
    candidate = typed_value["@value"]
    if len(candidate) != 64 or any(ch not in "0123456789abcdef" for ch in candidate):
        raise ValueError("invalid SHA-256 checksum value")
    declared = "sha256:" + candidate
    if isinstance(legacy, str) and legacy.startswith("sha256:") and legacy != declared:
        raise ValueError("conflicting legacy and SPDX digest bindings")
    return declared


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
        "declaredDigest": _declared_sha256(distribution),
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
    result["verification"] = digest_verdict(hexdigest, observed)
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
    seen_product_versions: set[tuple[str, str]] = set()
    for dataset in catalog["dcat:dataset"]:
        if not isinstance(dataset, dict) or "dcat:Dataset" not in (
            dataset.get("@type")
            if isinstance(dataset.get("@type"), list)
            else [dataset.get("@type")]
        ):
            raise ValueError("catalog includes a non-Dataset entry")
        product_id, version = dataset.get("dct:identifier"), dataset.get("dcat:version")
        if (
            not isinstance(product_id, str)
            or not product_id
            or not isinstance(version, str)
            or not version
        ):
            raise ValueError("dataset has no stable product identifier and version")
        identity = (product_id, version)
        if identity in seen_product_versions:
            raise ValueError("duplicate data product identity and version")
        seen_product_versions.add(identity)
        distributions = dataset.get("dcat:distribution", [])
        if not isinstance(distributions, list) or any(
            not isinstance(item, dict) for item in distributions
        ):
            raise TypeError("dataset distributions must be a list of objects")
        products.append(
            {
                "id": product_id,
                "title": dataset.get("dct:title"),
                "version": version,
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
