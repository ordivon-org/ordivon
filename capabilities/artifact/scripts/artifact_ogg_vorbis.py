#!/usr/bin/env python3
"""Standards-first bounded Ogg/Vorbis verifier with explicit browser-boundary evidence."""
from __future__ import annotations
import argparse,array,hashlib,json,os,re,subprocess,sys,tempfile
from pathlib import Path
from typing import Any
import jsonschema

ROOT=Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA=ROOT/'artifact-delivery/shadow-contracts/audio-ogg-vorbis-contract-v1.schema.json'
OGGINFO=Path(os.environ.get('ARTIFACT_OGGINFO','/usr/bin/ogginfo'))
OGGDEC=Path(os.environ.get('ARTIFACT_OGGDEC','/usr/bin/oggdec'))
FFMPEG=Path(os.environ.get('ARTIFACT_FFMPEG','/usr/bin/ffmpeg'))
FFPROBE=Path(os.environ.get('ARTIFACT_FFPROBE','/usr/bin/ffprobe'))
NODE=Path(os.environ.get('ARTIFACT_NODE','/usr/bin/node'))
BROWSER_PROBE=ROOT/'artifact-delivery/node/verify_ogg_vorbis.mjs'
NODE_PACKAGE_ROOT=Path(os.environ.get('ARTIFACT_NODE_PACKAGE_ROOT','/opt/ordivon/external/artifact-toolchain/node/1.63.0'))

def run(a:list[str],*,timeout=120,env=None): return subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout,env=env)
def sha_file(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def sha_bytes(b:bytes): return hashlib.sha256(b).hexdigest()
def canonical(v:Any): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def fact(p:Path): return {'path':str(p.resolve()),'name':p.name,'size':p.stat().st_size,'sha256':sha_file(p)}
def text(p):return p.stdout.decode('utf-8','replace'),p.stderr.decode('utf-8','replace')
def validate_contract(c):
 s=json.loads(CONTRACT_SCHEMA.read_text());return [f"ogg vorbis contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(s).iter_errors(c),key=lambda e:list(e.path))]
def int_or_none(x):
 try:return int(x)
 except:return None

def pcm_compat(reference:bytes,other:bytes)->dict[str,Any]:
 a=array.array('h');b=array.array('h');a.frombytes(reference);b.frombytes(other)
 if sys.byteorder!='little':a.byteswap();b.byteswap()
 n=min(len(a),len(b));diffs=[abs(a[i]-b[i]) for i in range(n)]
 return {'commonSamplesTotal':n,'maxAbsLsb':max(diffs) if diffs else None,'nonzeroDifferences':sum(1 for x in diffs if x),'exactOnCommonPrefix':all(x==0 for x in diffs) if diffs else False}

def verify_ogg_vorbis(path:Path,contract_path:Path,evidence_dir:Path|None=None)->dict[str,Any]:
 if not path.is_file():return {'schemaVersion':1,'kind':'artifact-ogg-vorbis-verification','profileId':'audio-ogg-vorbis-r1','status':'FAIL','failures':['input is not a regular file']}
 try:c=json.loads(contract_path.read_text())
 except Exception as e:return {'schemaVersion':1,'kind':'artifact-ogg-vorbis-verification','profileId':'audio-ogg-vorbis-r1','status':'FAIL','artifact':fact(path),'failures':[f'contract unreadable: {e}']}
 ev=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-ogg-vorbis-evidence-'));ev.mkdir(parents=True,exist_ok=True)
 failures=validate_contract(c);observations=[];want=c.get('audio',{})
 result={'schemaVersion':1,'kind':'artifact-ogg-vorbis-verification','profileId':'audio-ogg-vorbis-r1','status':'FAIL','artifact':fact(path),'contract':{'path':str(contract_path.resolve()),'sha256':sha_file(contract_path),'canonicalDigest':canonical(c)},'tools':{},'failures':failures,'observations':observations}
 tools=[('ogginfo',OGGINFO),('oggdec',OGGDEC),('ffmpeg',FFMPEG),('ffprobe',FFPROBE),('node',NODE),('browserProbe',BROWSER_PROBE)]
 for name,p in tools:
  if not p.is_file() or (name!='browserProbe' and not os.access(p,os.X_OK)):failures.append(f'required mature external capability unavailable: {name}')
  else:result['tools'][name]={'path':str(p.resolve()),'sha256':sha_file(p)}
 if not (NODE_PACKAGE_ROOT/'package.json').is_file():failures.append('pinned Artifact Node/Playwright package root unavailable')
 else:result['tools']['nodePackageRoot']={'path':str(NODE_PACKAGE_ROOT.resolve()),'packageJsonSha256':sha_file(NODE_PACKAGE_ROOT/'package.json')}
 if failures:result['failures']=failures;(ev/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result

 # Xiph ogginfo establishes bounded Ogg/Vorbis structural/technical identity.
 oi=run([str(OGGINFO),str(path)]);out,err=text(oi);(ev/'ogginfo.txt').write_text(out+err)
 oi_fail=[];logical=len(re.findall(r'^New logical stream',out,re.M));ended=len(re.findall(r'^Logical stream \d+ ended$',out,re.M))
 version=re.search(r'^Version:\s*(\d+)\s*$',out,re.M);channels=re.search(r'^Channels:\s*(\d+)\s*$',out,re.M);rate=re.search(r'^Rate:\s*(\d+)\s*$',out,re.M)
 oi_facts={'logicalStreams':logical,'endedLogicalStreams':ended,'vorbis':bool(re.search(r'type vorbis',out)),'version':int(version.group(1)) if version else None,'channels':int(channels.group(1)) if channels else None,'sampleRateHz':int(rate.group(1)) if rate else None}
 if oi.returncode!=0:oi_fail.append('Xiph ogginfo rejected the subject')
 if logical!=1 or ended!=1:oi_fail.append('R1 requires exactly one completed Ogg logical stream')
 if not oi_facts['vorbis'] or oi_facts['version']!=0:oi_fail.append('R1 requires Vorbis version 0')
 for k in ('channels','sampleRateHz'):
  if oi_facts[k]!=want.get(k):oi_fail.append(f'ogginfo {k} differs from contract')
 failures.extend(oi_fail)
 result['oggVorbisIntegrity']={'status':'PASS' if not oi_fail else 'FAIL','facts':oi_facts,'evidenceSha256':sha_file(ev/'ogginfo.txt'),'failures':oi_fail}
 if oi_fail:result['failures']=failures;(ev/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result

 # FFprobe independently exposes exact stream duration in codec time-base samples.
 fp=run([str(FFPROBE),'-v','error','-show_format','-show_streams','-of','json',str(path)]);fpout,fperr=text(fp);(ev/'ffprobe.json').write_text(fpout if fpout else fperr)
 probe_fail=[]
 try:obj=json.loads(fpout) if fp.returncode==0 else {}
 except:obj={}
 streams=obj.get('streams') if isinstance(obj,dict) else None;stream=streams[0] if isinstance(streams,list) and len(streams)==1 else {};fmt=obj.get('format') or {} if isinstance(obj,dict) else {}
 probe_facts={'formatName':fmt.get('format_name'),'codecName':stream.get('codec_name'),'sampleRateHz':int_or_none(stream.get('sample_rate')),'channels':int_or_none(stream.get('channels')),'durationSamples':int_or_none(stream.get('duration_ts')),'startPts':int_or_none(stream.get('start_pts'))}
 if fp.returncode!=0 or len(streams or [])!=1:probe_fail.append('FFprobe did not expose exactly one stream')
 if probe_facts['formatName']!='ogg' or probe_facts['codecName']!='vorbis':probe_fail.append('FFprobe does not identify Ogg/Vorbis')
 for k in ('sampleRateHz','channels'):
  if probe_facts[k]!=want.get(k):probe_fail.append(f'FFprobe {k} differs from contract')
 if probe_facts['durationSamples']!=want.get('playbackSamplesPerChannel'):probe_fail.append('FFprobe durationSamples differs from contract playback boundary')
 failures.extend(probe_fail)
 result['independentTechnicalView']={'status':'PASS' if not probe_fail else 'FAIL','facts':probe_facts,'evidenceSha256':sha_file(ev/'ffprobe.json'),'failures':probe_fail}
 if probe_fail:result['failures']=failures;(ev/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result

 # Xiph reference decode defines the profile's canonical playback-boundary observation.
 ref_path=ev/'oggdec-s16le.raw';od=run([str(OGGDEC),'-Q','-R','-b','16','-e','0','-s','1','-o',str(ref_path),str(path)]);odout,oderr=text(od);(ev/'oggdec.stderr.txt').write_text(odout+oderr)
 ref=ref_path.read_bytes() if ref_path.is_file() else b'';ref_fail=[];frame_bytes=2*want['channels'];ref_frames=len(ref)//frame_bytes if frame_bytes else 0
 if od.returncode!=0:ref_fail.append('Xiph oggdec failed to decode subject')
 if len(ref)%frame_bytes:ref_fail.append('Xiph oggdec PCM byte count is not frame-aligned')
 if ref_frames!=want['playbackSamplesPerChannel']:ref_fail.append('Xiph oggdec playback sample count differs from contract')
 ref_sha=sha_bytes(ref)
 if want.get('expectedReferencePcmSha256') and ref_sha!=want['expectedReferencePcmSha256']:ref_fail.append('Xiph reference PCM SHA-256 differs from object contract')
 failures.extend(ref_fail)
 result['referenceDecode']={'status':'PASS' if not ref_fail else 'FAIL','samplesPerChannel':ref_frames,'pcmBytes':len(ref),'pcmSha256':ref_sha,'failures':ref_fail}
 if ref_fail:result['failures']=failures;(ev/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result

 # FFmpeg is an independent decoder observation, not playback-boundary authority.
 ff=run([str(FFMPEG),'-v','error','-i',str(path),'-map','0:a:0','-f','s16le','-acodec','pcm_s16le','-ar',str(want['sampleRateHz']),'-ac',str(want['channels']),'-']);(ev/'ffmpeg.stderr.txt').write_bytes(ff.stderr)
 independent_fail=[];ff_frames=len(ff.stdout)//frame_bytes if frame_bytes else 0;compat=pcm_compat(ref,ff.stdout) if ff.stdout else {'commonSamplesTotal':0,'maxAbsLsb':None,'nonzeroDifferences':0,'exactOnCommonPrefix':False}
 if ff.returncode!=0 or not ff.stdout:independent_fail.append('FFmpeg independent Vorbis decode failed')
 if compat['maxAbsLsb'] is None or compat['maxAbsLsb']>2:independent_fail.append('FFmpeg common canonical PCM prefix differs from Xiph reference by more than 2 LSB')
 failures.extend(independent_fail)
 if ff_frames!=ref_frames:observations.append(f'FFmpeg decoded sample boundary differs from Xiph reference by {ff_frames-ref_frames} samples/channel')
 result['independentDecodeObservation']={'status':'PASS' if not independent_fail else 'FAIL','samplesPerChannel':ff_frames,'sampleDeltaFromReference':ff_frames-ref_frames,'pcmSha256':sha_bytes(ff.stdout),'commonPrefixCompatibility':compat,'failures':independent_fail,'boundary':'Decode compatibility observation only; FFmpeg sample count is not Vorbis granule authority.'}
 if independent_fail:result['failures']=failures;(ev/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result

 # Pinned Chromium + Firefox Web Audio target evidence. Divergent sample boundaries are surfaced, not laundered.
 env=dict(os.environ);env['ARTIFACT_NODE_PACKAGE_ROOT']=str(NODE_PACKAGE_ROOT)
 bp=run([str(NODE),str(BROWSER_PROBE),str(path),str(want['sampleRateHz'])],timeout=120,env=env);bpout,bperr=text(bp);(ev/'browser-matrix.json').write_text(bpout if bpout else bperr)
 browser_fail=[]
 try:bobj=json.loads(bpout) if bp.returncode==0 else {}
 except:bobj={}
 browsers=bobj.get('browsers') or {};facts={}
 for key in ('chromium','firefox'):
  v=browsers.get(key) or {};facts[key]={k:v.get(k) for k in ('name','status','version','executable','sampleRate','samplesPerChannel','channels','durationSeconds')}
  if v.get('status')!='PASS':browser_fail.append(f'{key} browser Vorbis decode failed')
  if v.get('sampleRate')!=want['sampleRateHz']:browser_fail.append(f'{key} browser sampleRate differs from contract')
  if v.get('channels')!=want['channels']:browser_fail.append(f'{key} browser channels differ from contract')
 failures.extend(browser_fail)
 boundary_agreement=bool(bobj.get('sampleBoundaryAgreement')) if isinstance(bobj,dict) else False
 for key,v in facts.items():
  if v.get('status')=='PASS' and v.get('samplesPerChannel')!=ref_frames:observations.append(f"{key} browser sample boundary differs from Xiph reference by {v.get('samplesPerChannel')-ref_frames} samples/channel")
 result['browserTargetMatrix']={'status':'PASS' if not browser_fail else 'FAIL','browsers':facts,'sampleBoundaryAgreement':boundary_agreement,'referenceBoundaryAgreement':all((v.get('samplesPerChannel')==ref_frames) for v in facts.values() if v.get('status')=='PASS'),'standing':'SAMPLE_BOUNDARY_AGREES' if boundary_agreement and all((v.get('samplesPerChannel')==ref_frames) for v in facts.values() if v.get('status')=='PASS') else 'TARGET_SAMPLE_BOUNDARY_DIVERGENCE_OBSERVED','evidenceSha256':sha_file(ev/'browser-matrix.json'),'failures':browser_fail}
 result.update({'status':'PASS' if not failures else 'FAIL','failures':failures,'observations':observations,'targetCompatibilityStanding':result['browserTargetMatrix']['standing'],'boundary':'PASS establishes one exact single-stream Ogg/Vorbis subject under RFC/Xiph structural and reference-decode semantics, exact object-contract rate/channel/playback-boundary facts, an independent FFprobe/FFmpeg view, and successful pinned Chromium/Firefox decoding. Browser or FFmpeg sample-boundary disagreement is surfaced as target divergence and is not treated as standard failure or as cross-browser equivalence. PASS does not establish artistic quality, tag truth, rights, chained-stream support, or caller-domain suitability.'})
 (ev/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n');return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--evidence-directory',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();v=verify_ogg_vorbis(a.input,a.contract,a.evidence_directory);s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.write_text(s) if a.output else print(s,end='');return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
