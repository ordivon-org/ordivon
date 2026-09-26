import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/verify_formal_trace.py"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_formal_trace", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_formal_trace_gate_passes_current_runtime_binding():
    module = load_module()
    assert module.main() == 0


def test_function_slice_is_symbol_scoped():
    module = load_module()
    text = """impl X {\n    fn alpha() { let x = 1; }\n\n    fn beta() { let y = 2; }\n}\n"""
    body = module.function_slice(text, "alpha")
    assert "let x = 1" in body
    assert "let y = 2" not in body
