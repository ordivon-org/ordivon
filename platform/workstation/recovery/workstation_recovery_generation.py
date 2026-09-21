#!/usr/bin/env python3
"""Materialize and verify an immutable Workstation-owned monorepo recovery generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import Any

DEFAULT_INSTALL_ROOT = Path("/opt/ordivon-workstation-recovery")
MANIFEST_NAME = "generation.json"


class RecoveryGenerationError(RuntimeError):
    pass


def _run(args: list[str]) -> str:
    proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RecoveryGenerationError(
            f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stdout}{proc.stderr}"
        )
    return proc.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _repository_root(owner_source: str | Path) -> Path:
    owner = Path(owner_source).resolve()
    if owner.is_symlink() or not owner.is_dir():
        raise RecoveryGenerationError(f"Workstation recovery owner source is unavailable: {owner}")
    root = Path(_run(["/usr/bin/git", "-C", str(owner), "rev-parse", "--show-toplevel"])).resolve()
    try:
        owner.relative_to(root)
    except ValueError as error:
        raise RecoveryGenerationError(
            f"Workstation recovery owner is outside its Git repository: {owner}"
        ) from error
    return root


def _source_binding(repository: str | Path) -> dict[str, Any]:
    root = Path(repository).resolve()
    if root.is_symlink() or not (root / ".git").exists():
        raise RecoveryGenerationError(f"Workstation recovery source is not a Git worktree: {root}")
    revision = _run(["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"])
    tree = _run(["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD^{tree}"])
    status = _run(
        ["/usr/bin/git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"]
    )
    return {
        "path": str(root),
        "revision": revision,
        "tree": tree,
        "clean": not bool(status),
        "dirtyPathCount": len(status.splitlines()) if status else 0,
    }


def _owner_relative(repository: Path, owner: Path) -> str:
    relative = owner.resolve().relative_to(repository.resolve())
    return relative.as_posix() or "."


def _config(owner_source: Path) -> dict[str, Any]:
    cfg = tomllib.loads((owner_source / "recovery/recovery.toml").read_text())
    recovery = cfg.get("recovery")
    if not isinstance(recovery, dict):
        raise RecoveryGenerationError("Workstation recovery config is absent")
    required = {
        "control_repository",
        "primary_repository",
        "restic_mirror",
        "restic_password_file",
        "control_snapshot_tag",
        "semantic_repository",
        "backup_generation_root",
        "retain_control_snapshots",
    }
    missing = sorted(required - set(recovery))
    if missing:
        raise RecoveryGenerationError(f"Workstation recovery generation config missing: {missing}")
    return recovery


def recovery_contract_digest(owner_root: str | Path) -> str:
    owner = Path(owner_root).resolve()
    cfg = tomllib.loads((owner / "recovery/recovery.toml").read_text())
    recovery = cfg.get("recovery")
    if not isinstance(recovery, dict):
        raise RecoveryGenerationError("Workstation recovery config is absent")
    external_paths = {
        name: list(value.get("recovery_paths", []))
        for name, value in sorted((cfg.get("external_apps") or {}).items())
        if isinstance(value, dict) and value.get("recovery_paths")
    }
    owner_capsules = {
        name: dict(value)
        for name, value in sorted((cfg.get("owner_capsules") or {}).items())
        if isinstance(value, dict)
    }
    generation_recovery = {
        key: value
        for key, value in recovery.items()
        if key not in {"timer_enabled", "timer_policy_reason"}
    }
    payload = {
        "recovery": generation_recovery,
        "externalRecoveryPaths": external_paths,
        "ownerCapsules": owner_capsules,
        "implementation": {
            "backup_authority_material.py": _sha256(owner / "recovery/backup_authority_material.py"),
            "backup_semantic_state.py": _sha256(owner / "recovery/backup_semantic_state.py"),
            "owner_capsule_recovery.py": _sha256(owner / "recovery/owner_capsule_recovery.py"),
            "restic_mirror_verify.py": _sha256(owner / "recovery/restic_mirror_verify.py"),
            "workstation_recovery_generation.py": _sha256(
                owner / "recovery/workstation_recovery_generation.py"
            ),
        },
    }
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _launcher_text(
    *,
    source_repository: Path,
    owner_relative: str,
    revision: str,
    tree: str,
    recovery: dict[str, Any],
) -> str:
    control = str(recovery["control_repository"])
    control_tag = str(recovery["control_snapshot_tag"])
    primary = str(recovery["primary_repository"])
    mirror = str(recovery["restic_mirror"])
    password = str(recovery["restic_password_file"])
    retain_control = int(recovery["retain_control_snapshots"])
    if retain_control < 1:
        raise RecoveryGenerationError("retain_control_snapshots must be >= 1")
    return f'''#!/usr/bin/env bash
set -euo pipefail
SOURCE_REPOSITORY={shlex.quote(str(source_repository))}
OWNER_RELATIVE={shlex.quote(owner_relative)}
OWNER_ROOT="$SOURCE_REPOSITORY/$OWNER_RELATIVE"
CONTROL_REPOSITORY={shlex.quote(control)}
PRIMARY_REPOSITORY={shlex.quote(primary)}
MIRROR_REPOSITORY={shlex.quote(mirror)}
PASSWORD_FILE={shlex.quote(password)}
RETAIN_CONTROL_SNAPSHOTS={retain_control}
CONTROL_SNAPSHOT_TAG={shlex.quote(control_tag)}
EXPECTED_REVISION={revision}
EXPECTED_TREE={tree}
export GIT_OPTIONAL_LOCKS=0
export PYTHONDONTWRITEBYTECODE=1
[ -d "$SOURCE_REPOSITORY/.git" ] || {{ echo "Workstation recovery generation source unavailable: $SOURCE_REPOSITORY" >&2; exit 70; }}
[ -d "$OWNER_ROOT/recovery" ] || {{ echo "Workstation recovery owner source unavailable: $OWNER_ROOT" >&2; exit 70; }}
[ "$(/usr/bin/git -C "$SOURCE_REPOSITORY" rev-parse HEAD)" = "$EXPECTED_REVISION" ] || {{ echo "Workstation recovery generation revision drift" >&2; exit 71; }}
[ "$(/usr/bin/git -C "$SOURCE_REPOSITORY" rev-parse 'HEAD^{{tree}}')" = "$EXPECTED_TREE" ] || {{ echo "Workstation recovery generation tree drift" >&2; exit 71; }}
[ -z "$(/usr/bin/git -C "$SOURCE_REPOSITORY" status --porcelain=v1 --untracked-files=all)" ] || {{ echo "Workstation recovery generation source is dirty" >&2; exit 71; }}
/usr/bin/mountpoint -q /mnt/d || {{ echo "Workstation recovery target /mnt/d is not mounted" >&2; exit 72; }}
[ -d "$CONTROL_REPOSITORY/.git" ] || {{ echo "Canonical monorepo control repository unavailable: $CONTROL_REPOSITORY" >&2; exit 73; }}
[ -s "$PASSWORD_FILE" ] || {{ echo "Workstation restic password file unavailable" >&2; exit 74; }}

/usr/bin/python3 "$OWNER_ROOT/recovery/backup_authority_material.py" --apply
BACKUP_JSON=$(/usr/bin/mktemp /tmp/ordivon-workstation-backup.XXXXXX.json)
trap '/usr/bin/rm -f "$BACKUP_JSON"' EXIT
RESTIC_REPOSITORY="$PRIMARY_REPOSITORY" RESTIC_PASSWORD_FILE="$PASSWORD_FILE" \
  /usr/bin/restic --no-cache backup "$CONTROL_REPOSITORY" --tag "$CONTROL_SNAPSHOT_TAG" --json \
  --exclude "$CONTROL_REPOSITORY/.git/worktrees" > "$BACKUP_JSON"
PRIMARY_SNAPSHOT_ID=$(/usr/bin/python3 "$OWNER_ROOT/recovery/restic_mirror_verify.py" extract-id "$BACKUP_JSON")
RESTIC_REPOSITORY="$MIRROR_REPOSITORY" RESTIC_PASSWORD_FILE="$PASSWORD_FILE" \
  /usr/bin/restic --no-cache copy --from-repo "$PRIMARY_REPOSITORY" --from-password-file "$PASSWORD_FILE" "$PRIMARY_SNAPSHOT_ID"
/usr/bin/python3 "$OWNER_ROOT/recovery/restic_mirror_verify.py" verify \
  --primary-repository "$PRIMARY_REPOSITORY" --mirror-repository "$MIRROR_REPOSITORY" \
  --password-file "$PASSWORD_FILE" --source-snapshot-id "$PRIMARY_SNAPSHOT_ID" --tag "$CONTROL_SNAPSHOT_TAG"
RESTIC_REPOSITORY="$PRIMARY_REPOSITORY" RESTIC_PASSWORD_FILE="$PASSWORD_FILE" \
  /usr/bin/restic --no-cache forget --tag "$CONTROL_SNAPSHOT_TAG" --group-by tags --keep-last "$RETAIN_CONTROL_SNAPSHOTS" --prune
RESTIC_REPOSITORY="$MIRROR_REPOSITORY" RESTIC_PASSWORD_FILE="$PASSWORD_FILE" \
  /usr/bin/restic --no-cache forget --tag "$CONTROL_SNAPSHOT_TAG" --group-by tags --keep-last "$RETAIN_CONTROL_SNAPSHOTS" --prune
/usr/bin/python3 "$OWNER_ROOT/recovery/backup_semantic_state.py" --apply
'''


def _owner_capsule_launcher_text(
    *, source_repository: Path, owner_relative: str, revision: str, tree: str
) -> str:
    return f'''#!/usr/bin/env bash
set -euo pipefail
SOURCE_REPOSITORY={shlex.quote(str(source_repository))}
OWNER_RELATIVE={shlex.quote(owner_relative)}
OWNER_ROOT="$SOURCE_REPOSITORY/$OWNER_RELATIVE"
EXPECTED_REVISION={revision}
EXPECTED_TREE={tree}
export GIT_OPTIONAL_LOCKS=0
export PYTHONDONTWRITEBYTECODE=1
[ -d "$SOURCE_REPOSITORY/.git" ] || {{ echo "Workstation recovery generation source unavailable: $SOURCE_REPOSITORY" >&2; exit 70; }}
[ -d "$OWNER_ROOT/recovery" ] || {{ echo "Workstation recovery owner source unavailable: $OWNER_ROOT" >&2; exit 70; }}
[ "$(/usr/bin/git -C "$SOURCE_REPOSITORY" rev-parse HEAD)" = "$EXPECTED_REVISION" ] || {{ echo "Workstation recovery generation revision drift" >&2; exit 71; }}
[ "$(/usr/bin/git -C "$SOURCE_REPOSITORY" rev-parse 'HEAD^{{tree}}')" = "$EXPECTED_TREE" ] || {{ echo "Workstation recovery generation tree drift" >&2; exit 71; }}
[ -z "$(/usr/bin/git -C "$SOURCE_REPOSITORY" status --porcelain=v1 --untracked-files=all)" ] || {{ echo "Workstation recovery generation source is dirty" >&2; exit 71; }}
exec /usr/bin/python3 "$OWNER_ROOT/recovery/owner_capsule_recovery.py" "$@"
'''


def _atomic_current(install_root: Path, generation_name: str) -> None:
    current = install_root / "current"
    temp = install_root / f".current.{os.getpid()}"
    temp.unlink(missing_ok=True)
    temp.symlink_to(generation_name, target_is_directory=True)
    os.replace(temp, current)


def _generation_id(revision: str, owner_relative: str) -> str:
    suffix = owner_relative.replace("/", "-").replace(".", "root")
    return f"workstation-recovery://git/{revision}/{suffix}"


def verify_generation(generation_root: str | Path, *, require_current: bool = False) -> dict[str, Any]:
    root = Path(generation_root).resolve()
    manifest_path = root / MANIFEST_NAME
    if root.is_symlink() or not root.is_dir() or manifest_path.is_symlink() or not manifest_path.is_file():
        raise RecoveryGenerationError(f"incomplete Workstation recovery generation: {root}")
    manifest = json.loads(manifest_path.read_text())
    required = {
        "schemaVersion",
        "kind",
        "generationId",
        "source",
        "ownerRelativePath",
        "launcher",
        "ownerCapsuleLauncher",
        "recoveryContractDigest",
        "controlRepository",
        "primaryRepository",
        "mirrorRepository",
        "semanticRepository",
        "createdFrom",
    }
    if not isinstance(manifest, dict) or set(manifest) != required or manifest.get("schemaVersion") != 1:
        raise RecoveryGenerationError("Workstation recovery generation manifest has unsupported shape")
    if manifest.get("kind") != "ordivon.workstation.recovery-generation.v1":
        raise RecoveryGenerationError("Workstation recovery generation manifest kind mismatch")

    source_repository = root / "source"
    binding = _source_binding(source_repository)
    expected_source = manifest["source"]
    if not binding["clean"]:
        raise RecoveryGenerationError("Workstation recovery installed source is dirty")
    if (
        binding["revision"] != expected_source.get("revision")
        or binding["tree"] != expected_source.get("tree")
    ):
        raise RecoveryGenerationError("Workstation recovery source binding mismatch")

    owner_relative = str(manifest["ownerRelativePath"])
    owner_root = (source_repository / owner_relative).resolve()
    try:
        owner_root.relative_to(source_repository.resolve())
    except ValueError as error:
        raise RecoveryGenerationError("Workstation recovery owner path escapes source repository") from error
    if not (owner_root / "recovery").is_dir():
        raise RecoveryGenerationError("Workstation recovery owner source is unavailable")

    contract_digest = recovery_contract_digest(owner_root)
    if manifest.get("recoveryContractDigest") != contract_digest:
        raise RecoveryGenerationError("Workstation recovery contract digest mismatch")

    launcher = root / "bin/workstation-backup"
    if launcher.is_symlink() or not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise RecoveryGenerationError("Workstation recovery launcher is unavailable")
    if _sha256(launcher) != manifest["launcher"].get("sha256"):
        raise RecoveryGenerationError("Workstation recovery launcher digest mismatch")

    owner_launcher = root / "bin/owner-capsule-recovery"
    if owner_launcher.is_symlink() or not owner_launcher.is_file() or not os.access(owner_launcher, os.X_OK):
        raise RecoveryGenerationError("Owner capsule recovery launcher is unavailable")
    if _sha256(owner_launcher) != manifest["ownerCapsuleLauncher"].get("sha256"):
        raise RecoveryGenerationError("Owner capsule recovery launcher digest mismatch")

    generation_id = _generation_id(binding["revision"], owner_relative)
    if manifest.get("generationId") != generation_id:
        raise RecoveryGenerationError("Workstation recovery generation identity mismatch")

    current = root.parent / "current"
    current_exact = current.is_symlink() and current.resolve() == root
    if require_current and not current_exact:
        raise RecoveryGenerationError("Workstation recovery generation is not current")

    created_from = manifest["createdFrom"]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.recovery-generation-verification.v1",
        "status": "pass",
        "path": str(root),
        "generationId": generation_id,
        "sourceRevision": binding["revision"],
        "sourceTree": binding["tree"],
        "sourceRepository": str(created_from["sourceRepositoryPath"]),
        "ownerSource": str(created_from["ownerSourcePath"]),
        "ownerRelativePath": owner_relative,
        "launcherSha256": _sha256(launcher),
        "ownerCapsuleLauncherSha256": _sha256(owner_launcher),
        "recoveryContractDigest": contract_digest,
        "controlRepository": manifest["controlRepository"],
        "primaryRepository": manifest["primaryRepository"],
        "mirrorRepository": manifest["mirrorRepository"],
        "semanticRepository": manifest["semanticRepository"],
        "current": current_exact,
    }


def provision_generation(
    owner_root: str | Path,
    *,
    install_root: str | Path | None = None,
    activate: bool = True,
) -> dict[str, Any]:
    owner = Path(owner_root).resolve()
    repository = _repository_root(owner)
    owner_relative = _owner_relative(repository, owner)
    binding = _source_binding(repository)
    if not binding["clean"]:
        raise RecoveryGenerationError(
            "Workstation recovery generation can only be provisioned from clean source"
        )

    recovery = _config(owner)
    configured_root = Path(str(recovery["backup_generation_root"])).resolve()
    install = Path(install_root).resolve() if install_root is not None else configured_root
    install.mkdir(parents=True, exist_ok=True)
    final = install / binding["revision"]

    if final.exists():
        verified = verify_generation(final)
        if activate:
            _atomic_current(install, binding["revision"])
            verified = verify_generation(final, require_current=True)
        return {"replayed": True, **verified}

    stage = Path(tempfile.mkdtemp(prefix=f".{binding['revision'][:12]}.", dir=install))
    try:
        installed_source = stage / "source"
        _run(["/usr/bin/git", "clone", "--no-local", "--no-checkout", str(repository), str(installed_source)])
        _run(
            [
                "/usr/bin/git",
                "-C",
                str(installed_source),
                "checkout",
                "--detach",
                binding["revision"],
            ]
        )
        installed_binding = _source_binding(installed_source)
        if not installed_binding["clean"] or installed_binding["tree"] != binding["tree"]:
            raise RecoveryGenerationError(
                "installed Workstation recovery source does not match source tree"
            )

        installed_owner = (installed_source / owner_relative).resolve()
        if not (installed_owner / "recovery").is_dir():
            raise RecoveryGenerationError(
                "installed Workstation recovery owner source is unavailable"
            )

        launcher = stage / "bin/workstation-backup"
        launcher.parent.mkdir(parents=True)
        launcher.write_text(
            _launcher_text(
                source_repository=final / "source",
                owner_relative=owner_relative,
                revision=binding["revision"],
                tree=binding["tree"],
                recovery=recovery,
            )
        )
        launcher.chmod(0o755)

        owner_launcher = stage / "bin/owner-capsule-recovery"
        owner_launcher.write_text(
            _owner_capsule_launcher_text(
                source_repository=final / "source",
                owner_relative=owner_relative,
                revision=binding["revision"],
                tree=binding["tree"],
            )
        )
        owner_launcher.chmod(0o755)

        manifest = {
            "schemaVersion": 1,
            "kind": "ordivon.workstation.recovery-generation.v1",
            "generationId": _generation_id(binding["revision"], owner_relative),
            "source": {"revision": binding["revision"], "tree": binding["tree"]},
            "ownerRelativePath": owner_relative,
            "launcher": {"relativePath": "bin/workstation-backup", "sha256": _sha256(launcher)},
            "ownerCapsuleLauncher": {
                "relativePath": "bin/owner-capsule-recovery",
                "sha256": _sha256(owner_launcher),
            },
            "recoveryContractDigest": recovery_contract_digest(installed_owner),
            "controlRepository": str(recovery["control_repository"]),
            "primaryRepository": str(recovery["primary_repository"]),
            "mirrorRepository": str(recovery["restic_mirror"]),
            "semanticRepository": str(recovery["semantic_repository"]),
            "createdFrom": {
                "sourceRepositoryPath": str(repository),
                "ownerSourcePath": str(owner),
            },
        }
        (stage / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        os.replace(stage, final)

        verified = verify_generation(final)
        if activate:
            _atomic_current(install, binding["revision"])
            verified = verify_generation(final, require_current=True)
        return {"replayed": False, **verified}
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Provision or verify the immutable Workstation-owned monorepo recovery generation."
    )
    parser.add_argument("--install-root", type=Path)
    parser.add_argument("--verify-current", action="store_true")
    parser.add_argument("--no-activate", action="store_true")
    args = parser.parse_args()

    owner = Path(__file__).resolve().parents[1]
    if args.verify_current:
        recovery = _config(owner)
        install = (
            args.install_root.resolve()
            if args.install_root is not None
            else Path(str(recovery["backup_generation_root"])).resolve()
        )
        current = install / "current"
        if not current.is_symlink():
            raise SystemExit(f"Workstation recovery current generation is absent: {current}")
        result = verify_generation(current.resolve(), require_current=True)
    else:
        result = provision_generation(
            owner, install_root=args.install_root, activate=not args.no_activate
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
