"""NS2 negative-flow evidence must fail closed if its independent spy dies."""
import importlib.util
from pathlib import Path

import pytest

SOURCE = (Path(__file__).resolve().parents[1] /
          "acceptance/egress/live-carrier-witness.py")


def witness():
    spec = importlib.util.spec_from_file_location("carrier_witness", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def observer(*, exit_code=None, thread_alive=True, overflow=False, error=None):
    module = witness()

    class Process:
        def poll(self):
            return exit_code

    class Thread:
        def is_alive(self):
            return thread_alive

    spy = module.Observer.__new__(module.Observer)
    spy.process = Process()
    spy.thread = Thread()
    spy.seen = [("allowed.example", 443)]
    spy.capture_overflow = overflow
    spy.reader_failure = error
    return spy


def test_live_observer_can_count_positive_and_negative_sample():
    spy = observer()
    spy.assert_live()
    assert spy.count("allowed.example:443") == 1
    assert spy.count("forbidden.example:443") == 0


@pytest.mark.parametrize("reason", [
    {"exit_code": 1},
    {"thread_alive": False},
    {"overflow": True},
    {"error": "OSError"},
])
def test_negative_sample_fails_closed_on_sensor_loss(reason):
    spy = observer(**reason)
    with pytest.raises(AssertionError, match="Carrier observer"):
        spy.count("forbidden.example:443")


def test_capture_overflow_does_not_silently_discard_negative_evidence(monkeypatch):
    module = witness()
    monkeypatch.setattr(module, "MAX_OBSERVED_CONNECTS", 1)
    spy = module.Observer.__new__(module.Observer)

    class Stream:
        def __iter__(self):
            return iter(("CONNECT allowed.example:443 HTTP/1.1\n",
                         "CONNECT forbidden.example:443 HTTP/1.1\n"))

    class Process:
        stdout = Stream()
        def poll(self):
            return None

    class Thread:
        def is_alive(self):
            return True

    spy.process = Process()
    spy.thread = Thread()
    spy.seen = []
    spy.capture_overflow = False
    spy.reader_failure = None
    spy._reader()
    assert spy.seen == [("allowed.example", 443)]
    assert spy.capture_overflow is True
    with pytest.raises(AssertionError, match="capture overflow"):
        spy.count("forbidden.example:443")
