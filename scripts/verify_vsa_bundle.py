#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from ordivon_security_v2.signed_vsa import (
    decode_bundle_statement,
    load_trust_mapping,
    sha256_file,
    verify_vsa_semantics,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--public-key", type=Path, required=True)
    parser.add_argument("--trust-policy", type=Path, required=True)
    parser.add_argument("--subject-git-commit", required=True)
    parser.add_argument("--verifier-id", required=True)
    parser.add_argument("--verified-level", required=True)
    parser.add_argument("--expected-statement", type=Path)
    args = parser.parse_args()

    statement, signed_payload = decode_bundle_statement(args.bundle)
    expected = None if args.expected_statement is None else args.expected_statement.read_bytes()
    verify_vsa_semantics(
        statement=statement,
        expected_subject_git_commit=args.subject_git_commit,
        expected_verifier_id=args.verifier_id,
        expected_level=args.verified_level,
        public_key_sha256=sha256_file(args.public_key),
        trust_mapping=load_trust_mapping(args.trust_policy),
        expected_statement_bytes=expected,
        signed_payload_bytes=signed_payload,
    )
    print("VSA semantic verification: PASSED")
    print(f"publicKeySha256={sha256_file(args.public_key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
