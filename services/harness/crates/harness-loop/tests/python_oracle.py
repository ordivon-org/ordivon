#!/usr/bin/env python3
"""Current Python source oracle. This is NOT a Rust behavioral model."""
from __future__ import annotations
import random
from types import SimpleNamespace
from ordivon_harness.ordivon.turn_projection import select_turn_tool_working_set
from ordivon_harness.ordivon.run_contract import RunBudget

rng = random.Random(26136)
catalog = ("read_workspace", "search_workspace", "edit_workspace", "read_artifact", "读取")
extra = ("not_admitted", "z_extra")
for n in range(200):
    admitted = tuple(rng.sample(catalog, rng.randrange(len(catalog) + 1)))
    defs = tuple(SimpleNamespace(name=name) for name in admitted)
    if n % 7 == 0:
        selected = None
    elif n % 7 == 1:
        selected = ()
    elif n % 7 == 2 and admitted:
        selected = (admitted[0], admitted[0])
    elif n % 7 == 3:
        selected = (extra[0], extra[1])
    else:
        pool = admitted + (extra[0],)
        selected = tuple(rng.sample(pool, rng.randrange(len(pool) + 1)))
    try:
        actual = select_turn_tool_working_set(defs, selected)
        indexes = [admitted.index(item.name) for item in actual]
        result = "ok:" + ",".join(map(str, indexes))
    except ValueError as exc:
        msg = str(exc)
        if msg == "Turn Tool Working Set names must be unique":
            result = "error:duplicate"
        elif msg.startswith("Turn Tool Working Set references Tools outside the admitted surface:"):
            missing = sorted(set(selected or ()) - set(admitted))
            result = "error:missing:" + ",".join(missing)
        else:
            raise
    display_selected = "*" if selected is None else ",".join(selected)
    print("S\t" + "\t".join(((",".join(admitted), display_selected, result))))

for n in range(200):
    prior_n = rng.randrange(16)
    prior_o = rng.randrange(16)
    max_n = rng.randrange(9)
    max_o = rng.randrange(9)
    budget = RunBudget(
        max_model_calls=8, max_tool_calls=8, max_observation_bytes=1024,
        max_wall_time_ms=10000, max_no_progress_turns=max_n,
        max_observation_only_turns=max_o,
    )
    reason = budget.observation_gate_reason(
        no_progress_turns=prior_n, observation_only_turns=prior_o
    )
    print("G\t" + "\t".join(map(str, (prior_n, prior_o, max_n, max_o))) +
          "\t" + (reason if reason is not None else "none"))
