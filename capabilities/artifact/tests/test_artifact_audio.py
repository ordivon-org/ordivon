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
SPEC=importlib.util.spec_from_file_location('artifact_audio',ROOT/'scripts/artifact_audio.py')
MODULE=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(MODULE)
BASE=ROOT/'artifact-delivery/shadow-contracts/audio-flac-pcm16-smoke-r1.json'


def make_wav(path: Path, *, sample_rate=48000, seconds=1) -> bytes:
    n=sample_rate*seconds; raw=bytearray()
    for i in range(n): raw += struct.pack('<hh',int(12000*math.sin(2*math.pi*440*i/sample_rate)),int(8000*math.sin(2*math.pi*660*i/sample_rate)))
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sample_rate); w.writeframes(bytes(raw))
    return bytes(raw)


def make_flac(root: Path, *, sample_rate=48000) -> tuple[Path,bytes]:
    wav=root/'in.wav'; raw=make_wav(wav,sample_rate=sample_rate); flac=root/'audio.flac'
    p=subprocess.run([str(MODULE.FLAC),'-f','--silent','-o',str(flac),str(wav)],capture_output=True)
    if p.returncode: raise RuntimeError((p.stdout+p.stderr).decode('utf-8','replace'))
    return flac,raw


class ArtifactAudioTests(unittest.TestCase):
    def require_tools(self):
        for p in (MODULE.FLAC,MODULE.METAFLAC,MODULE.FFMPEG,MODULE.FFPROBE):
            if not p.is_file(): self.skipTest(f'required mature external tool unavailable: {p}')

    def test_local_binding_tool_digests_match_proven_substrate(self):
        b=json.loads((ROOT/'artifact-delivery/shadow-bindings/audio-flac-pcm16-local-r1.json').read_text())
        checks=[
          ('/opt/ordivon/external/flac/1.5.0-1/rootfs/usr/bin/flac',b['bindings']['referenceDecoder']['flacBinarySha256']),
          ('/opt/ordivon/external/flac/1.5.0-1/rootfs/usr/bin/metaflac',b['bindings']['referenceDecoder']['metaflacBinarySha256']),
          ('/usr/bin/ffmpeg',b['bindings']['independentDecoder']['ffmpegSha256']),
          ('/usr/bin/ffprobe',b['bindings']['independentDecoder']['ffprobeSha256']),
        ]
        for path,want in checks:
            p=Path(path)
            if not p.is_file(): self.skipTest(f'proven substrate path unavailable: {path}')
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),want,path)

    def test_native_flac_contract_passes_decoder_matrix(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); flac,raw=make_flac(root)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),json.loads(BASE.read_text())['audio']['expectedPcmSha256'])
            value=MODULE.verify_flac(flac,BASE,root/'evidence')
            self.assertEqual(value['status'],'PASS',value)
            self.assertTrue(value['decoderMatrix']['exactByteMatch'])
            self.assertEqual(value['streamInfo']['streamInfoMd5'],value['pcmIdentity']['decodedPcmMd5'])

    def test_valid_flac_does_not_launder_wrong_sample_rate_contract(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); flac,_=make_flac(root); contract=root/'contract.json'
            c=json.loads(BASE.read_text()); c['audio']['sampleRateHz']=44100; contract.write_text(json.dumps(c))
            value=MODULE.verify_flac(flac,contract,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertEqual(value['referenceIntegrity']['status'],'PASS')
            self.assertTrue(any('sampleRateHz' in x or 'sample rate' in x for x in value['failures']),value)

    def test_corrupt_audio_frame_fails_closed(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); flac,_=make_flac(root)
            data=bytearray(flac.read_bytes()); idx=max(len(data)-1000,100); data[idx] ^= 0x55; flac.write_bytes(data)
            value=MODULE.verify_flac(flac,BASE,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertTrue(value['referenceIntegrity']['status']=='FAIL' or value['decoderMatrix']['status']=='FAIL',value)

    def test_picture_metadata_is_valid_flac_but_outside_r1_profile(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); flac,_=make_flac(root); png=root/'tiny.png'
            # Minimal valid 1x1 PNG.
            png.write_bytes(bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415408d763f8cfc0f01f00050001ff89993d1d0000000049454e44ae426082'))
            p=subprocess.run([str(MODULE.METAFLAC),'--import-picture-from='+str(png),str(flac)],capture_output=True)
            self.assertEqual(p.returncode,0,(p.stdout+p.stderr).decode('utf-8','replace'))
            p=subprocess.run([str(MODULE.FLAC),'-t',str(flac)],capture_output=True); self.assertEqual(p.returncode,0)
            value=MODULE.verify_flac(flac,BASE,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertEqual(value['referenceIntegrity']['status'],'PASS')
            self.assertEqual(value['metadataBlockPolicy']['status'],'FAIL')

    def test_wrong_expected_pcm_digest_fails_after_both_decoders_agree(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); flac,_=make_flac(root); contract=root/'contract.json'
            c=json.loads(BASE.read_text()); c['audio']['expectedPcmSha256']='0'*64; contract.write_text(json.dumps(c))
            value=MODULE.verify_flac(flac,contract,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertEqual(value['decoderMatrix']['status'],'PASS')
            self.assertIn('canonical decoded PCM SHA-256 differs from object contract',value['failures'])

    def test_contract_schema_rejects_non_r1_bit_depth_before_decoders(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); flac,_=make_flac(root); contract=root/'contract.json'
            c=json.loads(BASE.read_text()); c['audio']['bitsPerSample']=24; contract.write_text(json.dumps(c))
            value=MODULE.verify_flac(flac,contract,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertTrue(any('audio contract schema invalid' in x for x in value['failures']))
            self.assertNotIn('referenceIntegrity',value)

if __name__=='__main__': unittest.main()
