package governance.philosophy

misuse_rules := [
    {"id": "PGI-MISUSE-001", "keywords": ["long-term", "long term", "longterm"], "danger": ["ignore sleep", "sacrifice body", "sacrifice the body", "no rest", "burn out"], "desc": "Long-termism used to rationalize overwork or body neglect"},
    {"id": "PGI-MISUSE-002", "keywords": ["freedom"], "danger": ["all-in", "all in", "high leverage", "gamble", "double down"], "desc": "Freedom language used to rationalize gambling"},
    {"id": "PGI-MISUSE-003", "keywords": ["discipline"], "danger": ["ignore fatigue", "suppress emotion", "ignore emotion", "push through pain"], "desc": "Discipline used to suppress body/emotion signals"},
    {"id": "PGI-MISUSE-004", "keywords": ["existential", "meaning", "destiny"], "danger": ["ignore evidence", "skip evidence", "bypass evidence"], "desc": "Meaning language used to bypass evidence"},
    {"id": "PGI-MISUSE-005", "keywords": ["non-attachment", "non attachment", "wu wei", "daoism", "let it flow"], "danger": ["avoid responsibility", "no review", "do nothing"], "desc": "Non-attachment used to avoid responsibility"},
    {"id": "PGI-MISUSE-006", "keywords": ["pragmatism"], "danger": ["ignore principle", "skip evidence", "bypass boundary", "shortcut"], "desc": "Pragmatism used to justify unprincipled shortcuts"},
]

default allow := true

check_file(content, path) := findings if {
    lower_content := lower(content)
    findings := [{
        "severity": "WARN", "finding_id": r.id,
        "description": sprintf("%s in %s", [r.desc, path]),
        "affected_file": path,
    } | r := misuse_rules[_]; kw := r.keywords[_]; dw := r.danger[_]; contains(lower_content, lower(kw)); contains(lower_content, lower(dw))]
}
