import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_eda", ROOT / "scripts/artifact_eda.py")
M = importlib.util.module_from_spec(SPEC); assert SPEC and SPEC.loader; SPEC.loader.exec_module(M)


def make_board(path: Path, *, bad: bool) -> None:
    import pcbnew
    def mm(x): return pcbnew.FromMM(x)
    def v(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
    board = pcbnew.BOARD()
    for a, b in [((0, 0), (40, 0)), ((40, 0), (40, 30)), ((40, 30), (0, 30)), ((0, 30), (0, 0))]:
        shape = pcbnew.PCB_SHAPE(board); shape.SetShape(pcbnew.SHAPE_T_SEGMENT); shape.SetStart(v(*a)); shape.SetEnd(v(*b)); shape.SetLayer(pcbnew.Edge_Cuts); shape.SetWidth(mm(0.2)); board.Add(shape)
    for ref, x, net_name, code in [("J1", 10.0, "N1", 1), ("J2", 10.7 if bad else 30.0, "N2", 2)]:
        net = pcbnew.NETINFO_ITEM(board, net_name, code); board.Add(net)
        fp = pcbnew.FOOTPRINT(board); fp.SetReference(ref); fp.SetValue("TEST"); fp.SetPosition(v(x, 15)); board.Add(fp)
        pad = pcbnew.PAD(fp); pad.SetNumber("1"); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE); pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH); pad.SetSize(v(2, 2)); pad.SetDrillSize(v(1, 1)); pad.SetPosition(v(x, 15)); pad.SetNet(net); fp.Add(pad)
    pcbnew.SaveBoard(str(path), board)


def write_contract(path: Path) -> None:
    path.write_text(json.dumps({
        "schemaVersion": 1, "kind": "eda-kicad-pcb-contract-v1",
        "board": {"hasOutline": True, "widthMm": 40.0, "heightMm": 30.0, "throughHolePads": 2, "minDrillDiameterMm": 1.0},
        "drc": {"severity": "error", "requireZeroViolations": True},
        "manufacturingOutputs": {"gerberLayers": ["F.Cu", "B.Cu", "Edge.Cuts"], "excellon": True}
    }, indent=2) + "\n")


class ArtifactEdaTests(unittest.TestCase):
    def require_tools(self):
        if not Path("/usr/bin/kicad-cli").is_file(): self.skipTest("kicad-cli unavailable")
        try:
            import pcbnew  # noqa: F401
        except ImportError:
            self.skipTest("KiCad pcbnew Python bindings unavailable")

    def test_positive_board_passes_drc_contract_and_manufacturing_exports(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); board = root / "good.kicad_pcb"; contract = root / "contract.json"; evidence = root / "evidence"
            make_board(board, bad=False); write_contract(contract)
            result = M.verify_kicad_pcb(board, contract, evidence)
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["drc"]["violationCount"], 0)
            self.assertGreaterEqual(len(result["manufacturing"]["gerber"]), 4)
            self.assertTrue(any(Path(x["path"]).suffix.lower() == ".drl" for x in result["manufacturing"]["drill"]))

    def test_overlapping_different_net_pads_fail_closed(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); board = root / "bad.kicad_pcb"; contract = root / "contract.json"; evidence = root / "evidence"
            make_board(board, bad=True); write_contract(contract)
            result = M.verify_kicad_pcb(board, contract, evidence)
            self.assertEqual(result["status"], "FAIL")
            self.assertGreater(result["drc"]["violationCount"], 0)
            self.assertIn("KiCad DRC reported error-level violations", result["failures"])

    def test_profile_and_binding_keep_electrical_nonclaims_explicit(self):
        profile = json.loads((ROOT / "artifact-delivery/shadow-profiles/eda-kicad-pcb-gerber-r1.json").read_text())
        binding = json.loads((ROOT / "artifact-delivery/shadow-bindings/eda-kicad-pcb-local-r1.json").read_text())
        self.assertEqual(profile["classification"]["family"], "electronic-design")
        self.assertIn("electrical function or circuit correctness", profile["nonClaims"])
        self.assertEqual(binding["status"], "LOCAL_LIVE_PROVEN")


if __name__ == "__main__": unittest.main()
