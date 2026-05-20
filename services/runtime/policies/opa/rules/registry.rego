package governance.registry

valid_authorities := {"source_of_truth", "current_status", "supporting_evidence", "proposal", "bootstrap"}
required_fields := {"doc_id", "path", "title", "doc_type", "status", "authority"}
doc_types := {"receipt": true, "audit": true, "architecture": true, "methodology": true, "schema": true, "note": true, "proposal": true, "supporting_evidence": true, "bootstrap": true, "current_status": true, "source_of_truth": true}

default allow := true

# ── Validate entry structure ──
validate_entry(entry) := findings if {
    missing := {f | f := required_fields[_]; not entry[f]}
    f_missing := [{"severity": "BLOCKING", "finding_id": "REG-MISSING-FIELD", "description": sprintf("Missing: %s", [f])} | f := missing[_]]
    dt := object.get(entry, "doc_type", "")
    f_dt := [{"severity": "BLOCKING", "finding_id": "REG-INVALID-DOC-TYPE", "description": sprintf("Invalid doc_type: %s", [dt])} | dt != ""; not doc_types[dt]]
    auth := object.get(entry, "authority", "")
    f_auth := [{"severity": "BLOCKING", "finding_id": "REG-INVALID-AUTHORITY", "description": sprintf("Invalid authority: %s", [auth])} | auth != ""; not valid_authorities[auth]]
    nc := object.get(entry, "not_claimed", [])
    f_nc := [{"severity": "WARN", "finding_id": "REG-EMPTY-NOT-CLAIMED", "description": "not_claimed field is empty"} | count(nc) == 0]
    findings := array.concat(f_missing, array.concat(f_dt, array.concat(f_auth, f_nc)))
}

# ── Check freshness ──
check_freshness(entry, today_iso) := findings if {
    last_verified := object.get(entry, "last_verified", "")
    stale_days := object.get(entry, "stale_after_days", 0)
    findings := [{"severity": "WARN", "finding_id": "REG-STALE", "description": sprintf("Stale entry %s: last_verified=%s, stale_after=%d days", [object.get(entry, "doc_id", "?"), last_verified, stale_days])} | last_verified != ""; stale_days > 0; today_iso > last_verified]
}

# ── Full validation ──
validate_registry(entries) := all_findings if {
    f1 := [f | e := entries[_]; f := validate_entry(e)[_]]
    all_findings := f1
}
