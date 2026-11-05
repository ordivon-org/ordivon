extends Node

# Upstream Dialogue Manager is given this native port, not an independent token ledger.
var rules: Node
var tokens: int:
    get:
        return 1 if rules != null and rules.snapshot()["phase"] == "cleared" else 0

func bind_rules(source: Node) -> void:
    rules = source

func spend_token() -> void:
    if rules != null and rules.snapshot()["phase"] == "cleared":
        rules.advance()
