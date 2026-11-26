
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_eda", ROOT / "scripts/artifact_eda.py")
M = importlib.util.module_from_spec(SPEC); assert SPEC and SPEC.loader; SPEC.loader.exec_module(M)


KICAD_PYTHON = Path("/usr/bin/python")
BOARD_GENERATOR = ROOT / "tests/fixtures/eda_kicad_board.py"


def make_board(path: Path, *, bad: bool) -> None:
    args = [str(KICAD_PYTHON), "-I", str(BOARD_GENERATOR), str(path)]
    if bad:
        args.append("--bad")
    proc = subprocess.run(args, capture_output=True, text=True, timeout=30, check=False)
    if proc.returncode != 0 or not path.is_file():
        raise RuntimeError(f"KiCad fixture generation failed: {proc.returncode}: {proc.stderr}")


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
        if not KICAD_PYTHON.is_file():
            self.skipTest("KiCad package-owned Python unavailable")
        probe = subprocess.run(
            [str(KICAD_PYTHON), "-I", "-c", "import pcbnew; print(pcbnew.GetBuildVersion())"],
            capture_output=True, text=True, timeout=15, check=False,
        )
        if probe.returncode != 0:
            self.skipTest("KiCad package-owned pcbnew binding unavailable")
        self.assertEqual(probe.stdout.strip(), subprocess.check_output(
            ["/usr/bin/kicad-cli", "version"], text=True, timeout=15).strip())

    @pytest.mark.integration
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

    @pytest.mark.integration
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
