from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import wave
from pathlib import Path

from ordivon_studio.assets import hash_file, probe_media


def _windows_path(path: Path) -> str:
    result = subprocess.run(["/usr/bin/wslpath", "-w", str(path.resolve())], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def build_narration(
    timed_text_path: Path,
    output_path: Path,
    *,
    voice: str,
    rate: int,
    powershell: Path,
    ffmpeg: Path,
) -> dict[str, object]:
    document = json.loads(timed_text_path.read_text(encoding="utf-8"))
    cues = document.get("cues")
    if not isinstance(cues, list) or not cues:
        raise ValueError("TimedText contains no cues")
    ticks_per_second = int(document["timeBase"]["ticksPerSecond"])
    total_ticks = max(int(cue["endTick"]) for cue in cues)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    script = Path(__file__).with_name("synthesize-sapi-cues.ps1")
    with tempfile.TemporaryDirectory(prefix="ordivon-sapi-", dir=output_path.parent) as directory:
        cue_dir = Path(directory)
        subprocess.run(
            [
                str(powershell),
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                _windows_path(script),
                "-InputJson",
                _windows_path(timed_text_path),
                "-OutputDir",
                _windows_path(cue_dir),
                "-Voice",
                voice,
                "-Rate",
                str(rate),
            ],
            check=True,
        )

        input_args: list[str] = []
        filters: list[str] = []
        cue_records: list[dict[str, object]] = []
        for index, cue in enumerate(cues):
            cue_id = str(cue["id"])
            cue_path = cue_dir / f"{cue_id}.wav"
            duration = _duration_seconds(cue_path)
            start_tick = int(cue["startTick"])
            end_tick = int(cue["endTick"])
            slot = (end_tick - start_tick) / ticks_per_second
            if duration > slot:
                raise RuntimeError(f"cue {cue_id} duration {duration:.6f}s exceeds {slot:.6f}s slot")
            input_args.extend(["-i", str(cue_path)])
            start_ms = round(start_tick * 1000 / ticks_per_second)
            filters.append(f"[{index}:a]aresample=48000,adelay={start_ms}:all=1[a{index}]")
            cue_records.append(
                {
                    "id": cue_id,
                    "startTick": start_tick,
                    "endTick": end_tick,
                    "slotSeconds": slot,
                    "voiceSeconds": round(duration, 6),
                    "sourceBlob": hash_file(cue_path).as_dict(),
                }
            )

        mixed = "".join(f"[a{index}]" for index in range(len(cues)))
        total_seconds = total_ticks / ticks_per_second
        filter_complex = ";".join(filters + [f"{mixed}amix=inputs={len(cues)}:duration=longest:normalize=0,apad=whole_dur={total_seconds},atrim=duration={total_seconds}[out]"])
        temporary_output = output_path.with_suffix(output_path.suffix + ".tmp.wav")
        subprocess.run(
            [
                str(ffmpeg),
                "-v",
                "error",
                "-y",
                *input_args,
                "-filter_complex",
                filter_complex,
                "-map",
                "[out]",
                "-ac",
                "1",
                "-ar",
                "48000",
                "-c:a",
                "pcm_s24le",
                str(temporary_output),
            ],
            check=True,
        )
        temporary_output.replace(output_path)

    return {
        "schemaVersion": 1,
        "kind": "ordivon-studio-sapi-narration-build",
        "timedText": str(timed_text_path),
        "timedTextBlob": hash_file(timed_text_path).as_dict(),
        "generator": {
            "provider": "Windows System.Speech",
            "voice": voice,
            "rate": rate,
            "powershell": str(powershell),
        },
        "cues": cue_records,
        "output": hash_file(output_path).as_dict(),
        "probe": probe_media(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timed-text", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt")
    parser.add_argument("--voice", default="Microsoft Zira Desktop")
    parser.add_argument("--rate", type=int, default=1)
    parser.add_argument("--powershell", default="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
    parser.add_argument("--ffmpeg", default="/usr/bin/ffmpeg")
    args = parser.parse_args()

    receipt = build_narration(
        Path(args.timed_text),
        Path(args.output),
        voice=args.voice,
        rate=args.rate,
        powershell=Path(args.powershell),
        ffmpeg=Path(args.ffmpeg),
    )
    rendered = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
    if args.receipt:
        Path(args.receipt).write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
