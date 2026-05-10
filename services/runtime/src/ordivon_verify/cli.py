"""Ordivon Verify — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ordivon_verify.config import is_ordivon_native, load_config, resolve_profile_context, validate_config
from ordivon_verify.discovery import (
    SUPPORTED_TEMPLATE_TIERS,
    discover_external_evidence,
    emit_template_pack,
    render_discovery_markdown,
    render_discovery_summary,
)
from ordivon_verify.report import (
    build_report,
    determine_status,
    print_human,
    render_markdown,
    render_summary,
    status_to_exit_code,
)
from ordivon_verify.runner import (
    _ensure_all_checks,
    _get_all_gate_ids,
    _get_readonly_gate_ids,
    _get_entry,
)
from ordivon_verify import runner as _runner

_BUILTIN_ROOT = Path(__file__).resolve().parents[2]


def _parse_unknown(parser, unknown: list[str], ns) -> None:
    i = 0
    while i < len(unknown):
        u = unknown[i]
        if u == "--json":
            ns.json = True
        elif u == "--markdown":
            ns.markdown = True
        elif u == "--root":
            i += 1
            if i >= len(unknown):
                parser.error("--root requires a path argument")
            ns.root = unknown[i]
        elif u == "--config":
            i += 1
            if i >= len(unknown):
                parser.error("--config requires a path argument")
            ns.config = unknown[i]
        elif u == "--mode":
            i += 1
            if i >= len(unknown):
                parser.error("--mode requires a value (advisory, standard, strict)")
            ns.mode = unknown[i]
        elif u == "--suggest-config":
            ns.suggest_config = True
        elif u == "--standard-pack":
            ns.standard_pack = True
        elif u == "--template":
            i += 1
            if i >= len(unknown):
                parser.error("--template requires a value (minimal, standard, deep)")
            ns.template = unknown[i]
        elif u == "--emit-template-dir":
            i += 1
            if i >= len(unknown):
                parser.error("--emit-template-dir requires a directory path")
            ns.emit_template_dir = unknown[i]
        elif u == "--profile":
            i += 1
            if i >= len(unknown):
                parser.error("--profile requires a value")
            ns.profile = unknown[i]
        elif u == "--risk-stage":
            i += 1
            if i >= len(unknown):
                parser.error("--risk-stage requires a value (vibe, merge, release)")
            ns.risk_stage = unknown[i]
        elif u == "--summary":
            ns.summary = True
        elif u == "--full":
            ns.full = True
        else:
            parser.error(f"unrecognized arguments: {u}")
        i += 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ordivon-verify", description="Ordivon Verify — local read-only verification CLI"
    )
    sub = parser.add_subparsers(dest="command", title="commands")
    sub.add_parser("all", help="Run read-only checks (receipts + debt + gates + docs)")
    check_parser = sub.add_parser("check", help="Run read-only checks against a target root")
    check_parser.add_argument("target", nargs="?", help="Project root to verify")
    run_parser = sub.add_parser("run", help="Run a specific checker by gate_id")
    run_parser.add_argument("gate_id", help="Checker gate_id (e.g. receipt_integrity)")
    # Legacy subcommands
    sub.add_parser("receipts", help="Scan receipts for contradictions")
    sub.add_parser("debt", help="Check debt ledger invariants")
    sub.add_parser("gates", help="Verify gate manifest integrity")
    sub.add_parser("docs", help="Check document registry + semantic safety")
    ri_parser = sub.add_parser("registry-index", help="Generate unified registry control plane index (JSON)")
    ri_parser.add_argument("--check", action="store_true", help="Exit non-zero if BLOCKED > 0 (CI gate)")
    ri_parser.add_argument("--snapshot", action="store_true", help="Write index snapshot for future diff")
    ri_parser.add_argument("--diff", action="store_true", help="Compare current index vs last snapshot")
    dg_parser = sub.add_parser("document-governance", help="Run DGP document governance check (CI gate)")
    dg_parser.add_argument("--check", action="store_true", help="CI mode: exit non-zero on BLOCKED")
    dg_parser.add_argument("--summary", action="store_true", help="Compact status output")
    dg_parser.add_argument("--full", action="store_true", help="Full findings with details")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--markdown", action="store_true", help="Output Markdown trust report")
    parser.add_argument(
        "--suggest-config", action="store_true", help="Discover external evidence and print a suggested config"
    )
    parser.add_argument(
        "--standard-pack", action="store_true", help="Include a read-only standard governance pack draft"
    )
    parser.add_argument("--template", type=str, default=None, help="Template tier: minimal, standard, deep")
    parser.add_argument("--emit-template-dir", type=str, default=None, help="Write template pack to this directory")
    parser.add_argument("--profile", type=str, default=None, help="Profile: coding")
    parser.add_argument("--risk-stage", type=str, default=None, help="Risk stage: vibe, merge, release")
    parser.add_argument("--summary", action="store_true", help="Output compact trust summary")
    parser.add_argument("--full", action="store_true", help="Include full evidence appendix in Markdown output")
    parser.add_argument("--root", type=str, default=None, help="Project root directory")
    parser.add_argument("--config", type=str, default=None, help="Path to ordivon.verify.json")
    parser.add_argument("--mode", type=str, default=None, help="Mode: advisory, standard, strict")
    known, unknown = parser.parse_known_args(argv)
    if unknown:
        _parse_unknown(parser, unknown, known)
    return known


def _profile_stage_results(evidence_report: dict, config: dict, profile_context: dict) -> list[dict]:
    """Return Coding Trust Profile stage checks derived from read-only discovery."""
    stage = profile_context["risk_stage"]
    if stage == "vibe":
        return []

    inv = evidence_report.get("inventory", {})
    results: list[dict] = []
    bindings = inv.get("agent_claim_bindings", {})
    binding_items = bindings.get("items", [])
    non_ready_bindings = [item for item in binding_items if item.get("trust_signal") != "READY_WITHOUT_AUTHORIZATION"]
    if not bindings.get("binding_file"):
        results.append({
            "id": "agent_claim_bindings",
            "label": "Agent Claim Bindings",
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": "No agent claim binding file found for merge/release-stage coding trust audit",
            "missing_evidence": True,
            "next_action": "Add agent_claims.jsonl binding each claim to artifacts, tests, receipt, and review evidence.",
        })
    elif non_ready_bindings:
        results.append({
            "id": "agent_claim_bindings",
            "label": "Agent Claim Bindings",
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": f"{len(non_ready_bindings)} agent claim binding(s) lack complete evidence",
        })

    if not config.get("gate_manifest"):
        results.append({
            "id": "coding_profile_gate_manifest",
            "label": "Coding Profile Gate Manifest",
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": "No confirmed gate_manifest configured for merge/release-stage coding trust audit",
            "missing_evidence": True,
            "next_action": "Confirm canonical test/lint/security gates and configure gate_manifest.",
        })

    if stage != "release":
        return results

    release = inv.get("release_claim_audit", {})
    release_counts = release.get("status_counts", {})
    release_weak = release_counts.get("missing", 0) + release_counts.get("blocked", 0)
    if release_weak:
        results.append({
            "id": "release_claim_audit",
            "label": "Release Claim Audit",
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": f"{release_weak} release claim(s) need evidence mapping before release-stage audit",
        })

    skills = inv.get("skills", {})
    skill_failures = skills.get("status_counts", {}).get("FAIL", 0)
    if skill_failures:
        results.append({
            "id": "skill_safety",
            "label": "Skill Safety",
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": f"{skill_failures} skill safety finding(s) require owner disposition before release-stage audit",
        })
    memory = inv.get("memory_content_hygiene", {})
    memory_blockers = memory.get("status_counts", {}).get("BLOCKED", 0)
    if memory_blockers:
        results.append({
            "id": "memory_content_hygiene",
            "label": "Memory / Content Hygiene",
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": f"{memory_blockers} memory/content record(s) contain stale source, scope, or authority confusion",
        })
    harness = inv.get("harness_evidence_import", {})
    harness_blockers = harness.get("status_counts", {}).get("BLOCKED", 0)
    if harness_blockers:
        results.append({
            "id": "harness_evidence_import",
            "label": "Harness Evidence Import",
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": f"{harness_blockers} trace/checkpoint bundle(s) contain missing failures or authorization leakage",
        })
    return results


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit:
        return 3

    command = args.command or "all"
    target_root = getattr(args, "target", None) if command == "check" else None
    root = Path(args.root or target_root).resolve() if (args.root or target_root) else _BUILTIN_ROOT
    if not root.is_dir():
        print(f"Root directory not found: {root}", file=sys.stderr)
        return 3

    if args.template and args.template not in SUPPORTED_TEMPLATE_TIERS:
        print(f"Invalid template: {args.template}", file=sys.stderr)
        return 3
    if args.emit_template_dir and not args.suggest_config:
        print("--emit-template-dir requires --suggest-config", file=sys.stderr)
        return 3

    if args.suggest_config:
        risk_stage = args.risk_stage or "vibe"
        template_tier = args.template or "standard"
        include_template_pack = args.standard_pack or args.template is not None or args.emit_template_dir is not None
        suggestion = discover_external_evidence(
            root,
            include_standard_pack=include_template_pack,
            risk_stage=risk_stage,
            template_tier=template_tier,
        )
        if args.emit_template_dir:
            try:
                emit_result = emit_template_pack(
                    suggestion["standard_pack_draft"], Path(args.emit_template_dir).resolve()
                )
            except Exception as exc:
                print(f"Template emit error: {exc}", file=sys.stderr)
                return 4
            suggestion["template_emit"] = emit_result
        if args.summary:
            print(render_discovery_summary(suggestion), end="")
        elif args.markdown:
            print(render_discovery_markdown(suggestion), end="")
        else:
            print(json.dumps(suggestion, indent=2))
        return 0

    config_path = Path(args.config) if args.config else None
    if config_path and not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return 3
    config = load_config(config_path, root)
    if config_path and config is None:
        print(f"Config parse error: {config_path}", file=sys.stderr)
        return 3
    if config is None:
        auto_config_path = root / "ordivon.verify.json"
        if auto_config_path.exists():
            print(f"Config parse error: {auto_config_path}", file=sys.stderr)
            return 3

    mode = args.mode or (config.get("mode", "") if config else "")
    if not mode:
        mode = "standard" if is_ordivon_native(root) else "advisory"
    if mode not in ("advisory", "standard", "strict"):
        print(f"Invalid mode: {mode}", file=sys.stderr)
        return 3

    if config:
        config_errors = validate_config(config)
        if config_errors:
            print(f"Config error: {'; '.join(config_errors)}", file=sys.stderr)
            return 3
    else:
        config = {}
    profile_context, profile_errors = resolve_profile_context(config, args.profile, args.risk_stage, mode)
    if profile_errors:
        print(f"Profile error: {'; '.join(profile_errors)}", file=sys.stderr)
        return 3

    if command in ("all", "check"):
        _ensure_all_checks()
        check_ids = _get_readonly_gate_ids()
    elif command == "run":
        gate_id = getattr(args, "gate_id", None)
        if not gate_id:
            print("Missing gate_id. Usage: ordivon-verify run <gate_id>", file=sys.stderr)
            return 3
        entry = _get_entry(gate_id)
        if not entry:
            available = ", ".join(_get_all_gate_ids())
            print(f"Unknown checker: {gate_id}", file=sys.stderr)
            print(f"Available: {available}", file=sys.stderr)
            return 3
        check_ids = [gate_id]
    elif command in ("receipts", "debt", "gates", "docs"):
        check_ids = [command]
    elif command == "registry-index":
        # RG-8: generate unified registry control plane index
        from ordivon_verify.registry.reconciler import generate_registry_index
        import json as _json

        index = generate_registry_index(root)

        # RG-18: --check flag for CI: exit non-zero if BLOCKED > 0
        if getattr(args, "check", False):
            blocked = index["summary"]["blocked_findings"]
            degraded = index["summary"]["degraded_findings"]
            routed = index["summary"].get("routed_by_inheritance", 0)
            print(f"BLOCKED={blocked} DEGRADED={degraded} ROUTED={routed}")
            if blocked > 0:
                print(f"FAIL: {blocked} BLOCKED findings — hard gate failed", file=sys.stderr)
                print("Gate: --check exits nonzero only on BLOCKED > 0.", file=sys.stderr)
                print("      DEGRADED is advisory. Use --strict for degraded gate.", file=sys.stderr)
                print("      This is NOT merge/release/deploy authorization.", file=sys.stderr)
                return 1
            print("PASS: 0 BLOCKED")
            print("Gate: BLOCKED=0 — hard gate passed.")
            print(f"      DEGRADED={degraded} (advisory) ROUTED={routed} (by inheritance)")
            print("      This is NOT merge/release/deploy authorization.")
            return 0

        # RG-18: --snapshot flag: write index to .ordivon/registry/last-index.json for diff
        if getattr(args, "snapshot", False):
            snap_dir = root / ".ordivon" / "registry"
            snap_dir.mkdir(parents=True, exist_ok=True)
            snap_path = snap_dir / "last-index.json"
            snap_path.write_text(_json.dumps(index, indent=2))
            print(f"Snapshot written: {snap_path}")
            return 0

        # RG-18: --diff flag: compare current vs last snapshot
        if getattr(args, "diff", False):
            snap_path = root / ".ordivon" / "registry" / "last-index.json"
            if not snap_path.exists():
                print("No snapshot found. Run --snapshot first.", file=sys.stderr)
                return 3
            import json as _json

            prev = _json.loads(snap_path.read_text())
            prev_ids = set(prev.get("objects", {}).keys())
            curr_ids = set(index.get("objects", {}).keys())
            new_objects = curr_ids - prev_ids
            removed_objects = prev_ids - curr_ids
            print(f"New objects: {len(new_objects)}")
            if new_objects:
                for nid in sorted(new_objects)[:20]:
                    obj = index["objects"].get(nid, {})
                    print(f"  + {nid} ({obj.get('kind', '?')}) {obj.get('path', '')}")
            print(f"Removed objects: {len(removed_objects)}")
            if removed_objects:
                for rid in sorted(removed_objects)[:10]:
                    print(f"  - {rid}")
            return 0 if len(new_objects) == 0 else 0  # --diff is advisory

        print(_json.dumps(index, indent=2))
        return 0
    elif command == "document-governance":
        # DGP-9: document governance CI check — wraps registry-index + DGP layer reporting
        from ordivon_verify.registry.reconciler import generate_registry_index
        import json as _json

        index = generate_registry_index(root)
        blocked = index["summary"]["blocked_findings"]
        degraded = index["summary"]["degraded_findings"]
        routed = index["summary"].get("routed_by_inheritance", 0)
        checks = index["summary"].get("by_check", {})
        # Show ALL registered checks, not just ones with findings
        from ordivon_verify.registry.reconciler import _RECONCILER_CHECKS

        total_checks = len(_RECONCILER_CHECKS)
        check_names = [c[0] for c in _RECONCILER_CHECKS]

        dgp_layers = {
            "DGP-1": "Registry Control Plane Foundation",
            "DGP-2": "Document Lifecycle Governance",
            "DGP-3": "Current Truth / Authority Governance",
            "DGP-4": "AI Onboarding / Context Governance",
            "DGP-5": "Receipt / Stage Summit Governance",
            "DGP-6": "Format / Medium Governance",
            "DGP-7": "Archive / Tombstone / Metabolism",
            "DGP-8": "Knowledge Map / Navigation Governance",
        }

        is_check = getattr(args, "check", False)
        is_summary = getattr(args, "summary", False)
        is_full = getattr(args, "full", False)

        if is_check:
            print("Document Governance Check:")
            print(f"  BLOCKED={blocked}  DEGRADED={degraded}  ROUTED={routed}")
            print(f"  DGP layers: {len(dgp_layers)} governed")
            print(f"  Checks active: {total_checks}")
            for cn in check_names:
                cnt = checks.get(cn, 0)
                print(f"    {cn}: {cnt}")
            if blocked > 0:
                print(f"\nFAIL: {blocked} BLOCKED findings", file=sys.stderr)
                return 1
            print("\nPASS: 0 BLOCKED")
            print("Gate: --check exits nonzero only on BLOCKED > 0.")
            print("      DEGRADED is advisory unless --strict is used.")
            print("      This is NOT merge/release/deploy authorization.")
            return 0
        elif is_summary:
            print(f"Document Governance: BLOCKED={blocked} DEGRADED={degraded} ROUTED={routed}")
            print("DGP layers active: DGP-1→DGP-8")
            print(f"Reconciler checks: {total_checks}")
            print("Command: ordivon-verify registry-index --check")
            return 0
        elif is_full:
            print("=== Document Governance Full Report ===")
            print(f"BLOCKED: {blocked}")
            print(f"DEGRADED: {degraded}")
            print(f"ROUTED (by inheritance): {routed}")
            print(f"Objects: {index['summary']['total_objects']}")
            print("\nDGP Layers:")
            for layer, desc in dgp_layers.items():
                print(f"  {layer}: {desc}")
            print(f"\nReconciler checks: {total_checks}")
            for cn in check_names:
                cnt = checks.get(cn, 0)
                print(f"  {cn}: {cnt} findings")
            if index.get("findings"):
                print("\nTop findings:")
                for f in index["findings"][:10]:
                    print(f"  [{f['status']}] {f['invariant']}: {f['message'][:100]}")
            print("\nNon-authorization boundary:")
            print("  Report is generated_view. Not merge/release/deploy authorization.")
            return 0
        else:
            print(
                json.dumps(
                    {
                        "document_governance": {
                            "blocked": blocked,
                            "degraded": degraded,
                            "routed": routed,
                            "checks": checks,
                            "dgp_layers": list(dgp_layers.keys()),
                        },
                        "registry_index": index["summary"],
                    },
                    indent=2,
                )
            )
            return 0
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 3

    try:
        native = is_ordivon_native(root)
        if command in ("all", "check") and not native:
            check_ids = ["receipts", "debt", "gates", "docs"]
        if native and not (args.root or target_root):
            results = [_runner.run_check(cid) for cid in check_ids]
        elif native:
            results = [_runner.run_check(cid, root) for cid in check_ids]
        else:
            results = []
            for cid in check_ids:
                if cid == "receipts":
                    receipt_paths = config.get("receipt_paths", []) if config else []
                    if receipt_paths:
                        results.append(_runner.run_external_receipts(receipt_paths, root))
                    else:
                        receipts_required = mode in ("standard", "strict")
                        results.append({
                            "id": "receipts",
                            "label": "Receipt Integrity",
                            "status": "FAIL" if receipts_required else "WARN",
                            "exit_code": -1,
                            "stdout": "",
                            "stderr": "No receipt_paths configured",
                            "missing_evidence": True,
                            "next_action": "Configure receipt_paths so Ordivon can verify agent work claims.",
                        })
                else:
                    results.append(_runner.run_external_checker(cid, root, mode, config))
            evidence_report = discover_external_evidence(
                root,
                include_standard_pack=False,
                risk_stage=profile_context["risk_stage"],
            )
            results.extend(_profile_stage_results(evidence_report, config, profile_context))

        status = determine_status(results)
        root_str = str(root)
        cfg_str = str(config_path) if config_path else None
        evidence_appendix = {}
        if "evidence_report" in locals():
            inv = evidence_report.get("inventory", {})
            evidence_appendix = {
                "agent_claim_bindings": inv.get("agent_claim_bindings", {}),
                "release_claim_audit": inv.get("release_claim_audit", {}),
                "skills": inv.get("skills", {}),
                "memory_content_hygiene": inv.get("memory_content_hygiene", {}),
                "harness_evidence_import": inv.get("harness_evidence_import", {}),
                "gate_manifest_candidates": inv.get("gate_manifest_candidates", []),
                "agent_native_risk_matrix": inv.get("agent_native_risk_matrix", []),
            }

        if args.json:
            report = build_report(results, mode, root_str, cfg_str, profile_context, evidence_appendix)
            print(json.dumps(report, indent=2))
        elif args.summary:
            report = build_report(results, mode, root_str, cfg_str, profile_context, evidence_appendix)
            print(render_summary(report), end="")
        elif args.markdown:
            report = build_report(results, mode, root_str, cfg_str, profile_context, evidence_appendix)
            print(render_markdown(report, full=args.full), end="")
        else:
            print_human(results, mode, root_str, cfg_str)

        return status_to_exit_code(status)
    except Exception as exc:
        print(f"Runtime error: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
