"""Bounded public Host MCP Tool -> actual Owner operation/source selector witness.

Source-level consumer proof, not a universal Python dataflow theorem, a PDP
decision, or an installed-agent grant. No secret, database or Owner RPC.
This complements the *release* source-closure equivalence check: a malicious
unreviewed change must be detectable before the release stage as well.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from ordivon_gateway.logic.host_tool_contracts import (
    HOST_READ_SELECTORS,
    SOCIAL_WORK_HOST_TOOLS,
)

HOST_SOURCE = Path(__file__).resolve().parents[1] / "src/ordivon_gateway/capabilities/host"


def _registered_host_tool_name(node: ast.AsyncFunctionDef) -> str | None:
    names: list[str] = []
    for decorator in node.decorator_list:
        if not (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "server"
            and decorator.func.attr == "tool"
        ):
            continue
        named = [kw.value for kw in decorator.keywords if kw.arg == "name"]
        assert len(named) == 1 and not decorator.args, "dynamic or unnamed Host tool"
        literal = named[0]
        assert isinstance(literal, ast.Constant) and isinstance(literal.value, str)
        names.append(literal.value)
    assert len(names) <= 1, "ambiguous Host tool registration"
    return names[0] if names else None


def _assert_exact_host_tool_dispatch(directory: Path) -> set[str]:
    names: set[str] = set()
    for path in sorted(directory.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for method in ast.walk(tree):
            if not isinstance(method, ast.AsyncFunctionDef):
                continue
            public = _registered_host_tool_name(method)
            if public is None:
                continue
            assert public not in names, f"duplicate Host registration {public}"
            names.add(public)
            # A publicly permitted read must not be secretly forwarded to a
            # different natural Host tool. No nonliteral/dynamic Owner name.
            upstream = [
                call
                for call in ast.walk(method)
                if isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "_host"
            ]
            assert len(upstream) == 1, f"{public}: missing/ambiguous Owner delegation"
            effect = upstream[0]
            assert len(effect.args) == 2 and not effect.keywords, public
            assert isinstance(effect.args[0], ast.Constant) and effect.args[0].value == public, (
                f"{public}: public action != delegated Owner tool"
            )
            payload = effect.args[1]
            assert isinstance(payload, ast.Dict), f"{public}: dynamic delegated argument map"
            forwarded = {}
            for key, value in zip(payload.keys, payload.values, strict=True):
                assert isinstance(key, ast.Constant) and isinstance(key.value, str), public
                assert key.value not in forwarded, f"{public}: duplicate delegated field"
                forwarded[key.value] = value
            parameters = {
                arg.arg
                for arg in (*method.args.posonlyargs, *method.args.args, *method.args.kwonlyargs)
            }
            assert set(forwarded) == parameters, (
                f"{public}: delegated field set differs from public signature"
            )
            normalized = {
                ("work.create", "initialSnapshot"): "verified_snapshot",
                ("work.snapshot.commit", "snapshot"): "verified_snapshot",
                ("work.list", "limit"): "verified_limit",
            }
            for key, value in forwarded.items():
                if key in HOST_READ_SELECTORS.get(public, ()):
                    continue  # checked below with selector-specific diagnostic
                expected = normalized.get((public, key), key)
                assert isinstance(value, ast.Name) and value.id == expected, (
                    f"{public}: forwarded argument {key} is not its public value"
                )
            # The PEP binds a read to these canonical selectors. A different
            # actual object must not be substituted after authorization.
            for selector in HOST_READ_SELECTORS.get(public, ()):
                target = forwarded.get(selector)
                assert isinstance(target, ast.Name) and target.id == selector, (
                    f"{public}: authorized selector {selector} changed before Owner call"
                )
    assert names == SOCIAL_WORK_HOST_TOOLS, (
        f"Host registered tools do not match original natural Owner registry: "
        f"missing={sorted(SOCIAL_WORK_HOST_TOOLS - names)}, "
        f"unreviewed={sorted(names - SOCIAL_WORK_HOST_TOOLS)}"
    )
    return names


def test_every_registered_host_action_and_read_selector_matches_actual_owner_call() -> None:
    assert len(_assert_exact_host_tool_dispatch(HOST_SOURCE)) == len(SOCIAL_WORK_HOST_TOOLS)


@pytest.mark.parametrize(
    ("filename", "old", "bad", "diagnostic"),
    [
        (
            "work.py",
            'return await _host("work.get", {"workRef": workRef, "revision": revision})',
            'return await _host("work.snapshot.commit", '
            '{"workRef": workRef, "revision": revision})',
            "public action != delegated Owner tool",
        ),
        (
            "social.py",
            '"includeArchived": includeArchived,',
            '"includeArchived": True,',
            "forwarded argument includeArchived",
        ),
        (
            "social.py",
            '"topic.resume",\n            {\n                "topicRef": topicRef,',
            '"topic.resume",\n            {\n                "topicRef": forgedTopicRef,',
            "authorized selector topicRef changed",
        ),
    ],
)
def test_adversarial_source_changes_break_public_owner_consumer_congruence(
    tmp_path: Path, filename: str, old: str, bad: str, diagnostic: str
) -> None:
    # Source-only, never run the mutated Gateway or invoke a Host effect.
    for path in HOST_SOURCE.glob("*.py"):
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path = tmp_path / filename
    source = path.read_text(encoding="utf-8")
    assert old in source
    path.write_text(source.replace(old, bad, 1), encoding="utf-8")
    with pytest.raises(AssertionError, match=diagnostic):
        _assert_exact_host_tool_dispatch(tmp_path)


def test_unreviewed_registered_host_action_cannot_bypass_natural_owner_registry(
    tmp_path: Path,
) -> None:
    for path in HOST_SOURCE.glob("*.py"):
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "unexpected.py").write_text(
        "async def register_tools(server, _host):\n"
        '    @server.tool(name="host.unreviewed")\n'
        "    async def unreviewed():\n"
        '        return await _host("host.unreviewed", {})\n',
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="unreviewed"):
        _assert_exact_host_tool_dispatch(tmp_path)
