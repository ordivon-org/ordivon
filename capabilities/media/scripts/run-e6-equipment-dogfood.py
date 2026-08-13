from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "equipment" / "e6"
PROPOSITION = "The response was lost. The operation outcome is unknown. Recover the same operation identity before concluding success or failure."


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def run(name: str, command: Sequence[str], *, timeout: int = 120) -> dict[str, Any]:
    started = time.perf_counter_ns()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
    elapsed = (time.perf_counter_ns() - started) / 1_000_000.0
    if result.returncode != 0:
        raise RuntimeError(f"{name} failed ({result.returncode}): {(result.stderr or result.stdout)[-4000:]}")
    return {
        "name": name,
        "executable": command[0],
        "args": list(command[1:]),
        "argumentCount": len(command) - 1,
        "wallMs": elapsed,
        "stdoutTail": result.stdout[-1000:],
        "stderrTail": result.stderr[-1000:],
    }


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path.relative_to(ROOT)), "digest": digest(path), "bytes": path.stat().st_size}


def write_sources() -> dict[str, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    typ = OUT / "brief.typ"
    typ.write_text(
        "#set page(width: 297mm, height: 210mm, margin: 18mm)\n"
        "#set text(size: 14pt)\n"
        "= Recovery state\n\n"
        "*The response was lost.* The operation outcome is *unknown*.\n\n"
        "#rect(width: 100%, inset: 14pt, radius: 6pt, fill: rgb(\"f1efe9\"))[\n"
        "  Do not infer success or failure.\\\n"
        "  Recover the same operation identity before concluding.\n"
        "]\n\n"
        "This page is compiled by deterministic equipment and retained only as an E6 artifact.\n",
        encoding="utf-8",
    )
    svg = OUT / "recovery.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">'
        '<rect width="1200" height="630" fill="#111318"/>'
        '<text x="70" y="75" fill="#f5f3ee" font-family="sans-serif" font-size="34" font-weight="700">RECOVERY STATE</text>'
        '<rect x="70" y="135" width="390" height="190" rx="22" fill="#f1efe9"/>'
        '<text x="105" y="205" fill="#25262a" font-family="sans-serif" font-size="22">RESPONSE LOST</text>'
        '<text x="105" y="250" fill="#25262a" font-family="sans-serif" font-size="18">No terminal result is visible.</text>'
        '<line x1="460" y1="230" x2="650" y2="230" stroke="#6f63ff" stroke-width="10"/>'
        '<polygon points="632,215 650,230 632,245" fill="#6f63ff"/>'
        '<rect x="650" y="135" width="470" height="190" rx="22" fill="#e8e4d8"/>'
        '<text x="685" y="205" fill="#25262a" font-family="sans-serif" font-size="22" font-weight="700">OUTCOME UNKNOWN</text>'
        '<text x="685" y="250" fill="#25262a" font-family="sans-serif" font-size="18">Recover the same operation identity.</text>'
        '<text x="70" y="435" fill="#f5f3ee" font-family="sans-serif" font-size="24">UNKNOWN IS A STATE, NOT A FAILURE</text>'
        '<text x="70" y="485" fill="#b8bbc4" font-family="sans-serif" font-size="18">Same proposition across document, still, spatial, interactive and motion equipment.</text>'
        '</svg>',
        encoding="utf-8",
    )
    blender = OUT / "scene.py"
    blender.write_text(
        "import bpy, math, sys\n"
        "from mathutils import Vector\n"
        "from pathlib import Path\n"
        "out=Path(sys.argv[sys.argv.index('--')+1])\n"
        "bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)\n"
        "def mat(name,color):\n"
        " m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); return m\n"
        "dark=mat('dark',(0.04,0.05,0.07)); pale=mat('unknown',(0.75,0.73,0.66)); accent=mat('accent',(0.20,0.14,0.80))\n"
        "for x,z,scale,material,name in [(-1.7,0.7,(2.6,1.2,1.4),dark,'response-lost'),(1.7,0.7,(3.0,1.2,1.4),pale,'outcome-unknown')]:\n"
        " bpy.ops.mesh.primitive_cube_add(location=(x,0,z), scale=(scale[0]/2,scale[1]/2,scale[2]/2)); o=bpy.context.object; o.name=name; o.data.materials.append(material)\n"
        "bpy.ops.mesh.primitive_cube_add(location=(0,0,0.7), scale=(0.45,0.18,0.18)); bpy.context.object.data.materials.append(accent); bpy.context.object.name='recover-identity-link'\n"
        "bpy.ops.object.camera_add(location=(7,-10,7)); cam=bpy.context.object; bpy.context.scene.camera=cam\n"
        "direction=Vector((0,0,0.6))-cam.location; cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler(); cam.data.lens=52\n"
        "bpy.ops.object.light_add(type='AREA', location=(0,-2,8)); bpy.context.object.data.energy=1300; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=7\n"
        "bpy.ops.object.light_add(type='AREA', location=(4,-1,2)); bpy.context.object.data.energy=700; bpy.context.object.data.size=4\n"
        "scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE_NEXT'; scene.render.resolution_x=640; scene.render.resolution_y=360; scene.render.resolution_percentage=100\n"
        "scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(out/'spatial.png'); scene.render.film_transparent=False\n"
        "scene.world.color=(0.015,0.018,0.025)\n"
        "bpy.ops.wm.save_as_mainfile(filepath=str(out/'recovery-scene.blend'))\n"
        "try: bpy.ops.export_scene.gltf(filepath=str(out/'recovery-scene.glb'), export_format='GLB')\n"
        "except Exception as e: print('GLTF_EXPORT_WARNING', repr(e))\n"
        "bpy.ops.render.render(write_still=True)\n",
        encoding="utf-8",
    )
    godot = OUT / "trace.gd"
    godot.write_text(
        "extends SceneTree\n"
        "func _init():\n"
        "    var args = OS.get_cmdline_user_args()\n"
        "    if args.size() < 1:\n"
        "        push_error('output path required'); quit(2); return\n"
        "    var states = [\n"
        "        {'event':'response-lost','state':'unknown'},\n"
        "        {'event':'recover-same-identity','state':'checking'},\n"
        "        {'event':'no-terminal-evidence','state':'unknown'}\n"
        "    ]\n"
        "    var payload = {'operationId':'op-recovery-42','proposition':'The response was lost. The operation outcome is unknown. Recover the same operation identity before concluding success or failure.','states':states}\n"
        "    var file = FileAccess.open(args[0], FileAccess.WRITE)\n"
        "    if file == null:\n"
        "        push_error('cannot open output'); quit(3); return\n"
        "    file.store_string(JSON.stringify(payload, '  ')); file.close(); print('ORDIVON_E6_TRACE_WRITTEN'); quit()\n",
        encoding="utf-8",
    )
    return {"typst": typ, "svg": svg, "blender": blender, "godot": godot}


def main() -> None:
    sources = write_sources()
    commands: list[dict[str, Any]] = []
    pdf = OUT / "brief.pdf"
    commands.append(run("typst-compile", ["/usr/bin/typst", "compile", str(sources["typst"]), str(pdf)]))

    vector = OUT / "vector.png"
    if Path("/usr/bin/inkscape").is_file():
        vector_equipment = "inkscape"
        commands.append(run("inkscape-export", ["/usr/bin/inkscape", str(sources["svg"]), "--export-filename", str(vector), "--export-width", "1200"]))
    else:
        vector_equipment = "rsvg-convert"
        commands.append(run("rsvg-export", ["/usr/bin/rsvg-convert", "--width", "1200", "--height", "630", "-o", str(vector), str(sources["svg"])]))

    preview = OUT / "preview.png"
    commands.append(run("imagemagick-preview", ["/usr/bin/magick", str(vector), "-resize", "600x315!", str(preview)]))

    spatial = OUT / "spatial.png"
    blend = OUT / "recovery-scene.blend"
    glb = OUT / "recovery-scene.glb"
    if Path("/usr/bin/blender").is_file():
        spatial_equipment = "blender"
        commands.append(run("blender-scene", ["/usr/bin/blender", "--background", "--factory-startup", "--python", str(sources["blender"]), "--", str(OUT)], timeout=180))
    else:
        spatial_equipment = None
        commands.append(run("spatial-fallback-copy", ["/usr/bin/magick", str(vector), str(spatial)]))

    trace = OUT / "interaction.json"
    commands.append(run("godot-trace", ["/usr/bin/godot", "--headless", "--script", str(sources["godot"]), "--", str(trace)]))

    motion = OUT / "equipment-sequence.mp4"
    commands.append(run(
        "ffmpeg-compose",
        [
            "/usr/bin/ffmpeg", "-v", "error", "-y",
            "-loop", "1", "-framerate", "30", "-t", "1", "-i", str(preview),
            "-loop", "1", "-framerate", "30", "-t", "1", "-i", str(spatial),
            "-filter_complex", "[0:v]scale=640:360,setsar=1[v0];[1:v]scale=640:360,setsar=1[v1];[v0][v1]concat=n=2:v=1:a=0[outv]",
            "-map", "[outv]", "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", "2", str(motion),
        ],
        timeout=120,
    ))

    artifacts = {name: artifact(path) for name, path in {
        "documentPdf": pdf,
        "vectorPng": vector,
        "previewPng": preview,
        "spatialPng": spatial,
        "editableBlend": blend,
        "gltfScene": glb,
        "interactiveTrace": trace,
        "motionSequence": motion,
    }.items() if path.is_file()}
    report = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-e6-cross-equipment-dogfood",
        "observedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "sourceProposition": PROPOSITION,
        "equipment": [value for value in ["typst", vector_equipment, "imagemagick", spatial_equipment, "godot", "ffmpeg"] if value],
        "commands": commands,
        "artifacts": artifacts,
        "spatialEquipment": {"equipment": spatial_equipment, "status": "executed" if spatial_equipment else "withheld-after-provisioning-friction", "fallbackUsedForMotionAssembly": spatial_equipment is None},
        "crossEquipmentClaim": "One bounded proposition was compiled into document, vector/raster, interactive-trace and motion outputs by separate equipment while Studio retained source meaning and exact executable boundaries. Editable 3D is claimed only when Blender actually executed.",
        "boundary": "This is production-equipment dogfood. It proves executable integration, artifacts, editability classes and friction measurements; it does not prove human aesthetic preference or that every tool should remain installed.",
    }
    evidence = OUT / "evidence.json"
    evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "evidence": str(evidence.relative_to(ROOT)), "artifacts": artifacts, "commands": [{"name": c["name"], "wallMs": c["wallMs"]} for c in commands]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
