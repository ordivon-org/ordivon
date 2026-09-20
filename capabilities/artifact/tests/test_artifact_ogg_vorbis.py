import hashlib
import importlib.util
import json
import math
import struct
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_ogg_vorbis',ROOT/'scripts/artifact_ogg_vorbis.py');M=importlib.util.module_from_spec(SPEC);assert SPEC.loader;SPEC.loader.exec_module(M)

def make_wav(path:Path,rate=48000,channels=1,frames=9600):
 raw=bytearray()
 for i in range(frames):
  vals=[int(7000*math.sin(2*math.pi*(440+80*c)*i/rate)) for c in range(channels)];raw+=struct.pack('<'+'h'*channels,*vals)
 with wave.open(str(path),'wb') as w:w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes(raw)
def make_ogg(root:Path,frames=9600):
 wav=root/'in.wav';make_wav(wav,frames=frames);ogg=root/'in.ogg';p=subprocess.run(['/usr/bin/oggenc','-Q','-q','4','-o',str(ogg),str(wav)],capture_output=True);assert p.returncode==0,p.stderr.decode();return ogg
def make_contract(root:Path,ogg:Path,frames=9600):
 ref=root/'ref.raw';p=subprocess.run(['/usr/bin/oggdec','-Q','-R','-b','16','-e','0','-s','1','-o',str(ref),str(ogg)],capture_output=True);assert p.returncode==0
 x={'contractVersion':1,'id':'ogg-vorbis-smoke-r1','profileId':'audio-ogg-vorbis-r1','audio':{'sampleRateHz':48000,'channels':1,'playbackSamplesPerChannel':frames,'expectedReferencePcmSha256':hashlib.sha256(ref.read_bytes()).hexdigest()}};c=root/'contract.json';c.write_text(json.dumps(x));return c
class ArtifactOggVorbisTests(unittest.TestCase):
 def require_tools(self):
  for p in (M.OGGINFO,M.OGGDEC,M.FFMPEG,M.FFPROBE,M.NODE,M.BROWSER_PROBE):
   if not p.is_file():self.skipTest(str(p))
  if not (M.NODE_PACKAGE_ROOT/'package.json').is_file():self.skipTest(str(M.NODE_PACKAGE_ROOT))
 def test_short_vorbis_passes_standard_profile_and_surfaces_browser_boundary(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);o=make_ogg(r);c=make_contract(r,o);v=M.verify_ogg_vorbis(o,c,r/'e')
   self.assertEqual(v['status'],'PASS',v);self.assertEqual(v['referenceDecode']['samplesPerChannel'],9600);self.assertEqual(v['browserTargetMatrix']['status'],'PASS');self.assertEqual(v['browserTargetMatrix']['standing'],'TARGET_SAMPLE_BOUNDARY_DIVERGENCE_OBSERVED');self.assertFalse(v['browserTargetMatrix']['sampleBoundaryAgreement']);self.assertEqual(v['browserTargetMatrix']['browsers']['firefox']['samplesPerChannel'],9600);self.assertEqual(v['browserTargetMatrix']['browsers']['chromium']['samplesPerChannel'],9472)
 def test_wrong_playback_boundary_fails_before_target_promotion(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);o=make_ogg(r);c=make_contract(r,o);x=json.loads(c.read_text());x['audio']['playbackSamplesPerChannel']=9599;c.write_text(json.dumps(x));v=M.verify_ogg_vorbis(o,c,r/'e');self.assertEqual(v['status'],'FAIL');self.assertTrue(any('durationSamples' in z or 'playback sample count' in z for z in v['failures']),v)
 def test_corrupt_ogg_fails_closed_at_xiph_integrity(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);o=make_ogg(r);c=make_contract(r,o);b=bytearray(o.read_bytes());b[-20]^=0x55;o.write_bytes(b);v=M.verify_ogg_vorbis(o,c,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['oggVorbisIntegrity']['status'],'FAIL')
if __name__=='__main__':unittest.main()
