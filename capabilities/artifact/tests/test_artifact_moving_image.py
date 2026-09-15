import hashlib,importlib.util,json
from pathlib import Path
import subprocess,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_moving_image',ROOT/'scripts/artifact_moving_image.py')
MODULE=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(MODULE)
BASE=ROOT/'artifact-delivery/shadow-contracts/moving-image-matroska-ffv1-smoke-r1.json'


def make_mkv(root:Path, *, level=3, with_audio=False, rate=10)->Path:
    dst=root/'video.mkv'
    cmd=[str(MODULE.FFMPEG),'-v','error','-f','lavfi','-i',f'testsrc2=size=64x64:rate={rate}:duration=1']
    if with_audio: cmd += ['-f','lavfi','-i','sine=frequency=1000:sample_rate=48000:duration=1']
    if level == 3:
        cmd += ['-c:v','ffv1','-level','3','-coder','1','-context','1','-g','1','-slices','4','-slicecrc','1','-pix_fmt','yuv422p']
    else:
        cmd += ['-c:v','ffv1','-level',str(level),'-pix_fmt','yuv422p']
    if with_audio: cmd += ['-c:a','flac']
    else: cmd += ['-an']
    cmd += [str(dst)]
    p=subprocess.run(cmd,capture_output=True)
    if p.returncode: raise RuntimeError((p.stdout+p.stderr).decode('utf-8','replace'))
    return dst


def corrupt_first_packet(path:Path)->None:
    p=subprocess.run([str(MODULE.FFPROBE),'-v','error','-select_streams','v:0','-show_packets','-show_entries','packet=pos,size','-of','csv=p=0',str(path)],capture_output=True,text=True)
    if p.returncode or not p.stdout.strip(): raise RuntimeError(p.stderr)
    pos,size=map(int,p.stdout.splitlines()[0].split(',')[:2]); b=bytearray(path.read_bytes()); off=pos+max(8,size//2); b[off]^=0x5A; path.write_bytes(b)


class ArtifactMovingImageTests(unittest.TestCase):
    def require_tools(self):
        for p in (MODULE.MEDIACONCH,MODULE.FFMPEG,MODULE.FFPROBE):
            if not p.is_file(): self.skipTest(f'required mature external tool unavailable: {p}')

    def test_local_binding_tool_digests_match_proven_substrate(self):
        b=json.loads((ROOT/'artifact-delivery/shadow-bindings/moving-image-matroska-ffv1-local-r1.json').read_text())
        checks=[
          ('/opt/ordivon/external/mediaconch/25.04-1/rootfs/usr/bin/mediaconch',b['bindings']['implementationChecker']['binarySha256']),
          ('/usr/bin/ffmpeg',b['bindings']['technicalAndDecode']['ffmpegSha256']),
          ('/usr/bin/ffprobe',b['bindings']['technicalAndDecode']['ffprobeSha256'])]
        for path,want in checks:
            p=Path(path)
            if not p.is_file(): self.skipTest(f'proven substrate unavailable: {path}')
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),want,path)

    def test_matroska_ffv1_contract_passes(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mkv=make_mkv(root); value=MODULE.verify_moving_image(mkv,BASE,root/'e')
            self.assertEqual(value['status'],'PASS',value)
            self.assertGreater(value['matroskaImplementation']['testsRun'],0)
            self.assertEqual(value['mediaInfoTechnical']['codecVersion'],'3.4')
            self.assertEqual(value['decodedVideoIdentity']['rawVideoSha256'],json.loads(BASE.read_text())['video']['expectedRawVideoSha256'])

    def test_mediainfo_decimal_frame_rate_is_normalized_to_contract_rational(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mkv=make_mkv(root,rate=30); c=json.loads(BASE.read_text())
            c['video']['frameRate']={'numerator':30,'denominator':1}; c['video']['frameCount']=30; c['video'].pop('expectedRawVideoSha256',None)
            cp=root/'c.json'; cp.write_text(json.dumps(c)); value=MODULE.verify_moving_image(mkv,cp,root/'e')
            self.assertEqual(value['status'],'PASS',value)
            self.assertEqual(value['mediaInfoTechnical']['frameRate'],'30.000')

    def test_valid_file_does_not_launder_wrong_dimension_contract(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mkv=make_mkv(root); c=json.loads(BASE.read_text()); c['video']['width']=128; cp=root/'c.json'; cp.write_text(json.dumps(c))
            value=MODULE.verify_moving_image(mkv,cp,root/'e')
            self.assertEqual(value['status'],'FAIL'); self.assertEqual(value['matroskaImplementation']['status'],'PASS')
            self.assertTrue(any('Width' in x or 'dimensions' in x or 'byte count' in x for x in value['failures']),value)

    def test_corrupt_ffv1_packet_fails_even_when_ffmpeg_process_exits_zero(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mkv=make_mkv(root); corrupt_first_packet(mkv)
            c=json.loads(BASE.read_text()); c['video'].pop('expectedRawVideoSha256'); cp=root/'c.json'; cp.write_text(json.dumps(c))
            value=MODULE.verify_moving_image(mkv,cp,root/'e')
            self.assertEqual(value['status'],'FAIL')
            self.assertEqual(value['decodedVideoIdentity']['ffmpegReturnCode'],0)
            self.assertEqual(value['matroskaImplementation']['status'],'FAIL')
            self.assertTrue(value['matroskaImplementation']['nonZeroFailureChecks'] or value['ffv1Implementation']['nonZeroFailureChecks'])

    def test_ffv1_unstable_or_old_major_version_is_outside_r1(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mkv=make_mkv(root,level=1); c=json.loads(BASE.read_text()); c['video'].pop('expectedRawVideoSha256'); cp=root/'c.json'; cp.write_text(json.dumps(c))
            value=MODULE.verify_moving_image(mkv,cp,root/'e')
            self.assertEqual(value['status'],'FAIL')
            self.assertTrue(any('stable FFV1 version 3' in x for x in value['failures']),value)

    def test_audio_track_is_valid_container_but_outside_video_only_profile(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mkv=make_mkv(root,with_audio=True); c=json.loads(BASE.read_text()); c['video'].pop('expectedRawVideoSha256'); cp=root/'c.json'; cp.write_text(json.dumps(c))
            value=MODULE.verify_moving_image(mkv,cp,root/'e')
            self.assertEqual(value['status'],'FAIL')
            self.assertTrue(any('non-video' in x or 'non-video stream classes' in x for x in value['failures']),value)

    def test_wrong_expected_rawvideo_digest_fails_after_implementation_checks_pass(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mkv=make_mkv(root); c=json.loads(BASE.read_text()); c['video']['expectedRawVideoSha256']='0'*64; cp=root/'c.json'; cp.write_text(json.dumps(c))
            value=MODULE.verify_moving_image(mkv,cp,root/'e')
            self.assertEqual(value['status'],'FAIL'); self.assertEqual(value['matroskaImplementation']['status'],'PASS')
            self.assertIn('canonical decoded rawvideo SHA-256 differs from object contract',value['failures'])

    def test_contract_rejects_non_r1_pixel_format_before_external_evidence(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mkv=make_mkv(root); c=json.loads(BASE.read_text()); c['video']['pixelFormat']='yuv420p'; cp=root/'c.json'; cp.write_text(json.dumps(c))
            value=MODULE.verify_moving_image(mkv,cp,root/'e')
            self.assertEqual(value['status'],'FAIL'); self.assertTrue(any('moving-image contract schema invalid' in x for x in value['failures'])); self.assertNotIn('matroskaImplementation',value)

if __name__=='__main__': unittest.main()
