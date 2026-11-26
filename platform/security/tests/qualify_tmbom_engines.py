"""Opt-in independent native engine pilot; not part of the Owner's runtime.

Run in an isolated supported interpreter with jsonschema and jsonschema-rs.
Do not install the latter into the Python 3.15 Owner environment.
"""

import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

from tmbom_metadata_corpus import metadata_corpus, metadata_matrix

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/owasp-threat-model-v1.0.2.schema.json"
MODEL = ROOT / "threat-models/security-v2-r1.json"
EXPECTED_SHA256 = "428772fecfed799921e90bb7e7acf7ce7bb8e379128e43c4e7f4346a528539be"


def main():
    import jsonschema_rs
    from jsonschema import Draft202012Validator

    raw = SCHEMA.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise ValueError("pinned schema digest mismatch")
    schema = json.loads(raw)
    if schema["$schema"] != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("unexpected schema dialect")

    python_engine = Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
    rust_engine = jsonschema_rs.Draft202012Validator(schema, validate_formats=True)

    def check(document, expected, label):
        actual = (python_engine.is_valid(document), rust_engine.is_valid(document))
        if actual != (expected, expected):
            raise AssertionError(f"{label}: expected {expected}, observed {actual}")

    print("ENGINE_VERSIONS", sys.version.split()[0],
          importlib.metadata.version("jsonschema"),
          importlib.metadata.version("jsonschema-rs"))
    check(json.loads(MODEL.read_bytes()), True, "actual model")
    print("ACTUAL_MODEL_BOTH_VALID")
    corpus = metadata_corpus()
    for label, document, expected in corpus:
        check(document, expected, label)
    print("INDEPENDENT_CORPUS", len(corpus), "EXPECTED", 2 * len(corpus))
    count = 0
    for count, (document, expected) in enumerate(metadata_matrix(), 1):
        check(document, expected, f"metadata coordinate {count}")
    print("INDEPENDENT_METADATA_MATRIX", count, "EXPECTED", 2 * count)


if __name__ == "__main__":
    main()
