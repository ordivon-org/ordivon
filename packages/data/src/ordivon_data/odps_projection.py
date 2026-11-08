"""Deterministic discovery projection from actual producer-owned ODPS 1.1 metadata.

No source data, product registry, policy grant, or distribution URL is invented.
The projection is deliberately read-only and not an RDF schema validator.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from .local_evidence import LocalEvidenceBinding, qualified_local_distribution

_FORMATS = {
    "file/json": "application/json",
    "file/parquet": "application/vnd.apache.parquet",
    "file/csv": "text/csv",
}


def _uuid_uri(value: str) -> str | None:
    """Keep upstream IDs as supplied; mint no URI for a non-UUID identifier."""
    try:
        return "urn:uuid:" + str(UUID(value))
    except ValueError:
        return None


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"ODPS missing nonempty {field}")
    return value


def project_odps(
    source: Path | bytes, *, bindings: tuple[LocalEvidenceBinding, ...] = ()
) -> tuple[dict[str, Any], str]:
    """Project one ODPS metadata blob, never its physical availability.

    Bytes may originate from an exact Git commit, while Path remains the
    explicit live/local mode consumed by existing owner workflows.
    """
    if isinstance(source, Path):
        raw = source.read_bytes()
    elif isinstance(source, bytes):
        raw = source
    else:
        raise TypeError("ODPS input must be a Path or immutable bytes")
    product = json.loads(raw)
    if not isinstance(product, dict):
        raise TypeError("ODPS document must be an object")
    if product.get("apiVersion") != "v1.1.0" or product.get("kind") != "DataProduct":
        raise ValueError(
            "only explicitly consumed ODPS DataProduct v1.1.0 is supported"
        )
    if product.get("status") != "active":
        raise ValueError("projection requires explicitly active owner product")
    product_id = _text(product.get("id"), field="id")
    version = _text(product.get("version"), field="version")
    name = _text(product.get("name"), field="name")
    dataset_uri = _uuid_uri(product_id)

    outputs = product.get("outputPorts")
    if not isinstance(outputs, list) or not outputs:
        raise ValueError("ODPS active product must declare nonempty outputPorts")
    distributions = []
    seen_ports: set[tuple[str, str | None]] = set()
    seen_port_ids: set[str] = set()
    for port in outputs:
        if not isinstance(port, dict):
            raise TypeError("ODPS outputPort must be an object")
        port_name = _text(port.get("name"), field="outputPort.name")
        port_version = port.get("version")
        if port_version is not None:
            port_version = _text(port_version, field="outputPort.version")
        key = (port_name, port_version)
        if key in seen_ports:
            raise ValueError("ODPS duplicate output port name and version")
        seen_ports.add(key)
        entry: dict[str, Any] = {
            "@type": "dcat:Distribution",
            "dct:title": port_name,
        }
        port_id = port.get("id")
        if port_id is not None:
            port_id = _text(port_id, field="outputPort.id")
            if port_id in seen_port_ids:
                raise ValueError("ODPS duplicate output port id")
            seen_port_ids.add(port_id)
            stable_uri = _uuid_uri(port_id)
            if stable_uri:
                entry["@id"] = stable_uri
            else:
                entry["dct:identifier"] = port_id
        if port_version is not None:
            entry["dcat:version"] = port_version
        mime = (
            _FORMATS.get(port.get("type"))
            if isinstance(port.get("type"), str)
            else None
        )
        if mime:
            entry["dct:format"] = mime
        # Output ports do NOT establish physical locations or a verifiable
        # per-port digest; those remain UNKNOWN until a producer binds them.
        distributions.append(entry)

    props = product.get("customProperties", [])
    if not isinstance(props, list):
        raise TypeError("ODPS customProperties must be a list")
    rights = [
        item.get("value")
        for item in props
        if isinstance(item, dict) and item.get("property") == "governancePolicyUid"
    ]
    if len(rights) > 1 or (
        rights and (not isinstance(rights[0], str) or not rights[0].startswith("urn:"))
    ):
        raise ValueError("ambiguous or invalid governance policy identity")
    entry = {
        "@type": "dcat:Dataset",
        "dct:identifier": product_id,
        "dct:title": name,
        "dcat:version": version,
        "dcat:distribution": distributions,
        "dct:conformsTo": {
            "@id": "https://github.com/bitol-io/open-data-product-standard"
        },
    }
    description = product.get("description")
    if isinstance(description, dict) and isinstance(description.get("purpose"), str):
        entry["dct:description"] = description["purpose"]
    if dataset_uri:
        entry["@id"] = dataset_uri
    if rights:
        entry["odrl:hasPolicy"] = {"@id": rights[0]}
    claimed_ports: set[str] = set()
    for binding in bindings:
        if binding.product_id != product_id:
            continue
        if binding.port_name in claimed_ports:
            raise ValueError("duplicate local evidence binding for output port")
        claimed_ports.add(binding.port_name)
        qualified_local_distribution(product, entry, binding)
    return entry, "sha256:" + hashlib.sha256(raw).hexdigest()


def project_catalog(
    sources: list[Path | bytes], *, bindings: tuple[LocalEvidenceBinding, ...] = ()
) -> dict[str, Any]:
    """Build an immutable-source-fingerprinted DCAT discovery view, not a registry."""
    if not sources:
        raise ValueError("no producer-owned ODPS inputs")
    entries = [project_odps(source, bindings=bindings) for source in sources]
    datasets = [entry for entry, _ in entries]
    for binding in bindings:
        if not any(entry["dct:identifier"] == binding.product_id for entry in datasets):
            raise ValueError(
                "local evidence binding refers to unprojected owner product"
            )
    keys = [(entry["dct:identifier"], entry["dcat:version"]) for entry in datasets]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate owner product identifier and version")
    datasets.sort(key=lambda entry: (entry["dct:identifier"], entry["dcat:version"]))
    source_hashes = sorted(digest for _, digest in entries)
    projection_payload = json.dumps(
        {"datasets": datasets, "sourceHashes": source_hashes},
        sort_keys=True,
        separators=(",", ":"),
    )
    catalog_digest = hashlib.sha256(projection_payload.encode("utf-8")).hexdigest()
    return {
        "@context": {
            "dcat": "http://www.w3.org/ns/dcat#",
            "dct": "http://purl.org/dc/terms/",
            "odrl": "http://www.w3.org/ns/odrl/2/",
            "spdx": "http://spdx.org/rdf/terms#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
        },
        "@id": "urn:sha256:" + catalog_digest,
        "@type": "dcat:Catalog",
        "dct:title": "Ordivon producer-owned Data Product discovery projection",
        "dct:description": "Read-only projection over declared ODPS 1.1 metadata; source bytes, rights and file availability are not validated.",
        "dct:conformsTo": {"@id": "https://www.w3.org/TR/vocab-dcat-3/"},
        "dct:source": [{"@id": "urn:" + digest} for digest in source_hashes],
        "dcat:dataset": datasets,
    }
