#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
# Native package consumers and direct CLI both reuse the same source identity.
if __package__:
    from .source import (
        MCP_SCHEMA as MCP_SCHEMA,
        PLUGIN_SCHEMA as PLUGIN_SCHEMA,
        assert_regular_tree,
        canonical_bytes,
        discover_skills,
        read_json_object as read_json_object,
        sha256_bytes,
        tree_digest as tree_digest,
        tree_manifest,
        validate_plugin_skeleton,
        validate_plugin_skeleton_without_source_rule,
    )
else:
    from source import (
        MCP_SCHEMA as MCP_SCHEMA,
        PLUGIN_SCHEMA as PLUGIN_SCHEMA,
        assert_regular_tree,
        canonical_bytes,
        discover_skills,
        read_json_object as read_json_object,
        sha256_bytes,
        tree_digest as tree_digest,
        tree_manifest,
        validate_plugin_skeleton,
        validate_plugin_skeleton_without_source_rule,
    )


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
