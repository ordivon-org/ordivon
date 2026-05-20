package governance.architecture

forbidden_imports := {"from packs.finance.tool_refs import", "from packs.finance.policy import", "stop_loss", "max_loss_usdt", "is_chasing", "is_revenge_trade", "place_order", "execute_trade"}

core_dirs := {"governance", "state", "domains", "capabilities", "execution", "shared"}

allowed_exceptions := {"governance_engine/policy_source.py", "state/db/schema.py", "domains/finance/read_only_adapter.py"}

default allow := true

check_file(filepath, content) := findings if {
    lower_content := lower(content)
    # Check if file is in a core directory
    core_hits := {d | d := core_dirs[_]; contains(filepath, d)}
    is_core := count(core_hits) > 0
    # Check if file is an allowed exception
    exception_hits := {e | e := allowed_exceptions[_]; contains(filepath, e)}
    is_exception := count(exception_hits) > 0
    # Find forbidden imports if file is core and not excepted
    matched := {p | p := forbidden_imports[_]; is_core; not is_exception; contains(lower_content, lower(p))}
    findings := [{"severity": "BLOCKING", "finding_id": "ARCH-FORBIDDEN-IMPORT", "description": sprintf("Forbidden import '%s' in Core file %s", [p, filepath]), "affected_file": filepath} | p := matched[_]]
}
