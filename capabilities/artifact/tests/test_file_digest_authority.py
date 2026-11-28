from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
STANDALONE_DIGEST_AUTHORITIES = {
    "artifact_openxml_external_evidence.py",
    "artifact_openxml_validator_wrapper.py",
    "artifact_python_wrapper.py",
}
CANONICAL_DIGEST_CONSUMERS = {
    "artifact_openxml_environment.py",
    "artifact_software_release.py",
    "artifact_software_release_elf.py",
    "artifact_temporal_launch.py",
}



def _is_plain_stream_sha256(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    has_sha256_constructor = False
    has_file_open = False
    returns_bare_hexdigest = False

    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                node.func.attr == "sha256"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "hashlib"
            ):
                has_sha256_constructor = True
            if node.func.attr == "open":
                has_file_open = True
        if (
            isinstance(node, ast.Return)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "hexdigest"
        ):
            returns_bare_hexdigest = True

    return has_sha256_constructor and has_file_open and returns_bare_hexdigest



def _is_direct_read_bytes_sha256(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if len(function.body) != 1 or not isinstance(function.body[0], ast.Return):
        return False
    returned = function.body[0].value
    if not (
        isinstance(returned, ast.Call)
        and isinstance(returned.func, ast.Attribute)
        and returned.func.attr == "hexdigest"
        and isinstance(returned.func.value, ast.Call)
    ):
        return False
    digest_call = returned.func.value
    if not (
        isinstance(digest_call.func, ast.Attribute)
        and digest_call.func.attr == "sha256"
        and isinstance(digest_call.func.value, ast.Name)
        and digest_call.func.value.id == "hashlib"
    ):
        return False
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "read_bytes"
        for node in ast.walk(digest_call)
    )

def test_file_sha256_has_one_authority() -> None:
    offenders: list[str] = []
    observed_standalone: set[str] = set()
    governed = CANONICAL_DIGEST_CONSUMERS | STANDALONE_DIGEST_AUTHORITIES
    for name in sorted(governed):
        path = SCRIPTS / name
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        local_helpers = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and (
                _is_plain_stream_sha256(node)
                or _is_direct_read_bytes_sha256(node)
            )
        ]
        if name in STANDALONE_DIGEST_AUTHORITIES:
            if local_helpers:
                observed_standalone.add(name)
            continue
        offenders.extend(
            f"{path.relative_to(ROOT)}:{node.lineno}:{node.name}"
            for node in local_helpers
        )

    assert observed_standalone == STANDALONE_DIGEST_AUTHORITIES, (
        "standalone digest exceptions are deployment-boundary contracts; "
        "remove an exception when its carrier can depend on artifact_core"
    )
    assert offenders == [], (
        "governed repository-bound file SHA-256 helpers must reuse "
        "artifact_core.contracts.sha256_file; "
        f"duplicate implementations: {offenders}"
    )
