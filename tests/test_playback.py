"""Browser playback compatibility, cache isolation and failed encode recovery."""
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

MP4 = 'Input #0, mov,mp4,m4a,3gp,3g2,mj2, from upload:\n'
HEVC = MP4 + 'Video: hevc (Main), yuv420p(tv), 640x360\nAudio: aac (HE-AACv2)\n'
H264 = MP4 + 'Video: h264 (High), yuv420p(tv), 640x360\nAudio: aac (LC)\n'


class PlaybackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / ('a' * 32)
        self.folder.mkdir()
        self.original = self.folder / 'original.mp4'
        self.original.write_bytes(b'original uploaded bytes')
        self.row = {'id': self.folder.name, 'filename': self.original.name}
        for p in (patch.object(server, 'DATA', self.root), patch.object(server, 'FFMPEG', 'ffmpeg'),
                  patch.object(server, 'media_info', return_value=(640, 360, 'aac'))):
            p.start(); self.addCleanup(p.stop)

    def encode(self, args, **kwargs):
        if '-c:v' not in args:
            return subprocess.CompletedProcess(args, 1, '', HEVC)
        Path(args[-1]).write_bytes(b'complete portable preview')
        return subprocess.CompletedProcess(args, 0, '', '')

    def test_h264_aac_lc_mp4_uses_original_without_encoding(self):
        with patch.object(server.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', H264)) as run:
            self.assertEqual(server.playback_video(self.row), self.original)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(list(self.folder.glob('playback-*')), [])

    def test_hevc_preview_preserves_original_and_reuses_complete_cache(self):
        before = hashlib.sha256(self.original.read_bytes()).hexdigest()
        with patch.object(server.subprocess, 'run', side_effect=self.encode) as run:
            output = server.playback_video(self.row)
            self.assertNotEqual(output, self.original)
            self.assertEqual(output.read_bytes(), b'complete portable preview')
            args = run.call_args_list[-1].args[0]
            for required in ('libx264', 'yuv420p', 'aac_low', '+faststart', '0:a:0?'):
                self.assertIn(required, args)
            self.assertEqual(server.playback_video(self.row), output)
            self.assertEqual(run.call_count, 2)
        self.assertEqual(hashlib.sha256(self.original.read_bytes()).hexdigest(), before)
        self.assertEqual(list(self.folder.glob('*.pending.mp4')), [])

    def test_replaced_video_does_not_reuse_previous_preview(self):
        with patch.object(server.subprocess, 'run', side_effect=self.encode):
            old = server.playback_video(self.row)
            self.original.write_bytes(b'a different longer upload')
            self.assertNotEqual(server.playback_video(self.row), old)

    def test_failed_encode_is_not_cached_and_can_retry(self):
        def failed(args, **kwargs):
            if '-c:v' not in args: return self.encode(args, **kwargs)
            Path(args[-1]).write_bytes(b'incomplete')
            return subprocess.CompletedProcess(args, 1, '', 'decoder failure')
        with patch.object(server.subprocess, 'run', side_effect=failed):
            with self.assertRaises(RuntimeError): server.playback_video(self.row)
        self.assertEqual(list(self.folder.glob('playback-*')), [])
        with patch.object(server.subprocess, 'run', side_effect=self.encode):
            self.assertTrue(server.playback_video(self.row).is_file())

    def test_he_aac_or_ten_bit_video_also_gets_portable_preview(self):
        for details in (H264.replace('(LC)', '(HE-AACv2)'), H264.replace('yuv420p(', 'yuv420p10le(')):
            with self.subTest(details=details):
                self.original.write_bytes(details.encode())
                def encode(args, **kwargs):
                    if '-c:v' not in args: return subprocess.CompletedProcess(args, 1, '', details)
                    return self.encode(args, **kwargs)
                with patch.object(server.subprocess, 'run', side_effect=encode):
                    self.assertNotEqual(server.playback_video(self.row), self.original)


if __name__ == '__main__': unittest.main()
