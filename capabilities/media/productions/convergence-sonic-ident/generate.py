#!/usr/bin/env python3
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

RATE = 48_000
DURATION = 4.8
OUT = Path(__file__).resolve().parent / "render" / "convergence-source.wav"


def clamp(x: float) -> float:
    return max(-1.0, min(1.0, x))


def smoothstep(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def env(t: float, start: float, end: float, fade: float = 0.12) -> float:
    if t < start or t > end:
        return 0.0
    a = smoothstep((t - start) / fade)
    b = smoothstep((end - t) / fade)
    return min(a, b)


def glide(t: float, start: float, settle: float, f0: float, f1: float) -> float:
    if t <= start:
        return f0
    if t >= settle:
        return f1
    p = smoothstep((t - start) / (settle - start))
    return f0 + (f1 - f0) * p


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames = int(RATE * DURATION)
    phases = [0.0, 0.0, 0.0]
    target = [220.0, 330.0, 440.0]
    initial = [183.0, 271.0, 503.0]
    pans = [-0.78, 0.74, 0.05]
    starts = [0.18, 0.58, 0.98]
    settles = [2.65, 2.78, 2.92]

    payload = bytearray()
    for i in range(frames):
        t = i / RATE
        left = right = 0.0

        # Three independent signals arrive from different positions and frequencies,
        # then converge toward one harmonic field and the stereo center.
        for j in range(3):
            e = env(t, starts[j], 4.42, 0.16)
            if e == 0.0:
                continue
            f = glide(t, starts[j], settles[j], initial[j], target[j])
            phases[j] += (2.0 * math.pi * f) / RATE
            convergence = smoothstep((t - starts[j]) / max(0.001, settles[j] - starts[j]))
            pan = pans[j] * (1.0 - convergence)
            amp = 0.21 * e
            tone = math.sin(phases[j])
            tone += 0.18 * math.sin(2.0 * phases[j]) * convergence
            l_gain = math.sqrt((1.0 - pan) * 0.5)
            r_gain = math.sqrt((1.0 + pan) * 0.5)
            left += amp * tone * l_gain
            right += amp * tone * r_gain

        # A restrained low pulse marks evidence accumulation without becoming a beat.
        for pulse_t in (0.22, 0.66, 1.10, 2.98):
            dt = t - pulse_t
            if 0.0 <= dt <= 0.34:
                pe = math.exp(-dt * 11.0)
                p = math.sin(2.0 * math.pi * 82.4 * dt) * 0.12 * pe
                left += p
                right += p

        # Final short high cue: the state is now resolved/actionable.
        dt = t - 3.55
        if 0.0 <= dt <= 0.65:
            ce = math.sin(math.pi * min(1.0, dt / 0.65)) ** 2
            cue = math.sin(2.0 * math.pi * 880.0 * dt) * 0.055 * ce
            left += cue
            right += cue

        # Global tail avoids abrupt truncation.
        tail = 1.0 if t < 4.15 else max(0.0, (DURATION - t) / (DURATION - 4.15))
        left = clamp(left * tail)
        right = clamp(right * tail)
        payload.extend(struct.pack("<hh", int(left * 32767), int(right * 32767)))

    with wave.open(str(OUT), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(payload)

    print(OUT)


if __name__ == "__main__":
    main()
