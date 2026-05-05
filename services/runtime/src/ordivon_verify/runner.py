"""Ordivon Verify — check orchestration runner.

Uses checker registry for auto-discovery. No manual CHECKER_SCRIPTS dict.
Adding a checker: create checkers/<name>/ with CHECKER.md + run.py. Done.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

# Lazy import to avoid import issues with scripts/ordivon_verify.py shadow
_CHECKER_ENTRIES: dict[str, Any] | None = None


def _load_registry() -> dict[str, Any]:
    """Load checker entries from the checker ecosystem registry.

    Returns {gate_id: CheckerEntry}. Memoized — only discovers once per process.
    """
    global _CHECKER_ENTRIES
    if _CHECKER_ENTRIES is not None:
        return _CHECKER_ENTRIES

    import importlib.util
    _src = Path(__file__).resolve().parents[1]
    _spec = importlib.util.spec_from_file_location(
        "ordivon_verify.checker_registry",
        _src / "ordivon_verify" / "checker_registry.py",
    )
    _mod = importlib.util.module_from_spec(_spec)
    # Ensure package chain so @dataclass works when this is loaded from
    # scripts/ordivon_verify.py, without clobbering the real package when
    # runner.py is imported normally by tests or library users.
    existing_pkg = sys.modules.get("ordivon_verify")
    if existing_pkg is None or not hasattr(existing_pkg, "__path__"):
        _pkg = type(sys)("ordivon_verify")
        _pkg.__path__ = [str(_src / "ordivon_verify")]
        _pkg.__package__ = "ordivon_verify"
        sys.modules["ordivon_verify"] = _pkg
    sys.modules["ordivon_verify.checker_registry"] = _mod
    _spec.loader.exec_module(_mod)

    _CHECKER_ENTRIES = _mod.discover_checkers()
    return _CHECKER_ENTRIES


def _get_entry(gate_id: str):
    entries = _load_registry()
    return entries.get(gate_id)


def _get_all_gate_ids() -> list[str]:
    return sorted(_load_registry().keys())


# ── Compatibility: expose gate_id-based interface for CLI ────────────

ALL_CHECKS: list[str] = []   # populated lazily


class _CheckerScriptsCompat(dict):
    """Lazy compatibility mapping for legacy tests and callers.

    The checker ecosystem no longer has a hand-maintained CHECKER_SCRIPTS
    table. Some product tests and older integrations still import the symbol,
    so this mapping materializes gate_id -> run.py Path from the registry on
    first use.
    """

    def _refresh(self) -> None:
        if dict.__len__(self) > 0:
            return
        for gate_id, entry in _load_registry().items():
            if entry.file_path:
                super().__setitem__(gate_id, Path(entry.file_path))

        # Legacy command aliases remain valid user-facing subcommands.
        aliases = {
            "receipts": "receipt_integrity",
            "debt": "verification_debt",
            "gates": "gate_manifest",
            "docs": "document_registry",
        }
        for legacy_id, gate_id in aliases.items():
            entry = _load_registry().get(gate_id)
            if entry and entry.file_path:
                super().__setitem__(legacy_id, Path(entry.file_path))

    def items(self):
        self._refresh()
        return super().items()

    def keys(self):
        self._refresh()
        return super().keys()

    def values(self):
        self._refresh()
        return super().values()

    def __iter__(self):
        self._refresh()
        return super().__iter__()

    def __len__(self):
        self._refresh()
        return super().__len__()

    def __getitem__(self, key):
        self._refresh()
        return super().__getitem__(key)


CHECKER_SCRIPTS: dict[str, Path] = _CheckerScriptsCompat()


def _ensure_all_checks():
    if not ALL_CHECKS:
        ALL_CHECKS.extend(_get_all_gate_ids())


ROOT = Path(__file__).resolve().parents[2]


def run_check(gate_id: str, root: Path | None = None) -> dict:
    """Run a checker by gate_id as subprocess.

    Uses file_path from checker registry. Falls back to old-style
    script paths for backward compatibility.
    """
    entries = _load_registry()
    entry = entries.get(gate_id)

    if entry and entry.file_path:
        script = entry.file_path
        label = entry.display_name
    elif gate_id == "receipts":
        # Backward compat: gate_id from old CLI
        entry = entries.get("receipt_integrity")
        if entry and entry.file_path:
            script = entry.file_path
            label = entry.display_name
        else:
            script = str(ROOT / "scripts" / "check_receipt_integrity.py")
            label = "Receipt Integrity"
    elif gate_id == "debt":
        entry = entries.get("verification_debt")
        script = entry.file_path if entry else str(ROOT / "scripts" / "check_verification_debt.py")
        label = entry.display_name if entry else "Verification Debt"
    elif gate_id == "gates":
        entry = entries.get("gate_manifest")
        script = entry.file_path if entry else str(ROOT / "scripts" / "check_verification_manifest.py")
        label = entry.display_name if entry else "Gate Manifest"
    elif gate_id == "docs":
        entry = entries.get("document_registry")
        script = entry.file_path if entry else str(ROOT / "scripts" / "check_document_registry.py")
        label = entry.display_name if entry else "Document Registry"
    else:
        return {
            "id": gate_id,
            "label": gate_id,
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Unknown checker: {gate_id}",
        }

    cmd = [sys.executable, str(script)]
    cwd = str(root) if root else str(ROOT)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=cwd)
        return {
            "id": gate_id,
            "label": label,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {
            "id": gate_id, "label": label, "status": "FAIL",
            "exit_code": -1, "stdout": "",
            "stderr": f"Checker timed out: {gate_id}",
        }
    except Exception as exc:
        return {
            "id": gate_id, "label": label, "status": "FAIL",
            "exit_code": -1, "stdout": "",
            "stderr": f"Runtime error: {exc}",
        }


# ── External mode (unchanged) ────────────────────────────────────────

from ordivon_verify.checks.debt import validate_debt_ledger
from ordivon_verify.checks.docs import validate_document_registry
from ordivon_verify.checks.gates import validate_gate_manifest
from ordivon_verify.checks.receipts import scan_receipt_files

_BUILTIN_ROOT = Path(__file__).resolve().parents[2]

_WARN_ADVICE = {
    "debt": "Add verification-debt-ledger.jsonl when moving from advisory to standard mode.",
    "gates": "Add verification-gate-manifest.json before strict CI use.",
    "docs": "Add document-registry.jsonl for document governance.",
}


def run_external_receipts(receipt_paths: list[str], root: Path) -> dict:
    failures, scanned = scan_receipt_files(receipt_paths, root)
    if failures:
        return {
            "id": "receipts", "label": "Receipt Integrity", "status": "FAIL",
            "exit_code": 1, "stdout": "",
            "stderr": f"{len(failures)} contradiction(s) in {scanned} receipt(s)",
            "failures": failures,
        }
    return {
        "id": "receipts", "label": "Receipt Integrity", "status": "PASS",
        "exit_code": 0,
        "stdout": f"{scanned} receipt(s) scanned, 0 contradictions",
        "stderr": "",
    }


def run_external_checker(check_id: str, root: Path, mode: str, config: dict) -> dict:
    config_keys = {"debt": "debt_ledger", "gates": "gate_manifest", "docs": "document_registry"}
    key = config_keys.get(check_id, "")
    cfg_path = config.get(key, "") if config else ""
    target = root / cfg_path if cfg_path else None
    evidence_name = cfg_path or key or check_id
    label_map = {"receipts": "Receipt Integrity", "debt": "Verification Debt",
                 "gates": "Gate Manifest", "docs": "Document Registry"}
    label = label_map.get(check_id, check_id)

    if target and target.exists() and cfg_path:
        validators = {"debt": validate_debt_ledger, "gates": validate_gate_manifest,
                      "docs": validate_document_registry}
        try:
            result = validators[check_id](target)
        except Exception as exc:
            result = {"status": "FAIL", "exit_code": -1, "stdout": "", "stderr": f"Validation error: {exc}"}
        result["id"] = check_id
        result["label"] = label
        return result

    if mode == "strict":
        return {
            "id": check_id, "label": label, "status": "FAIL",
            "exit_code": -1, "stdout": "",
            "stderr": f"Missing required file: {target or evidence_name}",
            "missing_evidence": True,
        }
    if mode == "standard" and cfg_path:
        return {
            "id": check_id, "label": label, "status": "FAIL",
            "exit_code": -1, "stdout": "",
            "stderr": f"Configured file not found: {target or cfg_path}",
            "missing_evidence": True,
        }
    return {
        "id": check_id, "label": label, "status": "WARN",
        "exit_code": -1, "stdout": "",
        "stderr": f"Not configured: {evidence_name}",
        "missing_evidence": True,
        "next_action": _WARN_ADVICE.get(check_id, f"Configure {check_id} when ready."),
    }
