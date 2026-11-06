"""Counterexamples: no historical Windows traffic may be inferred from a profile."""
import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "consumers/codex/windows_process_egress.py"


def module():
    spec = importlib.util.spec_from_file_location("win_codex_process_witness", SOURCE)
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def test_proxy_requires_both_http_and_https_with_same_scoped_endpoint():
    witness = module()
    assert witness.proxy_env_state({}) == "UNSET"
    assert witness.proxy_env_state({"HTTPS_PROXY": "http://127.0.0.1:19982"}) == "PARTIAL"
    assert witness.proxy_env_state({
        "HTTP_PROXY": "http://127.0.0.1:19980",
        "HTTPS_PROXY": "http://127.0.0.1:19982",
    }) == "MISMATCH"
    assert witness.proxy_env_state({
        "HTTP_PROXY": "http://127.0.0.1:19982",
        "HTTPS_PROXY": "http://127.0.0.1:19982",
    }) == "SCOPED"


def test_unrelated_tls_socket_does_not_certify_a_proxy_route():
    witness = module()
    assert witness.socket_observation("UNSET", 0, 1) == "NONLOCAL_TLS_SOCKET_OBSERVED"
    assert witness.socket_observation("SCOPED", 0, 1) == "NONLOCAL_TLS_SOCKET_OBSERVED"
    assert witness.socket_observation("SCOPED", 1, 0) == "SCOPED_PROXY_SOCKET_OBSERVED"
