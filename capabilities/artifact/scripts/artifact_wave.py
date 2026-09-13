#!/usr/bin/env python3
"""Standards-first bounded RIFF/WAVE WAVE_FORMAT_PCM 16-bit verifier."""
from __future__ import annotations
import argparse,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
from typing import Any
import jsonschema

ROOT=Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA=ROOT/'artifact-delivery/shadow-contracts/audio-wave-pcm16-contract-v1.schema.json'
SNDFILE_INFO=Path(os.environ.get('ARTIFACT_SNDFILE_INFO','/usr/bin/sndfile-info'))
SOX=Path(os.environ.get('ARTIFACT_SOX','/usr/bin/sox'))
SOXI=Path(os.environ.get('ARTIFACT_SOXI','/usr/bin/soxi'))
FFMPEG=Path(os.environ.get('ARTIFACT_FFMPEG','/usr/bin/ffmpeg'))
FFPROBE=Path(os.environ.get('ARTIFACT_FFPROBE','/usr/bin/ffprobe'))

def run(a:list[str],timeout=120): return subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def sha_file(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()
def sha_bytes(b:bytes): return hashlib.sha256(b).hexdigest()
def canonical(v:Any): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def text(p): return p.stdout.decode('utf-8','replace'),p.stderr.decode('utf-8','replace')
def fact(p:Path): return {'path':str(p.resolve()),'name':p.name,'size':p.stat().st_size,'sha256':sha_file(p)}
def validate_contract(c):
 s=json.loads(CONTRACT_SCHEMA.read_text());return [f"wave contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(s).iter_errors(c),key=lambda e:list(e.path))]
def int_match(pattern:str,s:str):
 m=re.search(pattern,s,re.M);return int(m.group(1)) if m else None

def verify_wave(path:Path,contract_path:Path,evidence_dir:Path|None=None)->dict[str,Any]:
 if not path.is_file(): return {'schemaVersion':1,'kind':'artifact-wave-verification','profileId':'audio-wave-pcm16-r1','status':'FAIL','failures':['input is not a regular file']}
 try:c=json.loads(contract_path.read_text())
 except Exception as e:return {'schemaVersion':1,'kind':'artifact-wave-verification','profileId':'audio-wave-pcm16-r1','status':'FAIL','artifact':fact(path),'failures':[f'contract unreadable: {e}']}
 failures=validate_contract(c);ev=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-wave-evidence-'));ev.mkdir(parents=True,exist_ok=True)
 result={'schemaVersion':1,'kind':'artifact-wave-verification','profileId':'audio-wave-pcm16-r1','status':'FAIL','artifact':fact(path),'contract':{'path':str(contract_path.resolve()),'sha256':sha_file(contract_path),'canonicalDigest':canonical(c)},'tools':{},'failures':failures}
 if failures:(ev/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result
 for n,p in [('sndfileInfo',SNDFILE_INFO),('sox',SOX),('soxi',SOXI),('ffmpeg',FFMPEG),('ffprobe',FFPROBE)]:
  if not p.is_file() or not os.access(p,os.X_OK): failures.append(f'required mature external capability unavailable: {n}')
  else: result['tools'][n]={'path':str(p.resolve()),'sha256':sha_file(p)}
 if failures:result['failures']=failures;(ev/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result
 want=c['audio']
 # libsndfile is the reference container/format view.
 sf=run([str(SNDFILE_INFO),str(path)]);sfout,sferr=text(sf);(ev/'sndfile-info.txt').write_text(sfout+sferr)
 sf_fail=[]
 sf_facts={
  'wave':bool(re.search(r'^WAVE\s*$',sfout,re.M)),
  'formatTag':(re.search(r'Format\s*:\s*(0x[0-9A-Fa-f]+)\s*=>\s*(\S+)',sfout) or [None,None,None])[1] if re.search(r'Format\s*:',sfout) else None,
  'formatName':(re.search(r'Format\s*:\s*(0x[0-9A-Fa-f]+)\s*=>\s*(\S+)',sfout) or [None,None,None])[2] if re.search(r'Format\s*:',sfout) else None,
  'sampleRateHz':int_match(r'^Sample Rate\s*:\s*(\d+)\s*$',sfout),
  'channels':int_match(r'^Channels\s*:\s*(\d+)\s*$',sfout),
  'bitsPerSample':int_match(r'^\s*Bit Width\s*:\s*(\d+)\s*$',sfout),
  'frameCount':int_match(r'^Frames\s*:\s*(\d+)\s*$',sfout),
 }
 if sf.returncode!=0: sf_fail.append('libsndfile rejected the subject')
 if not sf_facts['wave'] or sf_facts['formatTag']!='0x1' or sf_facts['formatName']!='WAVE_FORMAT_PCM': sf_fail.append('libsndfile does not identify RIFF/WAVE WAVE_FORMAT_PCM tag 0x0001')
 for key in ('sampleRateHz','channels','bitsPerSample','frameCount'):
  if sf_facts.get(key)!=want[key]: sf_fail.append(f'libsndfile {key} differs from contract')
 failures.extend(sf_fail)
 # FFprobe is an independent technical interpretation.
 fp=run([str(FFPROBE),'-v','error','-show_format','-show_streams','-of','json',str(path)]);fpout,fperr=text(fp);(ev/'ffprobe.json').write_text(fpout if fpout else fperr)
 probe_fail=[]
 try:obj=json.loads(fpout) if fp.returncode==0 else {}
 except Exception:obj={}
 streams=obj.get('streams') if isinstance(obj,dict) else None;stream=streams[0] if isinstance(streams,list) and len(streams)==1 else {}
 fmt=obj.get('format') or {} if isinstance(obj,dict) else {}
 def as_int(v):
  try:return int(v)
  except:return None
 probe_facts={'formatName':fmt.get('format_name'),'codecName':stream.get('codec_name'),'codecTag':stream.get('codec_tag'),'sampleFormat':stream.get('sample_fmt'),'sampleRateHz':as_int(stream.get('sample_rate')),'channels':as_int(stream.get('channels')),'bitsPerSample':as_int(stream.get('bits_per_sample')),'frameCount':as_int(stream.get('duration_ts')),'initialPadding':as_int(stream.get('initial_padding'))}
 if fp.returncode!=0 or len(streams or [])!=1: probe_fail.append('FFprobe did not expose exactly one stream')
 if probe_facts['formatName']!='wav' or probe_facts['codecName']!='pcm_s16le' or probe_facts['codecTag']!='0x0001' or probe_facts['sampleFormat']!='s16': probe_fail.append('FFprobe does not identify bounded WAVE PCM s16le tag 0x0001')
 for key in ('sampleRateHz','channels','bitsPerSample','frameCount'):
  if probe_facts.get(key)!=want[key]: probe_fail.append(f'FFprobe {key} differs from contract')
 if probe_facts['initialPadding'] not in (None,0): probe_fail.append('R1 requires zero decoder initial padding')
 failures.extend(probe_fail)
 # SoX metadata view is retained separately and then used as decoder B.
 soxi_facts={};soxi_fail=[]
 for key,arg in [('channels','-c'),('sampleRateHz','-r'),('bitsPerSample','-b'),('frameCount','-s')]:
  p=run([str(SOXI),arg,str(path)]);out,err=text(p)
  try:soxi_facts[key]=int(out.strip())
  except:soxi_fail.append(f'SoX failed to read {key}')
  if p.returncode!=0:soxi_fail.append(f'SoX metadata probe failed for {key}')
  if soxi_facts.get(key)!=want[key]:soxi_fail.append(f'SoX {key} differs from contract')
 failures.extend(soxi_fail)
 # Canonical decoded PCM matrix.
 ff=run([str(FFMPEG),'-v','error','-i',str(path),'-map','0:a:0','-f','s16le','-acodec','pcm_s16le','-ar',str(want['sampleRateHz']),'-ac',str(want['channels']),'-'])
 sx=run([str(SOX),'-D',str(path),'-t','raw','-e','signed-integer','-b','16','-L','-r',str(want['sampleRateHz']),'-c',str(want['channels']),'-'])
 (ev/'ffmpeg.stderr.txt').write_bytes(ff.stderr);(ev/'sox.stderr.txt').write_bytes(sx.stderr)
 decoder_fail=[];exact=ff.returncode==0 and sx.returncode==0 and ff.stdout==sx.stdout
 if ff.returncode!=0:decoder_fail.append('FFmpeg canonical PCM decode failed')
 if sx.returncode!=0:decoder_fail.append('SoX canonical PCM decode failed')
 if not exact:decoder_fail.append('FFmpeg and SoX canonical PCM bytes differ')
 expected_bytes=want['frameCount']*want['channels']*2
 if len(ff.stdout)!=expected_bytes:decoder_fail.append('FFmpeg PCM byte count differs from contract-derived size')
 if len(sx.stdout)!=expected_bytes:decoder_fail.append('SoX PCM byte count differs from contract-derived size')
 failures.extend(decoder_fail)
 pcm_sha=sha_bytes(ff.stdout) if ff.returncode==0 else '' ; pcm_fail=[]
 if want.get('expectedPcmSha256') and pcm_sha!=want['expectedPcmSha256']:pcm_fail.append('canonical decoded PCM SHA-256 differs from object contract')
 failures.extend(pcm_fail)
 result.update({
  'referenceContainerView':{'status':'PASS' if not sf_fail else 'FAIL','facts':sf_facts,'evidenceSha256':sha_file(ev/'sndfile-info.txt'),'failures':sf_fail},
  'independentTechnicalView':{'status':'PASS' if not probe_fail else 'FAIL','facts':probe_facts,'evidenceSha256':sha_file(ev/'ffprobe.json'),'failures':probe_fail},
  'soxTechnicalView':{'status':'PASS' if not soxi_fail else 'FAIL','facts':soxi_facts,'failures':soxi_fail},
  'decoderMatrix':{'status':'PASS' if not decoder_fail else 'FAIL','canonicalFormat':'s16le','ffmpegPcmSha256':sha_bytes(ff.stdout),'soxPcmSha256':sha_bytes(sx.stdout),'exactByteMatch':exact,'pcmBytes':len(ff.stdout),'expectedPcmBytes':expected_bytes,'failures':decoder_fail},
  'pcmIdentity':{'status':'PASS' if not pcm_fail else 'FAIL','decodedPcmSha256':pcm_sha,'contractExpectedPcmSha256':want.get('expectedPcmSha256'),'failures':pcm_fail},
  'status':'PASS' if not failures else 'FAIL','failures':failures,
  'boundary':'PASS is bounded to RIFF/WAVE carrying WAVE_FORMAT_PCM tag 0x0001 with 16-bit signed little-endian mono/stereo PCM under one exact object contract. It establishes libsndfile and FFprobe technical agreement plus exact FFmpeg/SoX canonical PCM agreement. It does not establish artistic/factual correctness, loudness/mastering, ancillary metadata truth, BWF metadata conformance, RF64/WAVE64, compressed WAVE codecs, or signal-quality acceptance.'
 })
 (ev/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n');return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--evidence-directory',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();v=verify_wave(a.input,a.contract,a.evidence_directory);s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.write_text(s) if a.output else print(s,end='');return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
