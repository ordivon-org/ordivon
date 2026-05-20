#!/usr/bin/env python3
"""Advisory checker: mcp-permissions

Scans MCP server configurations and tool registries for permission gaps.
Advisory only — produces warnings, never blocks.

Checks:
- M5 tools without human approval gate
- MCP servers without permission manifest
- Destructive tools without receipt_required
- Third-party sources without trust classification

Usage:
    python3 checkers/mcp-permissions/run.py [--path mcp/]
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

M5_TOOLS = ["deploy", "delete", "merge", "force_push", "rotate_secret", 
            "execute_trade", "send_email", "publish_release", "drop_table",
            "delete_branch", "update_protected_branch", "modify_permissions"]

M4_TOOLS = ["create_pr", "update_notion", "create_issue", "comment", 
            "draft_email", "modify_jira", "push"]

WARNINGS = []
PASS = True


def check_mcp_config(path: Path) -> None:
    global PASS
    try:
        data = json.loads(path.read_text()) if path.suffix == ".json" else None
    except Exception:
        data = None
    
    if data is None:
        # Check yaml/json/permissions files with text patterns
        content = path.read_text().lower()
        
        for tool in M5_TOOLS:
            if tool in content:
                # Check if human approval is mentioned nearby
                if "approval" not in content and "human" not in content and "confirm" not in content:
                    WARNINGS.append(f"  {path.name}: M5 tool '{tool}' found without approval reference")
                    PASS = False
        
        if "mcp" in content or "connector" in content:
            if "permission" not in content and "manifest" not in content:
                WARNINGS.append(f"  {path.name}: MCP config found without permission manifest")
                PASS = False
            if "trust" not in content and "review" not in content and "source" not in content:
                WARNINGS.append(f"  {path.name}: MCP config found without trust classification")
                PASS = False
        
        return
    
    # Structured JSON check
    for tool in data.get("tools", []):
        tool_name = tool.get("name", tool.get("id", ""))
        tool_perm = tool.get("permission", tool.get("level", ""))
        
        if tool_name.lower() in [t.lower() for t in M5_TOOLS]:
            if tool.get("approval_required") is not True:
                WARNINGS.append(f"  {path.name}: M5 tool '{tool_name}' missing approval_required=true")
                PASS = False
            if tool.get("receipt_required") is not True:
                WARNINGS.append(f"  {path.name}: M5 tool '{tool_name}' missing receipt_required=true")
                PASS = False
    
    server_source = data.get("source", data.get("origin", ""))
    if server_source and "third-party" in str(server_source).lower():
        if data.get("trust_level") is None and data.get("reviewed") is not True:
            WARNINGS.append(f"  {path.name}: third-party source without trust classification or review")
            PASS = False


def check_tool_file(path: Path) -> None:
    """Check Python tool files for M5 operations without permission checks."""
    global PASS
    content = path.read_text()
    
    for tool in M5_TOOLS:
        if tool in content.lower():
            if "approval" not in content.lower() and "authoriz" not in content.lower():
                WARNINGS.append(f"  {path.name}: M5 keyword '{tool}' in tool without approval check")
                PASS = False


def main():
    target = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "--path" else (
        sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "mcp"))
    
    if "--path" in sys.argv:
        idx = sys.argv.index("--path")
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else str(ROOT / "mcp")
    
    target_path = Path(target)
    
    print("=== mcp-permissions advisory check ===")
    
    if not target_path.exists():
        print(f"Target not found: {target}")
        print("(This is expected — mcp/ directory is reserved but empty)")
        print("Checker loaded and ready for future MCP configurations.")
        sys.exit(0)
    
    for config_file in sorted(target_path.rglob("*")):
        if config_file.is_file() and config_file.suffix in (".json", ".yaml", ".yml", ".toml"):
            print(f"\n--- {config_file.relative_to(ROOT)} ---")
            check_mcp_config(config_file)
    
    # Also check scripts/ for M5 tool usage
    scripts_dir = ROOT / "scripts"
    if scripts_dir.exists():
        for py_file in scripts_dir.rglob("*.py"):
            check_tool_file(py_file)
    
    print(f"\n=== Result: {'PASS' if PASS else 'ADVISORY WARNINGS'} ===")
    if WARNINGS:
        print(f"  {len(WARNINGS)} advisory finding(s):")
        for w in WARNINGS:
            print(w)
        print("\n  These are ADVISORY only — not blocking gates.")
        print("  M5 tools without approval gates are a supply-chain and overreach risk.")
    else:
        print("  No permission gaps detected.")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
