"""Independent generated observations for native release evidence."""
from pathlib import Path
import sys

import pytest
from hypothesis import given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "providers/gluetun"))
from release_unit_evidence import require_loaded_identity

FRAGMENT = Path("/etc/systemd/system/test-evidence.service")
EXPECTED = [
    "LoadState=loaded",
    "FragmentPath=" + str(FRAGMENT),
    "DropInPaths=",
    "NeedDaemonReload=no",
]


@settings(max_examples=50, derandomize=True, database=None, deadline=None)
@given(st.permutations(EXPECTED))
def test_native_metadata_permutation_is_not_semantic_change(lines):
    require_loaded_identity("\n".join(lines), FRAGMENT)


@settings(max_examples=100, derandomize=True, database=None, deadline=None)
@given(st.permutations(EXPECTED), st.integers(0,3),
       st.sampled_from(["omit","duplicate","foreign","invalid"]))
def test_metadata_mutation_cannot_be_qualified(lines, index, mutation):
    rows = list(lines)
    if mutation == "omit":
        rows.pop(index)
    elif mutation == "duplicate":
        rows.append(rows[index])
    elif mutation == "foreign":
        rows.append("Unexpected=loaded")
    else:
        key = rows[index].split("=",1)[0]
        rows[index] = key + "=unqualified"
    with pytest.raises(ValueError):
        require_loaded_identity("\n".join(rows), FRAGMENT)
