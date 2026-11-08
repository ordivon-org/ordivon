"""Bounded DCAT 3 discovery projection; not a JSON-LD/RDF conformance engine.

Only exact, explicitly scoped local file distributions can be byte-checked.
Missing, remote, malformed and unbound data remain UNKNOWN rather than FAIL.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from .verification import digest_verdict


_SCOPED_OPEN_SUPPORTED = (
    os.open in os.supports_dir_fd
    and hasattr(os, "O_NOFOLLOW")
    and hasattr(os, "O_DIRECTORY")
)


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


def _scoped_sha256(
    path: Path, allowed_roots: tuple[Path, ...], *, hash_bytes: bool
) -> tuple[str | None, str]:
    """Hash one opened regular-file descriptor, anchored to an allowed root.

    Linux/POSIX openat-style dir_fd traversal + O_NOFOLLOW closes the
    check-then-open pathname race. Symlink components are intentionally not
    accepted, even when they currently resolve within an allowed root.
    A concurrent in-place writer is detected on best-effort file metadata;
    immutable producer snapshots remain required for strong read isolation.
    """
    if ".." in path.parts or "\x00" in str(path):
        return None, "unsupported_scoped_path"
    roots = sorted(
        (root.absolute() for root in allowed_roots if ".." not in root.parts),
        key=lambda root: len(root.parts),
        reverse=True,
    )
    matching = [root for root in roots if path.is_relative_to(root)]
    if not matching:
        return None, "outside_explicit_scope"
    if not _SCOPED_OPEN_SUPPORTED:
        # Never silently fall back to an unsafe path reopen on other OSes.
        return None, "scoped_descriptor_unavailable"

    dir_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    file_flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    reason = "local_file_unavailable"
    for root in matching:
        relative = path.relative_to(root)
        if not relative.parts:
            return None, "unsupported_scoped_path"
        directory_fd = None
        try:
            directory_fd = os.open("/", dir_flags)
            # Anchor every ancestor, including the allowed root itself.
            # No pathname is consulted after its directory FD is opened.
            for component in (*root.parts[1:], *relative.parts[:-1]):
                next_fd = os.open(component, dir_flags, dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = next_fd
            fd = os.open(relative.parts[-1], file_flags, dir_fd=directory_fd)
            with os.fdopen(fd, "rb") as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode):
                    return None, "not_regular_file"
                if not hash_bytes:
                    return None, "sha256_not_bound"
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
                after = os.fstat(stream.fileno())
                identity = lambda st: (
                    st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns
                )
                if identity(before) != identity(after):
                    return None, "file_changed_during_read"
                return digest, "descriptor_digest_observed"
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                reason = "unsupported_scoped_path"
            elif exc.errno == errno.ENOENT and reason != "unsupported_scoped_path":
                reason = "local_file_unavailable"
            elif reason != "unsupported_scoped_path":
                reason = "local_file_unavailable"
        finally:
            if directory_fd is not None:
                os.close(directory_fd)
    return None, reason


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
    path = Path(unquote(parts.path))
    declared = result["declaredDigest"]
    digest_bound = (
        isinstance(declared, str)
        and len(declared) == 71
        and declared.startswith("sha256:")
        and all(c in "0123456789abcdef" for c in declared[7:])
    )
    observed, reason = _scoped_sha256(path, allowed_roots, hash_bytes=digest_bound)
    if observed is None:
        result["reason"] = reason
        return result
    hexdigest = declared[7:]
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
