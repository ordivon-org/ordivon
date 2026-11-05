"""Optional Resolve host bridge CLI handlers.

The Resolve extra is loaded only when a Resolve action is invoked.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import _write_json


def _optional_path(value: str | None) -> Path | None:
    return Path(value) if value else None


def _resolve_adapter():
    try:
        from .. import resolve_adapter
    except ModuleNotFoundError as error:
        if error.name == "opentimelineio":
            raise RuntimeError(
                "Resolve/OTIO equipment is optional; install the 'resolve' extra "
                "or run through `uv run --extra resolve ...`"
            ) from error
        raise
    return resolve_adapter


def _command_resolve_paths(args: argparse.Namespace) -> int:
    paths = _resolve_adapter().discover_resolve_paths()
    _write_json(
        {
            "scriptsDirectory": str(paths.scripts_directory),
            "controlDirectory": str(paths.control_directory),
            "windowsControlDirectory": paths.windows_control_directory,
        }
    )
    return 0


def _command_resolve_install(args: argparse.Namespace) -> int:
    _write_json(
        _resolve_adapter().install_runner(
            scripts_directory=_optional_path(args.scripts_directory),
            control_directory=_optional_path(args.control_directory),
            windows_control_directory=args.windows_control_directory,
        )
    )
    return 0


def _command_resolve_prepare_probe(args: argparse.Namespace) -> int:
    _write_json(
        _resolve_adapter().prepare_probe(
            control_directory=_optional_path(args.control_directory),
            operation_id=args.operation_id,
        )
    )
    return 0


def _command_resolve_prepare_smoke(args: argparse.Namespace) -> int:
    _write_json(
        _resolve_adapter().prepare_smoke(
            control_directory=_optional_path(args.control_directory),
            media_path=_optional_path(args.media),
            windows_media_path=args.windows_media_path,
            operation_id=args.operation_id,
        )
    )
    return 0


def _command_resolve_prepare_compatibility(args: argparse.Namespace) -> int:
    _write_json(
        _resolve_adapter().prepare_compatibility(
            control_directory=_optional_path(args.control_directory),
            media_path=_optional_path(args.media),
            windows_media_path=args.windows_media_path,
            developer_readme_path=_optional_path(args.developer_readme),
            operation_id=args.operation_id,
        )
    )
    return 0


def _command_resolve_prepare_assembly_conform(args: argparse.Namespace) -> int:
    _write_json(
        _resolve_adapter().prepare_assembly_conform(
            production_id=args.production_id,
            production_root=_optional_path(args.production_root),
            control_directory=_optional_path(args.control_directory),
            media_root=_optional_path(args.media_root),
            windows_media_root=args.windows_media_root,
            resolve_otio_root=_optional_path(args.resolve_otio_root),
            windows_resolve_otio_root=args.windows_resolve_otio_root,
            developer_readme_path=_optional_path(args.developer_readme),
            operation_id=args.operation_id,
        )
    )
    return 0


def _command_resolve_result(args: argparse.Namespace) -> int:
    from ..resolve_results import read_result

    result = read_result(
        control_directory=_optional_path(args.control_directory),
        expected_operation_id=args.operation_id,
    )
    _write_json(result)
    return 0 if result.get("status") == "succeeded" else 1
