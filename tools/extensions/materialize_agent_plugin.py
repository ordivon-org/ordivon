#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT
DEFAULT_PLUGIN = REPO_ROOT / "extensions" / "ordivon-control-plane"
DEFAULT_SKILLS = REPO_ROOT / ".agents" / "skills"
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


def git_head() -> str | None:
    git = shutil.which("git")
    if git is None:
        return None
    try:
        return subprocess.check_output(
            [git, "-C", str(ROOT), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except OSError, subprocess.CalledProcessError:
        return None


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


def copy_regular_tree(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for path in assert_regular_tree(source):
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        os.chmod(target, stat.S_IMODE(path.stat().st_mode) & 0o755)


def materialize(
    plugin: Path,
    skills_root: Path | None,
    output: Path,
    receipt: Path,
    *,
    selected_skill_names: list[str] | None = None,
) -> dict:
    plugin = plugin.resolve(strict=True)
    resolved_skills_root = None
    if skills_root is not None:
        if DEFAULT_SKILLS.is_symlink() or not DEFAULT_SKILLS.is_dir():
            raise SystemExit(
                f"canonical Agent Skills root must be a real directory: {DEFAULT_SKILLS}"
            )
        canonical_skills_root = DEFAULT_SKILLS.resolve(strict=True)
        if skills_root.is_symlink():
            raise SystemExit(f"skills source must not be a symlink: {skills_root}")
        resolved_skills_root = skills_root.resolve(strict=True)
        if resolved_skills_root != canonical_skills_root:
            raise SystemExit(
                f"skills source must be the canonical Agent Skills root: {canonical_skills_root}"
            )
    output = output.resolve(strict=False)
    receipt = receipt.resolve(strict=False)

    if output.exists():
        raise SystemExit(f"output already exists; refusing overwrite: {output}")
    if receipt.exists():
        raise SystemExit(f"receipt already exists; refusing overwrite: {receipt}")
    if output == plugin or plugin in output.parents:
        raise SystemExit("output must not be inside the canonical plugin source tree")
    if resolved_skills_root is not None and (
        output == resolved_skills_root or resolved_skills_root in output.parents
    ):
        raise SystemExit("output must not be inside the canonical Skill source tree")
    if receipt == output or output in receipt.parents:
        raise SystemExit("receipt must remain outside the portable plugin package")

    validate_plugin_skeleton(plugin)
    skills = (
        discover_skills(resolved_skills_root)
        if resolved_skills_root is not None
        else []
    )
    selected_names: list[str] | None = None
    if selected_skill_names is not None:
        if resolved_skills_root is None:
            raise SystemExit(
                "selected Skills require the canonical Agent Skills source"
            )
        selected_names = sorted(set(selected_skill_names))
        if not selected_names:
            raise SystemExit("selected Skills must contain at least one Skill name")
        by_name = {skill.name: skill for skill in skills}
        missing = [name for name in selected_names if name not in by_name]
        if missing:
            raise SystemExit(
                "selected Skill is not present in canonical Agent Skills source: "
                + ", ".join(missing)
            )
        skills = [by_name[name] for name in selected_names]

    output.parent.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="agent-plugin-release-", dir=output.parent
    ) as tmp_name:
        staged = Path(tmp_name) / "package"
        copy_regular_tree(plugin, staged)
        if skills:
            skill_destination = staged / "skills"
            skill_destination.mkdir()
            for skill in skills:
                copy_regular_tree(skill, skill_destination / skill.name)

        # Re-check the final package before publishing it from the staging directory.
        validate_plugin_skeleton_without_source_rule(staged)
        final_manifest = tree_manifest(staged)
        final_digest = sha256_bytes(canonical_bytes(final_manifest))
        os.replace(staged, output)

    skill_rows = []
    for skill in skills:
        package_manifest = tree_manifest(skill)
        skill_rows.append(
            {
                "name": skill.name,
                "sourceRelativePath": skill.relative_to(REPO_ROOT).as_posix()
                if REPO_ROOT in skill.parents
                else str(skill),
                "packageDigest": sha256_bytes(canonical_bytes(package_manifest)),
                "fileCount": len(package_manifest),
            }
        )
    skill_source = None
    if resolved_skills_root is not None:
        skill_source = (
            resolved_skills_root.relative_to(REPO_ROOT).as_posix()
            if REPO_ROOT in resolved_skills_root.parents
            else str(resolved_skills_root)
        )
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.agent-plugin-release-materialization-receipt",
        "sourceOfTruth": ".agents/skills" if resolved_skills_root is not None else None,
        "sourceGitRevision": git_head(),
        "pluginSource": plugin.relative_to(REPO_ROOT).as_posix()
        if REPO_ROOT in plugin.parents
        else str(plugin),
        "skillComposition": (
            "selected"
            if selected_names is not None
            else ("included" if resolved_skills_root is not None else "omitted")
        ),
        "skillSelection": selected_names,
        "skillSource": skill_source,
        "skillCount": len(skill_rows),
        "skills": skill_rows,
        "outputTreeDigest": final_digest,
        "outputFileCount": len(final_manifest),
        "portableSemantics": (
            "Agent Plugins 1.0; Agent Skills may be explicitly composed into a release without making "
            "the plugin their semantic owner. This receipt is external release evidence and is not part "
            "of the portable plugin package."
        ),
    }
    receipt.write_bytes(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
        + b"\n"
    )
    return value


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize a disposable Agent Plugins release directory. Agent Skills are composed only "
            "when --skill or --include-skills is explicitly requested."
        )
    )
    parser.add_argument("--plugin", type=Path, default=DEFAULT_PLUGIN)
    skill_mode = parser.add_mutually_exclusive_group()
    skill_mode.add_argument("--include-skills", action="store_true")
    skill_mode.add_argument(
        "--skill",
        action="append",
        default=[],
        help="Compose one named canonical Agent Skill; repeat for multiple Skills.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = args.receipt or args.output.with_name(args.output.name + ".receipt.json")
    selected_skill_names = args.skill or None
    skills_root = (
        DEFAULT_SKILLS
        if args.include_skills or selected_skill_names is not None
        else None
    )
    value = materialize(
        args.plugin,
        skills_root,
        args.output,
        receipt,
        selected_skill_names=selected_skill_names,
    )
    print(
        json.dumps(
            {"output": str(args.output), "receipt": str(receipt), **value},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
