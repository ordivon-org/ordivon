#!/usr/bin/env python3
"""Standards-first shadow verifier for bounded Matroska v4 + stable FFV1 v3 video artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from fractions import Fraction
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any
import xml.etree.ElementTree as ET

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA = ROOT / "artifact-delivery/shadow-contracts/moving-image-ffv1-contract-v1.schema.json"
MEDIACONCH = Path(os.environ.get("ARTIFACT_MEDIACONCH", "/opt/ordivon/external/mediaconch/25.04-1/mediaconch"))
FFMPEG = Path(os.environ.get("ARTIFACT_FFMPEG", "/usr/bin/ffmpeg"))
FFPROBE = Path(os.environ.get("ARTIFACT_FFPROBE", "/usr/bin/ffprobe"))
MC_NS = "{https://mediaarea.net/mediaconch}"


def run(argv: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=timeout)


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def artifact_fact(path: Path) -> dict[str,Any]:
    return {'path':str(path.resolve()),'name':path.name,'size':path.stat().st_size,'sha256':sha256_file(path)}


def validate_contract(contract: dict[str,Any]) -> list[str]:
    schema=json.loads(CONTRACT_SCHEMA.read_text())
    return [f"moving-image contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(schema).iter_errors(contract),key=lambda e:list(e.path))]


def decode_xml(data: bytes) -> ET.Element | None:
    try: return ET.fromstring(data.decode('utf-8','replace'))
    except ET.ParseError: return None


def parse_mediaconch_implementation(root: ET.Element | None) -> tuple[dict[str,Any],dict[str,Any],list[str]]:
    failures=[]
    if root is None:
        return {'status':'FAIL'},{'status':'FAIL'},['MediaConch implementation XML is not parseable']
    groups=[]
    for e in root.iter():
        if e.tag==MC_NS+'implementationChecks':
            checks=[dict(c.attrib) for c in e.findall(MC_NS+'check')]
            groups.append({'attrs':dict(e.attrib),'checks':checks})
    if not groups:
        return {'status':'FAIL'},{'status':'FAIL'},['MediaConch emitted no implementationChecks groups']
    # MediaConch currently emits Matroska/EBML group first and FFV1 group second.
    # Identify semantically by ICID prefixes instead of positional trust.
    mat_groups=[]; ffv1_groups=[]; other=[]
    for g in groups:
        ids=[c.get('icid','') for c in g['checks']]
        if any(i.startswith('EBML-') or i.startswith('MKV-') for i in ids): mat_groups.append(g)
        elif any(i.startswith('FFV1-') for i in ids): ffv1_groups.append(g)
        elif len(groups)>=2 and not ids: other.append(g)
        else: other.append(g)
    # Clean MediaConch 25.04 can emit a placeholder FFV1 group with one blank 0-test check.
    if not ffv1_groups:
        for g in other:
            checks=g['checks']
            if len(checks)==1 and not checks[0].get('icid'):
                ffv1_groups.append(g); break
    def summarize(gs):
        checks=[c for g in gs for c in g['checks']]
        return {
            'groupCount':len(gs),'checkCount':len(checks),
            'testsRun':sum(int(c.get('tests_run','0') or 0) for c in checks),
            'failCount':sum(int(c.get('fail_count','0') or 0) for c in checks),
            'warnCount':sum(int(c.get('warn_count','0') or 0) for c in checks),
            'passCount':sum(int(c.get('pass_count','0') or 0) for c in checks),
            'nonZeroFailureChecks':[c for c in checks if int(c.get('fail_count','0') or 0)>0],
            'nonZeroWarningChecks':[c for c in checks if int(c.get('warn_count','0') or 0)>0],
        }
    mat=summarize(mat_groups); ffv=summarize(ffv1_groups)
    mat_fail=[]; ffv_fail=[]
    if mat['groupCount']<1 or mat['testsRun']<1: mat_fail.append('MediaConch executed no Matroska/EBML implementation tests')
    if mat['failCount'] or mat['warnCount']: mat_fail.append('MediaConch Matroska/EBML implementation report contains failure/warning')
    if ffv['groupCount']<1: ffv_fail.append('MediaConch emitted no FFV1 implementation-check group')
    if ffv['failCount'] or ffv['warnCount']: ffv_fail.append('MediaConch FFV1 implementation report contains failure/warning')
    mat['status']='PASS' if not mat_fail else 'FAIL'; mat['failures']=mat_fail
    ffv['status']='PASS' if not ffv_fail else 'FAIL'; ffv['failures']=ffv_fail
    failures.extend(mat_fail+ffv_fail)
    return mat,ffv,failures


def parse_mediainfo(root: ET.Element | None) -> tuple[dict[str,str],dict[str,str],list[str]]:
    if root is None: return {},{},['MediaInfo XML is not parseable']
    tracks=[]
    for e in root.iter():
        if e.tag.split('}')[-1]=='track':
            vals={c.tag.split('}')[-1]:(c.text or '').strip() for c in list(e)}
            tracks.append((e.attrib.get('type',''),vals))
    general=[v for t,v in tracks if t=='General']; video=[v for t,v in tracks if t=='Video']
    failures=[]
    if len(general)!=1: failures.append('MediaInfo did not expose exactly one General track')
    if len(video)!=1: failures.append('MediaInfo did not expose exactly one Video track')
    return general[0] if general else {}, video[0] if video else {}, failures


def frac(s: str) -> Fraction | None:
    try: return Fraction(s)
    except Exception: return None


def verify_moving_image(path: Path, contract_path: Path, evidence_dir: Path | None=None) -> dict[str,Any]:
    if not path.is_file(): return {'schemaVersion':1,'kind':'artifact-moving-image-verification','profileId':'moving-image-matroska-ffv1-v3-r1','status':'FAIL','failures':['input is not a regular file']}
    try: contract=json.loads(contract_path.read_text())
    except Exception as e: return {'schemaVersion':1,'kind':'artifact-moving-image-verification','profileId':'moving-image-matroska-ffv1-v3-r1','status':'FAIL','artifact':artifact_fact(path),'failures':[f'contract unreadable: {e}']}
    failures=validate_contract(contract)
    evidence_dir=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-moving-image-evidence-')); evidence_dir.mkdir(parents=True,exist_ok=True)
    result={'schemaVersion':1,'kind':'artifact-moving-image-verification','profileId':'moving-image-matroska-ffv1-v3-r1','status':'FAIL','artifact':artifact_fact(path),'contract':{'path':str(contract_path.resolve()),'sha256':sha256_file(contract_path),'canonicalDigest':canonical_digest(contract)},'tools':{},'failures':failures}
    if failures:
        result['boundary']='Invalid moving-image object contracts fail before external evidence can be promoted.'
        (evidence_dir/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); return result
    for name,tool in (('mediaconch',MEDIACONCH),('ffmpeg',FFMPEG),('ffprobe',FFPROBE)):
        if not tool.is_file() or not os.access(tool,os.X_OK): failures.append(f'required mature external capability unavailable: {name}')
        else: result['tools'][name]={'path':str(tool.resolve()),'sha256':sha256_file(tool)}
    if failures:
        result['failures']=failures; (evidence_dir/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); return result

    # MediaConch built-in implementation checks.
    mc=run([str(MEDIACONCH),'-mc','-fx',str(path)])
    (evidence_dir/'mediaconch-implementation.xml').write_bytes(mc.stdout if mc.stdout else mc.stderr)
    mc_root=decode_xml(mc.stdout) if mc.returncode==0 else None
    mat,ffv,mc_fail=parse_mediaconch_implementation(mc_root)
    if mc.returncode!=0: mc_fail.append('MediaConch process failed')
    failures.extend(mc_fail)

    # MediaInfo technical view through MediaConch's frozen libmediainfo carrier.
    mi=run([str(MEDIACONCH),'-mi','-fx',str(path)])
    (evidence_dir/'mediainfo.xml').write_bytes(mi.stdout if mi.stdout else mi.stderr)
    general,video,mi_parse_fail=parse_mediainfo(decode_xml(mi.stdout) if mi.returncode==0 else None)
    mi_fail=list(mi_parse_fail)
    want=contract['video']
    if general.get('Format')!='Matroska': mi_fail.append('MediaInfo container format is not Matroska')
    if general.get('Format_Version')!='4': mi_fail.append('MediaInfo Matroska version is not 4')
    if general.get('VideoCount')!='1': mi_fail.append('MediaInfo does not report exactly one video track')
    if any(int(general.get(k,'0') or 0)>0 for k in ('AudioCount','TextCount','MenuCount','ImageCount')): mi_fail.append('R1 excludes non-video stream classes')
    if video.get('Format')!='FFV1' or video.get('CodecID')!='V_FFV1': mi_fail.append('MediaInfo video codec is not FFV1/V_FFV1')
    ver=video.get('Format_Version',''); m=re.fullmatch(r'3\.(\d+)',ver)
    micro=int(m.group(1)) if m else -1
    if micro<4: mi_fail.append('MediaInfo does not report stable FFV1 version 3 micro-version >=4')
    expected={'Width':str(want['width']),'Height':str(want['height']),'FrameCount':str(want['frameCount']),'BitDepth':str(want['bitDepth']),'ChromaSubsampling':want['chromaSubsampling'],'ScanType':want['scanType']}
    for k,v in expected.items():
        if video.get(k)!=v: mi_fail.append(f'MediaInfo {k} differs from contract')
    if video.get('FrameRate_Mode')!='CFR': mi_fail.append('MediaInfo frame-rate mode is not CFR')
    mi_rate=None
    if video.get('FrameRate_Num') and video.get('FrameRate_Den'):
        try: mi_rate=Fraction(int(video['FrameRate_Num']),int(video['FrameRate_Den']))
        except (TypeError,ValueError,ZeroDivisionError): mi_rate=None
    if mi_rate is None:
        mi_rate=frac(video.get('FrameRate',''))
    want_rate=Fraction(want['frameRate']['numerator'],want['frameRate']['denominator'])
    if mi_rate!=want_rate: mi_fail.append('MediaInfo frame-rate rational differs from contract')
    failures.extend(mi_fail)

    # FFprobe independent technical view/topology.
    probe=run([str(FFPROBE),'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)])
    (evidence_dir/'ffprobe.json').write_bytes(probe.stdout if probe.stdout else probe.stderr)
    probe_fail=[]
    try: pobj=json.loads(probe.stdout.decode()) if probe.returncode==0 else {}
    except Exception: pobj={}
    streams=pobj.get('streams') if isinstance(pobj,dict) else None
    streams=streams if isinstance(streams,list) else []
    video_streams=[s for s in streams if s.get('codec_type')=='video']; other_streams=[s for s in streams if s.get('codec_type')!='video']
    if len(video_streams)!=1: probe_fail.append('FFprobe did not expose exactly one video stream')
    if other_streams: probe_fail.append('FFprobe exposed non-video streams outside R1 topology')
    vs=video_streams[0] if video_streams else {}
    if vs.get('codec_name')!='ffv1': probe_fail.append('FFprobe codec is not FFV1')
    if int(vs.get('width',-1))!=want['width'] or int(vs.get('height',-1))!=want['height']: probe_fail.append('FFprobe dimensions differ from contract')
    if vs.get('pix_fmt')!=want['pixelFormat']: probe_fail.append('FFprobe pixel format differs from contract')
    if int(vs.get('bits_per_raw_sample') or -1)!=want['bitDepth']: probe_fail.append('FFprobe raw bit depth differs from contract')
    if vs.get('field_order')!='progressive': probe_fail.append('FFprobe scan type is not progressive')
    rate=frac(vs.get('r_frame_rate',''))
    want_rate=Fraction(want['frameRate']['numerator'],want['frameRate']['denominator'])
    if rate!=want_rate: probe_fail.append('FFprobe frame rate differs from contract')
    if int(vs.get('nb_read_frames') or -1)!=want['frameCount']: probe_fail.append('FFprobe decoded/read frame count differs from contract')
    fmt=(pobj.get('format') or {}).get('format_name','')
    if 'matroska' not in fmt: probe_fail.append('FFprobe does not identify Matroska container')
    failures.extend(probe_fail)

    # Canonical decoded frame sequence.
    dec=run([str(FFMPEG),'-v','error','-i',str(path),'-map','0:v:0','-f','rawvideo','-pix_fmt','yuv422p','-'])
    (evidence_dir/'ffmpeg-decode.stderr.txt').write_bytes(dec.stderr)
    decode_fail=[]
    # yuv422p 8-bit = 2 bytes/pixel/frame.
    expected_bytes=want['width']*want['height']*2*want['frameCount']
    raw_sha=sha256_bytes(dec.stdout)
    if dec.returncode!=0: decode_fail.append('FFmpeg canonical rawvideo decode failed')
    if len(dec.stdout)!=expected_bytes: decode_fail.append('canonical rawvideo byte count differs from contract-derived size')
    expected_sha=want.get('expectedRawVideoSha256')
    if expected_sha and raw_sha!=expected_sha: decode_fail.append('canonical decoded rawvideo SHA-256 differs from object contract')
    # stderr integrity diagnostics are blocking even when FFmpeg exits zero.
    stderr=dec.stderr.decode('utf-8','replace')
    diagnostic_patterns=['crc mismatch','bytestream end mismatching','invalid data','error while decoding']
    diagnostics=[p for p in diagnostic_patterns if p in stderr.lower()]
    if diagnostics: decode_fail.append('FFmpeg emitted decode-integrity diagnostics despite process exit status')
    failures.extend(decode_fail)

    result.update({
      'matroskaImplementation':{**mat,'processReturnCode':mc.returncode,'evidenceSha256':sha256_file(evidence_dir/'mediaconch-implementation.xml')},
      'ffv1Implementation':ffv,
      'mediaInfoTechnical':{'status':'PASS' if not mi_fail else 'FAIL','containerFormat':general.get('Format'),'containerVersion':general.get('Format_Version'),'codec':video.get('Format'),'codecVersion':ver,'ffv1MicroVersion':micro,'width':video.get('Width'),'height':video.get('Height'),'frameRate':video.get('FrameRate'),'frameCount':video.get('FrameCount'),'chromaSubsampling':video.get('ChromaSubsampling'),'bitDepth':video.get('BitDepth'),'scanType':video.get('ScanType'),'failures':mi_fail,'evidenceSha256':sha256_file(evidence_dir/'mediainfo.xml')},
      'ffprobeTechnical':{'status':'PASS' if not probe_fail else 'FAIL','streamCount':len(streams),'videoStreamCount':len(video_streams),'otherStreamCount':len(other_streams),'codec':vs.get('codec_name'),'width':vs.get('width'),'height':vs.get('height'),'pixelFormat':vs.get('pix_fmt'),'frameRate':vs.get('r_frame_rate'),'frameCount':vs.get('nb_read_frames'),'failures':probe_fail,'evidenceSha256':sha256_file(evidence_dir/'ffprobe.json')},
      'decodedVideoIdentity':{'status':'PASS' if not decode_fail else 'FAIL','ffmpegReturnCode':dec.returncode,'rawVideoSha256':raw_sha,'contractExpectedRawVideoSha256':expected_sha,'rawVideoBytes':len(dec.stdout),'expectedRawVideoBytes':expected_bytes,'integrityDiagnostics':diagnostics,'failures':decode_fail},
      'status':'PASS' if not failures else 'FAIL','failures':failures,
      'boundary':'PASS is bounded to one RFC 9559 Matroska v4 video-only artifact carrying stable RFC 9043 FFV1 version 3 (micro-version >=4), 8-bit progressive yuv422p CFR video under one exact object contract. It establishes MediaConch zero-failure/warning implementation evidence, MediaInfo/FFprobe technical agreement, stream topology, canonical rawvideo byte count and optional decoded-frame SHA-256 identity. It does not claim full FFV1 conformance from MediaConch when its clean-file FFV1 checker executes zero tests, visual/artistic correctness, broad player compatibility, audio/subtitle semantics, or bit-identical Matroska reproducibility.'
    })
    (evidence_dir/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    return result


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('input',type=Path); ap.add_argument('--contract',type=Path,required=True); ap.add_argument('--evidence-directory',type=Path); ap.add_argument('--output',type=Path); a=ap.parse_args()
    value=verify_moving_image(a.input,a.contract,a.evidence_directory); s=json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(s)
    else: print(s,end='')
    return 0 if value.get('status')=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
