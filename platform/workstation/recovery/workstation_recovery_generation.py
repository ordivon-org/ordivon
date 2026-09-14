#!/usr/bin/env python3
"""Materialize and verify an immutable Workstation scheduled-recovery generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import tomllib
from typing import Any

DEFAULT_INSTALL_ROOT = Path('/opt/ordivon-workstation-recovery')
MANIFEST_NAME = 'generation.json'


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
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return 'sha256:' + digest.hexdigest()


def _source_binding(source: str | Path) -> dict[str, Any]:
    root = Path(source).resolve()
    if root.is_symlink() or not (root / '.git').exists():
        raise RecoveryGenerationError(f'Workstation recovery source is not a Git worktree: {root}')
    revision = _run(['/usr/bin/git', '-C', str(root), 'rev-parse', 'HEAD'])
    tree = _run(['/usr/bin/git', '-C', str(root), 'rev-parse', 'HEAD^{tree}'])
    status = _run(['/usr/bin/git', '-C', str(root), 'status', '--porcelain=v1', '--untracked-files=all'])
    return {
        'path': str(root),
        'revision': revision,
        'tree': tree,
        'clean': not bool(status),
        'dirtyPathCount': len(status.splitlines()) if status else 0,
    }


def _config(source: Path) -> dict[str, Any]:
    cfg = tomllib.loads((source / 'recovery/recovery.toml').read_text())
    recovery = cfg.get('recovery')
    if not isinstance(recovery, dict):
        raise RecoveryGenerationError('Workstation recovery config is absent')
    required = {
        'control_repository', 'primary_repository', 'restic_mirror', 'restic_password_file', 'control_snapshot_tag',
        'semantic_repository', 'backup_generation_root', 'retain_control_snapshots',
    }
    missing = sorted(required - set(recovery))
    if missing:
        raise RecoveryGenerationError(f'Workstation recovery generation config missing: {missing}')
    return recovery


def recovery_contract_digest(source_root: str | Path) -> str:
    source = Path(source_root).resolve()
    cfg = tomllib.loads((source / 'recovery/recovery.toml').read_text())
    recovery = cfg.get('recovery')
    if not isinstance(recovery, dict):
        raise RecoveryGenerationError('Workstation recovery config is absent')
    external_paths = {
        name: list(value.get('recovery_paths', []))
        for name, value in sorted((cfg.get('external_apps') or {}).items())
        if isinstance(value, dict) and value.get('recovery_paths')
    }
    # Scheduling admission is owner policy, not recovery implementation identity.
    # Preserve the historical recovery contract unchanged except for coordinates
    # that only decide whether/why the timer is allowed to run.
    generation_recovery = {
        key: value
        for key, value in recovery.items()
        if key not in {'timer_enabled', 'timer_policy_reason'}
    }
    payload = {
        'recovery': generation_recovery,
        'externalRecoveryPaths': external_paths,
        'implementation': {
            'backup_authority_material.py': _sha256(source / 'recovery/backup_authority_material.py'),
            'backup_semantic_state.py': _sha256(source / 'recovery/backup_semantic_state.py'),
            'restic_mirror_verify.py': _sha256(source / 'recovery/restic_mirror_verify.py'),
            'workstation_recovery_generation.py': _sha256(source / 'recovery/workstation_recovery_generation.py'),
        },
    }
    encoded = (json.dumps(payload, sort_keys=True, separators=(',', ':')) + '\n').encode()
    return 'sha256:' + hashlib.sha256(encoded).hexdigest()


def _launcher_text(*, source: Path, revision: str, tree: str, recovery: dict[str, Any]) -> str:
    control = str(recovery['control_repository'])
    control_tag = str(recovery['control_snapshot_tag'])
    primary = str(recovery['primary_repository'])
    mirror = str(recovery['restic_mirror'])
    password = str(recovery['restic_password_file'])
    retain_control = int(recovery['retain_control_snapshots'])
    if retain_control < 1:
        raise RecoveryGenerationError('retain_control_snapshots must be >= 1')
    return f'''#!/usr/bin/env bash
set -euo pipefail
SOURCE={shlex.quote(str(source))}
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
[ -d "$SOURCE/.git" ] || {{ echo "Workstation recovery generation source unavailable: $SOURCE" >&2; exit 70; }}
[ "$(/usr/bin/git -C "$SOURCE" rev-parse HEAD)" = "$EXPECTED_REVISION" ] || {{ echo "Workstation recovery generation revision drift" >&2; exit 71; }}
[ "$(/usr/bin/git -C "$SOURCE" rev-parse 'HEAD^{{tree}}')" = "$EXPECTED_TREE" ] || {{ echo "Workstation recovery generation tree drift" >&2; exit 71; }}
[ -z "$(/usr/bin/git -C "$SOURCE" status --porcelain=v1 --untracked-files=all)" ] || {{ echo "Workstation recovery generation source is dirty" >&2; exit 71; }}
/usr/bin/mountpoint -q /mnt/d || {{ echo "Workstation recovery target /mnt/d is not mounted" >&2; exit 72; }}
[ -d "$CONTROL_REPOSITORY/.git" ] || {{ echo "Canonical Workstation control repository unavailable: $CONTROL_REPOSITORY" >&2; exit 73; }}
[ -s "$PASSWORD_FILE" ] || {{ echo "Workstation restic password file unavailable" >&2; exit 74; }}

/usr/bin/python3 "$SOURCE/recovery/backup_authority_material.py" --apply
BACKUP_JSON=$(/usr/bin/mktemp /tmp/ordivon-workstation-backup.XXXXXX.json)
trap '/usr/bin/rm -f "$BACKUP_JSON"' EXIT
RESTIC_REPOSITORY="$PRIMARY_REPOSITORY" RESTIC_PASSWORD_FILE="$PASSWORD_FILE" \
  /usr/bin/restic --no-cache backup "$CONTROL_REPOSITORY" --tag "$CONTROL_SNAPSHOT_TAG" --json \
  --exclude "$CONTROL_REPOSITORY/.git/worktrees" > "$BACKUP_JSON"
PRIMARY_SNAPSHOT_ID=$(/usr/bin/python3 "$SOURCE/recovery/restic_mirror_verify.py" extract-id "$BACKUP_JSON")
RESTIC_REPOSITORY="$MIRROR_REPOSITORY" RESTIC_PASSWORD_FILE="$PASSWORD_FILE" \
  /usr/bin/restic --no-cache copy --from-repo "$PRIMARY_REPOSITORY" --from-password-file "$PASSWORD_FILE" "$PRIMARY_SNAPSHOT_ID"
/usr/bin/python3 "$SOURCE/recovery/restic_mirror_verify.py" verify \
  --primary-repository "$PRIMARY_REPOSITORY" --mirror-repository "$MIRROR_REPOSITORY" \
  --password-file "$PASSWORD_FILE" --source-snapshot-id "$PRIMARY_SNAPSHOT_ID" --tag "$CONTROL_SNAPSHOT_TAG"
RESTIC_REPOSITORY="$PRIMARY_REPOSITORY" RESTIC_PASSWORD_FILE="$PASSWORD_FILE" \
  /usr/bin/restic --no-cache forget --tag "$CONTROL_SNAPSHOT_TAG" --group-by tags --keep-last "$RETAIN_CONTROL_SNAPSHOTS" --prune
RESTIC_REPOSITORY="$MIRROR_REPOSITORY" RESTIC_PASSWORD_FILE="$PASSWORD_FILE" \
  /usr/bin/restic --no-cache forget --tag "$CONTROL_SNAPSHOT_TAG" --group-by tags --keep-last "$RETAIN_CONTROL_SNAPSHOTS" --prune
/usr/bin/python3 "$SOURCE/recovery/backup_semantic_state.py" --apply
'''


def _atomic_current(install_root: Path, generation_name: str) -> None:
    current = install_root / 'current'
    temp = install_root / f'.current.{os.getpid()}'
    temp.unlink(missing_ok=True)
    temp.symlink_to(generation_name, target_is_directory=True)
    os.replace(temp, current)


def verify_generation(generation_root: str | Path, *, require_current: bool = False) -> dict[str, Any]:
    root = Path(generation_root).resolve()
    manifest_path = root / MANIFEST_NAME
    if root.is_symlink() or not root.is_dir() or manifest_path.is_symlink() or not manifest_path.is_file():
        raise RecoveryGenerationError(f'incomplete Workstation recovery generation: {root}')
    manifest = json.loads(manifest_path.read_text())
    required = {
        'schemaVersion', 'kind', 'generationId', 'source', 'launcher', 'recoveryContractDigest',
        'controlRepository', 'primaryRepository', 'mirrorRepository', 'semanticRepository', 'createdFrom',
    }
    if not isinstance(manifest, dict) or set(manifest) != required or manifest.get('schemaVersion') != 0:
        raise RecoveryGenerationError('Workstation recovery generation manifest has unsupported shape')
    if manifest.get('kind') != 'ordivon.workstation.recovery-generation.v0':
        raise RecoveryGenerationError('Workstation recovery generation manifest kind mismatch')
    source = root / 'source'
    binding = _source_binding(source)
    expected_source = manifest['source']
    if not binding['clean']:
        raise RecoveryGenerationError('Workstation recovery installed source is dirty')
    if binding['revision'] != expected_source.get('revision') or binding['tree'] != expected_source.get('tree'):
        raise RecoveryGenerationError('Workstation recovery source binding mismatch')
    contract_digest = recovery_contract_digest(source)
    if manifest.get('recoveryContractDigest') != contract_digest:
        raise RecoveryGenerationError('Workstation recovery contract digest mismatch')
    launcher = root / 'bin/workstation-backup'
    if launcher.is_symlink() or not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise RecoveryGenerationError('Workstation recovery launcher is unavailable')
    if _sha256(launcher) != manifest['launcher'].get('sha256'):
        raise RecoveryGenerationError('Workstation recovery launcher digest mismatch')
    generation_id = f"workstation-recovery://git/{binding['revision']}"
    if manifest.get('generationId') != generation_id:
        raise RecoveryGenerationError('Workstation recovery generation identity mismatch')
    current = root.parent / 'current'
    current_exact = current.is_symlink() and current.resolve() == root
    if require_current and not current_exact:
        raise RecoveryGenerationError('Workstation recovery generation is not current')
    return {
        'schemaVersion': 0,
        'kind': 'ordivon.workstation.recovery-generation-verification.v0',
        'status': 'pass',
        'path': str(root),
        'generationId': generation_id,
        'sourceRevision': binding['revision'],
        'sourceTree': binding['tree'],
        'launcherSha256': _sha256(launcher),
        'recoveryContractDigest': contract_digest,
        'controlRepository': manifest['controlRepository'],
        'primaryRepository': manifest['primaryRepository'],
        'mirrorRepository': manifest['mirrorRepository'],
        'semanticRepository': manifest['semanticRepository'],
        'current': current_exact,
    }


def provision_generation(
    source_root: str | Path,
    *,
    install_root: str | Path | None = None,
    activate: bool = True,
) -> dict[str, Any]:
    source = Path(source_root).resolve()
    binding = _source_binding(source)
    if not binding['clean']:
        raise RecoveryGenerationError('Workstation recovery generation can only be provisioned from clean source')
    recovery = _config(source)
    configured_root = Path(str(recovery['backup_generation_root'])).resolve()
    install = Path(install_root).resolve() if install_root is not None else configured_root
    install.mkdir(parents=True, exist_ok=True)
    final = install / binding['revision']
    if final.exists():
        verified = verify_generation(final)
        if activate:
            _atomic_current(install, binding['revision'])
            verified = verify_generation(final, require_current=True)
        return {'replayed': True, **verified}

    stage = Path(tempfile.mkdtemp(prefix=f'.{binding["revision"][:12]}.', dir=install))
    try:
        installed_source = stage / 'source'
        _run(['/usr/bin/git', 'clone', '--no-local', '--no-checkout', str(source), str(installed_source)])
        _run(['/usr/bin/git', '-C', str(installed_source), 'checkout', '--detach', binding['revision']])
        installed_binding = _source_binding(installed_source)
        if not installed_binding['clean'] or installed_binding['tree'] != binding['tree']:
            raise RecoveryGenerationError('installed Workstation recovery source does not match source tree')
        launcher = stage / 'bin/workstation-backup'
        launcher.parent.mkdir(parents=True)
        launcher.write_text(_launcher_text(
            source=final / 'source', revision=binding['revision'], tree=binding['tree'], recovery=recovery,
        ))
        launcher.chmod(0o755)
        manifest = {
            'schemaVersion': 0,
            'kind': 'ordivon.workstation.recovery-generation.v0',
            'generationId': f"workstation-recovery://git/{binding['revision']}",
            'source': {'revision': binding['revision'], 'tree': binding['tree']},
            'launcher': {'relativePath': 'bin/workstation-backup', 'sha256': _sha256(launcher)},
            'recoveryContractDigest': recovery_contract_digest(installed_source),
            'controlRepository': str(recovery['control_repository']),
            'primaryRepository': str(recovery['primary_repository']),
            'mirrorRepository': str(recovery['restic_mirror']),
            'semanticRepository': str(recovery['semantic_repository']),
            'createdFrom': {'sourcePath': str(source)},
        }
        (stage / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
        os.replace(stage, final)
        verified = verify_generation(final)
        if activate:
            _atomic_current(install, binding['revision'])
            verified = verify_generation(final, require_current=True)
        return {'replayed': False, **verified}
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description='Provision or verify the immutable scheduled Workstation recovery generation.')
    parser.add_argument('--install-root', type=Path)
    parser.add_argument('--verify-current', action='store_true')
    parser.add_argument('--no-activate', action='store_true')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    if args.verify_current:
        recovery = _config(source)
        install = args.install_root.resolve() if args.install_root is not None else Path(str(recovery['backup_generation_root'])).resolve()
        current = install / 'current'
        if not current.is_symlink():
            raise SystemExit(f'Workstation recovery current generation is absent: {current}')
        result = verify_generation(current.resolve(), require_current=True)
    else:
        result = provision_generation(source, install_root=args.install_root, activate=not args.no_activate)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
