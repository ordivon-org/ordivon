"""Canonical Agent Plugin / Skills source admission and deterministic tree identity.

This is source-only validation: package staging, external release effects and
receipt writing remain with the existing materialization entrypoint.
"""

from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path

PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def read_json_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def assert_regular_tree(root: Path, *, require_skill_md: bool = False) -> list[Path]:
    if not root.is_dir() or root.is_symlink():
        raise SystemExit(f"expected real directory: {root}")
    if require_skill_md:
        skill_md = root / "SKILL.md"
        if not skill_md.is_file() or skill_md.is_symlink():
            raise SystemExit(f"Skill directory lacks regular SKILL.md: {root}")
    files: list[Path] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        info = path.lstat()
        relative = path.relative_to(root)
        if stat.S_ISLNK(info.st_mode):
            raise SystemExit(
                f"symlink is not allowed in portable release input: {root / relative}"
            )
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            raise SystemExit(
                f"non-regular file is not allowed in portable release input: {root / relative}"
            )
        files.append(path)
    return files


def tree_manifest(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in assert_regular_tree(root):
        raw = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": len(raw),
                "sha256": sha256_bytes(raw),
            }
        )
    return rows


def tree_digest(root: Path) -> str:
    return sha256_bytes(canonical_bytes(tree_manifest(root)))


def validate_plugin_skeleton(plugin: Path) -> None:
    skills_path = plugin / "skills"
    if skills_path.exists() or skills_path.is_symlink():
        raise SystemExit(
            f"plugin skeleton must not contain a source-owned skills/ tree: {plugin}"
        )
    assert_regular_tree(plugin)
    manifest = read_json_object(plugin / "plugin.json")
    if manifest.get("$schema") != PLUGIN_SCHEMA:
        raise SystemExit(
            f"plugin.json must target Agent Plugins 1.0.0: {plugin / 'plugin.json'}"
        )
    if not isinstance(manifest.get("name"), str) or not manifest["name"].strip():
        raise SystemExit("plugin.json requires non-empty name")
    if not isinstance(manifest.get("version"), str) or not manifest["version"].strip():
        raise SystemExit("plugin.json requires non-empty version")
    mcp_path = plugin / "mcp.json"
    if mcp_path.exists():
        mcp = read_json_object(mcp_path)
        if mcp.get("$schema") != MCP_SCHEMA:
            raise SystemExit(f"mcp.json must target Agent Plugins 1.0.0: {mcp_path}")


def discover_skills(skills_root: Path) -> list[Path]:
    if not skills_root.is_dir() or skills_root.is_symlink():
        raise SystemExit(f"expected canonical Agent Skills directory: {skills_root}")
    skills: list[Path] = []
    for child in sorted(skills_root.iterdir(), key=lambda item: item.name):
        info = child.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise SystemExit(f"symlink Skill root is not allowed: {child}")
        if not stat.S_ISDIR(info.st_mode):
            raise SystemExit(
                f"canonical skills root may contain Skill directories only: {child}"
            )
        assert_regular_tree(child, require_skill_md=True)
        skills.append(child)
    if not skills:
        raise SystemExit(f"no Skills found under {skills_root}")
    return skills


def validate_plugin_skeleton_without_source_rule(plugin: Path) -> None:
    assert_regular_tree(plugin)
    manifest = read_json_object(plugin / "plugin.json")
    if manifest.get("$schema") != PLUGIN_SCHEMA:
        raise SystemExit("materialized plugin.json does not target Agent Plugins 1.0.0")
    mcp_path = plugin / "mcp.json"
    if mcp_path.exists() and read_json_object(mcp_path).get("$schema") != MCP_SCHEMA:
        raise SystemExit("materialized mcp.json does not target Agent Plugins 1.0.0")
    skill_root = plugin / "skills"
    if skill_root.exists():
        discover_skills(skill_root)
