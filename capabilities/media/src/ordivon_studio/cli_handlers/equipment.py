"""Equipment discovery, selection and provider routing CLI handlers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import _write_json


def _equipment_module():
    from .. import equipment
    return equipment


def _command_equipment_inventory(args: argparse.Namespace) -> int:
    module = _equipment_module()
    world = module.load_equipment_world(Path(args.world))
    inventory = module.discover_equipment(world)
    _write_json(inventory)
    return 0


def _command_equipment_select(args: argparse.Namespace) -> int:
    from .. import equipment_capabilities

    module = _equipment_module()
    world = module.load_equipment_world(Path(args.world))
    inventory = module.discover_equipment_for_capability(world, args.capability) if args.local else None
    _write_json({"capability": args.capability, "matches": equipment_capabilities.select_for_capability(world, args.capability, inventory=inventory)})
    return 0


def _command_equipment_coverage(args: argparse.Namespace) -> int:
    from .. import equipment_capabilities

    module = _equipment_module()
    world = module.load_equipment_world(Path(args.world))
    _write_json(equipment_capabilities.capability_coverage(world))
    return 0


def _command_equipment_providers(args: argparse.Namespace) -> int:
    from .. import equipment_capabilities

    module = _equipment_module()
    world = module.load_equipment_world(Path(args.world))
    _write_json(equipment_capabilities.local_provider_surface(world))
    return 0


def _command_equipment_plan(args: argparse.Namespace) -> int:
    module = _equipment_module()
    parameters = json.loads(args.parameters) if args.parameters else {}
    _write_json(module.compile_operation(args.equipment_id, args.capability, parameters).as_dict())
    return 0


def _command_equipment_propose(args: argparse.Namespace) -> int:
    module = _equipment_module()
    world = module.load_equipment_world(Path(args.world))
    parameters = json.loads(args.parameters) if args.parameters else {}
    proposal = module.propose_operation(
        world,
        args.capability,
        parameters,
        equipment_id=args.equipment_id,
        local=not args.no_local,
    )
    _write_json(proposal)
    return 0 if proposal.get("ready") else 3


def _command_figma_route(args: argparse.Namespace) -> int:
    from ..figma_provider import route_figma_operation
    _write_json(route_figma_operation(
        args.operation, desktop_state=args.desktop_state, remote_state=args.remote_state, prefer_local=not args.prefer_remote
    ).as_dict())
    return 0
