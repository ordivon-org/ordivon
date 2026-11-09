from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

SCENES = (
    (0, 6, "响应可能消失\n工作不能失控", "可靠执行不能靠猜测结果。"),
    (13, 24, "精确源码\n受保护的更改", "修改只针对已经读取的确切状态。"),
    (37, 48, "重新连接\n找回同一个 Job", "不盲目重试，读取已记录的证据。"),
    (67, 74, "理解能力\n更要理解边界", "不是敌对沙箱，也不保证外部操作幂等。"),
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a bounded 35-second 1080x1920 Chinese Runtime excerpt from a real selected English A/V master using FFmpeg.")
    parser.add_argument("master", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if not args.master.is_file():
        raise FileNotFoundError(args.master)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg not installed")
    font = next((p for p in (Path("/mnt/c/Windows/Fonts/NotoSansSC-VF.ttf"), Path("/mnt/c/Windows/Fonts/simhei.ttf"), Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc")) if p.is_file()), None)
    if font is None:
        raise RuntimeError("A real Chinese font is required for burned-in captions")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="runtime-zh-short-") as tmp:
        root = Path(tmp)
        lead = root / "lead.txt"
        lead.write_text("ORDIVON  /  RUNTIME", encoding="utf-8")
        footer = root / "footer.txt"
        footer.write_text("2026-08 历史演示  ·  英文旁白 / 中文字幕", encoding="utf-8")
        filters = []
        for i, (start, end, _, _) in enumerate(SCENES):
            filters.extend((
                f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]",
                f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]",
            ))
        streams = "".join(f"[v{i}][a{i}]" for i in range(len(SCENES)))
        filters.append(f"{streams}concat=n={len(SCENES)}:v=1:a=1[cutv][cuta]")
        filters.append("[cutv]scale=1040:585:flags=lanczos,setsar=1[small]")
        filters.append("color=c=0x0A111C:s=1080x1920:r=30:d=35[background]")
        filters.append("[background][small]overlay=x=20:y=570:shortest=1[stage]")
        filters.append("[stage]drawbox=x=0:y=0:w=1080:h=8:color=0xA4E8BE:t=fill,drawbox=x=28:y=1203:w=1024:h=2:color=0x38544A:t=fill[layout]")

        fontarg = f"fontfile={font.as_posix()}:fontcolor=0xF2F8F5"
        filters.append(f"[layout]drawtext={fontarg}:textfile={lead}:fontsize=34:x=64:y=110:fontcolor=0xA4E8BE[f0]")
        elapsed = 0
        before = "f0"
        for i, (_, _, heading, detail) in enumerate(SCENES):
            duration = SCENES[i][1] - SCENES[i][0]
            head = root / f"heading-{i}.txt"
            head.write_text(heading, encoding="utf-8")
            note = root / f"note-{i}.txt"
            note.write_text(detail, encoding="utf-8")
            end = elapsed + duration
            enabled = f"between(t\\,{elapsed}\\,{end})"
            filters.append(f"[{before}]drawtext={fontarg}:textfile={head}:fontsize=70:line_spacing=22:x=60:y=270:enable='{enabled}'[h{i}]")
            filters.append(f"[h{i}]drawtext={fontarg}:textfile={note}:fontsize=42:x=60:y=1320:enable='{enabled}'[f{i+1}]")
            before = f"f{i+1}"
            elapsed = end
        filters.append(f"[{before}]drawtext={fontarg}:textfile={footer}:fontsize=27:x=60:y=1800:fontcolor=0xAFBEBE[vout]")
        filtergraph = ";".join(filters)
        subprocess.run(
            [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(args.master), "-filter_complex", filtergraph,
             "-map", "[vout]", "-map", "[cuta]",
             "-c:v", "libx264", "-preset", "fast", "-crf", "21", "-pix_fmt", "yuv420p",
             "-r", "30", "-c:a", "aac", "-ar", "48000", "-b:a", "128k",
             "-t", "35", "-movflags", "+faststart", str(args.output)],
            check=True,
        )
    print(f"CREATED {args.output} {args.output.stat().st_size} bytes")


if __name__ == "__main__":
    main()
