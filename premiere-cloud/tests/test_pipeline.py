import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave
import struct

spec = importlib.util.spec_from_file_location('pipeline', Path(__file__).parents[1] / 'pipeline.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class PipelineTests(unittest.TestCase):
    def test_job_contract_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            job = p.prepare(root, 'teste-1', 'Anime Shake', 'forte', 60, 'vertical')
            self.assertEqual(job['export']['height'], 1920)
            self.assertEqual(job['preset_state'], 'nao_iniciado')
            with self.assertRaises(FileExistsError):
                p.prepare(root, 'teste-1', 'Anime Shake', 'forte', 60, 'vertical')

    def test_traversal_and_injection_rejected(self):
        for identifier in ('../secret', '/tmp/x', 'a/b', 'a\\b', '$(whoami)', 'a;exit', '', 'x'*65):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                p.job_id(identifier)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            link = Path(root) / 'link'
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest('Symlinks indisponíveis neste host')
            with self.assertRaises(ValueError):
                p.job_dir(root, 'link')

    @unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg indisponível')
    def test_audio_peaks_and_silence(self):
        with tempfile.TemporaryDirectory() as root:
            audio = Path(root) / 'test.wav'
            for silent in (False, True):
                with wave.open(str(audio), 'wb') as stream:
                    stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(11025)
                    samples = [16000 if not silent and .5 <= i/11025 < .55 else 0 for i in range(22050)]
                    stream.writeframes(struct.pack('<'+'h'*len(samples), *samples))
                result = p.impacts(audio, 2)
                self.assertEqual(result['state'], 'experimental')
                if silent:
                    self.assertEqual(result['events'], [])
                else:
                    self.assertTrue(any(abs(e['time_seconds']-.5) < .06 for e in result['events']))

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg/ffprobe indisponível')
    def test_real_mp4_validation_and_wrong_fps(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / 'synthetic.mp4'
            subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=144x256:rate=30',
                            '-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','1',
                            '-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(output)], check=True, timeout=30)
            settings = dict(width=144, height=256, fps=30)
            result = p.validate_export(output, settings)
            self.assertFalse(result['premiere_proven'])
            self.assertEqual(len(result['sha256']), 64)
            with self.assertRaises(ValueError):
                p.validate_export(output, dict(settings, fps=60))
            with self.assertRaises(ValueError):
                p.validate_export(output, dict(settings, width=1080))

if __name__ == '__main__':
    unittest.main()
