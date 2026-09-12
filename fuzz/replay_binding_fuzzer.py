from __future__ import annotations

import sys

import atheris

with atheris.instrument_imports():
    from ordivon_security_v2.admission import ReplayBinding


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    request_id = fdp.ConsumeUnicodeNoSurrogates(64)
    request = {
        "requestId": request_id,
        "actorId": fdp.ConsumeUnicodeNoSurrogates(64),
        "capability": fdp.ConsumeUnicodeNoSurrogates(64),
        "nonce": fdp.ConsumeUInt(32),
        "enabled": fdp.ConsumeBool(),
    }
    admission = {
        "admitted": fdp.ConsumeBool(),
        "reason": fdp.ConsumeUnicodeNoSurrogates(64),
    }

    binding = ReplayBinding()
    if not request_id:
        try:
            binding.bind(request=request, admission=admission)
        except ValueError:
            return
        raise AssertionError("empty requestId must fail closed")

    first, replayed = binding.bind(request=request, admission=admission)
    if replayed or first != admission:
        raise AssertionError("first bind must return the supplied admission without replay")

    second, replayed = binding.bind(request=dict(request), admission={"ignored": True})
    if not replayed or second != admission:
        raise AssertionError("exact replay must return the original admission")

    changed = dict(request)
    changed["nonce"] = (int(changed["nonce"]) + 1) % (2**32)
    try:
        binding.bind(request=changed, admission=admission)
    except ValueError:
        return
    raise AssertionError("same requestId with changed content must fail closed")


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
