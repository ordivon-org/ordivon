import hashlib
import importlib.util
import json
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_wave',ROOT/'scripts/artifact_wave.py');M=importlib.util.module_from_spec(SPEC);assert SPEC.loader;SPEC.loader.exec_module(M)

def make_wave(path:Path,rate=48000,channels=1,frames=4800):
 raw=bytearray()
 for i in range(frames):
  vals=[int(9000*math.sin(2*math.pi*(440+110*c)*i/rate)) for c in range(channels)]
  raw+=struct.pack('<'+'h'*channels,*vals)
 with wave.open(str(path),'wb') as w:w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes(raw)
 return bytes(raw)
def contract(path:Path,raw:bytes,rate=48000,channels=1,frames=4800):
 x={'contractVersion':1,'id':'wave-smoke-r1','profileId':'audio-wave-pcm16-r1','audio':{'sampleRateHz':rate,'channels':channels,'bitsPerSample':16,'frameCount':frames,'expectedPcmSha256':hashlib.sha256(raw).hexdigest()}};path.write_text(json.dumps(x));return x
class ArtifactWaveTests(unittest.TestCase):
 def require_tools(self):
  for p in (M.SNDFILE_INFO,M.SOX,M.SOXI,M.FFMPEG,M.FFPROBE):
   if not p.is_file():self.skipTest(str(p))
 def test_pcm16_wave_passes_three_views_and_exact_decoder_matrix(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);f=r/'a.wav';raw=make_wave(f);c=r/'c.json';contract(c,raw);v=M.verify_wave(f,c,r/'e')
   self.assertEqual(v['status'],'PASS',v);self.assertTrue(v['decoderMatrix']['exactByteMatch']);self.assertEqual(v['referenceContainerView']['facts']['formatName'],'WAVE_FORMAT_PCM');self.assertEqual(v['independentTechnicalView']['facts']['codecTag'],'0x0001')
 def test_wrong_sample_rate_contract_fails_after_file_remains_valid(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);f=r/'a.wav';raw=make_wave(f);c=r/'c.json';x=contract(c,raw);x['audio']['sampleRateHz']=44100;c.write_text(json.dumps(x));v=M.verify_wave(f,c,r/'e');self.assertEqual(v['status'],'FAIL');self.assertTrue(any('sampleRateHz' in z or 'sampleRate' in z for z in v['failures']))
 def test_wrong_pcm_digest_fails_after_decoder_matrix_passes(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);f=r/'a.wav';raw=make_wave(f);c=r/'c.json';x=contract(c,raw);x['audio']['expectedPcmSha256']='0'*64;c.write_text(json.dumps(x));v=M.verify_wave(f,c,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['decoderMatrix']['status'],'PASS');self.assertIn('canonical decoded PCM SHA-256 differs from object contract',v['failures'])
 def test_non_pcm_wave_fails_profile(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);f=r/'fake.wav';f.write_bytes(b'not wave');c=r/'c.json';contract(c,b'\0'*9600);v=M.verify_wave(f,c,r/'e');self.assertEqual(v['status'],'FAIL')
 def test_local_binding_digests_match(self):
  b=json.loads((ROOT/'artifact-delivery/shadow-bindings/audio-wave-pcm16-local-r1.json').read_text())
  for k,p in [('sndfileInfo','/usr/bin/sndfile-info'),('sox','/usr/bin/sox'),('ffmpeg','/usr/bin/ffmpeg'),('ffprobe','/usr/bin/ffprobe')]:self.assertEqual(hashlib.sha256(Path(p).read_bytes()).hexdigest(),b['bindings'][k]['binarySha256'])
if __name__=='__main__':unittest.main()
