#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

workspace = Path(os.environ["ORDIVON_EVAL_WORKSPACE"])
source = workspace / "feature_flags.py"
spec = importlib.util.spec_from_file_location("candidate_feature_flags", source)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load candidate feature_flags.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if module.alpha_enabled() is not False:
    raise SystemExit("alpha_enabled must remain False")
if module.beta_enabled() is not True:
    raise SystemExit("beta_enabled must become True")
if sorted(name for name in vars(module) if name.endswith("_enabled")) != [
    "alpha_enabled",
    "beta_enabled",
]:
    raise SystemExit("public enabled-function surface changed")
print("hidden verifier: PASS")
