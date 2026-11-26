"""Independent generated observations for native release evidence."""
from pathlib import Path
import sys

import pytest
from hypothesis import given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "providers/gluetun"))
from release_unit_evidence import require_loaded_identity, require_command, require_calendar

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

ARGV = ["/usr/bin/python3", "/example/consumer.py", "--check"]


@settings(max_examples=80, derandomize=True, database=None, deadline=None)
@given(st.lists(st.integers(0,2**64-1), min_size=4, max_size=4),
       st.integers(0,2**32-1), st.integers(-(2**31),2**31-1),
       st.integers(-(2**31),2**31-1))
def test_command_dynamic_coordinates_do_not_change_configuration(times,pid,code,status):
    raw = {"type":"a(sasbttttuii)","data":[[ARGV[0],ARGV.copy(),False,*times,pid,code,status]]}
    require_command(raw, ARGV)


@settings(max_examples=80, derandomize=True, database=None, deadline=None)
@given(st.integers(0,2**64-1))
def test_calendar_runtime_coordinate_is_not_configuration(next_elapse):
    require_calendar({"type":"a(sst)","data":[["OnCalendar","daily",next_elapse]]}, "daily")


@pytest.mark.parametrize("bad", [None, True, -1, 2**64, "0", [], {}])
def test_dynamic_coordinate_malformed_rejects(bad):
    with pytest.raises(ValueError):
        require_calendar({"type":"a(sst)","data":[["OnCalendar","daily",bad]]},"daily")
    with pytest.raises(ValueError):
        require_command({"type":"a(sasbttttuii)","data":[[ARGV[0],ARGV.copy(),False,bad,0,0,0,0,0,0]]},ARGV)


@pytest.mark.parametrize("bad", [None, [], {}, {"type":"s","data":[]},
    {"type":"a(sst)","data":[]}, {"type":"a(sst)","data":[None]},
    {"type":"a(sst)","data":[["OnCalendar","daily"]]}])
def test_invalid_native_envelope_rejects(bad):
    with pytest.raises(ValueError):
        require_calendar(bad,"daily")
