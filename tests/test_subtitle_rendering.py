"""Shared subtitle rasterization and private draft exports."""
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from subtitle_png import alpha_bounds


def chunk(name, payload):
    return struct.pack('>I', len(payload)) + name + payload + struct.pack('>I', zlib.crc32(name + payload))


class SubtitleRenderingTests(unittest.TestCase):
    def test_sources_exclude_unconfirmed_and_unaligned_records(self):
        source = {'kind': 'quran', 'arabic': 'نص', 'english': 'Source', 'start': 99, 'end': 100}
        quote = {'type': 'quran', 'start': 1, 'end': 3, 'ar': 'نص', 'en': 'Source', 'source': source,
                 'reviewed': True, 'needs_review': False}
        self.assertEqual(server.make_sources([quote])[0]['start'], 1)
        for changes in ({'reviewed': False}, {'reviewed': 'true'}, {'en': '  '}, {'candidate': {'kind': 'quran'}},
                        {'source': {**source, 'partial': True, 'alignment_status': 'needs_selection'}}):
            with self.subTest(changes=changes):
                segment = {**quote, **changes}
                self.assertTrue(server.segment_review_pending(segment))
                self.assertEqual(server.make_sources([segment]), [])

    def test_whitespace_translation_has_the_same_placeholder_in_srt_and_ass(self):
        segment = {'type': 'speech', 'ar': 'اختبار', 'en': ' \n ', 'start': 0, 'end': 1}
        for output in (server.make_srt([segment]), server.make_ass([segment], {})):
            self.assertIn('[Translation unavailable]', output)

    @unittest.skipUnless(server.FFMPEG, 'FFmpeg required for frame timing')
    def test_short_cue_is_visible_only_on_its_60fps_video_frame(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(server, 'DATA', Path(temp)):
            folder = server.DATA / ('a' * 32); folder.mkdir()
            src = folder / 'original.mp4'
            subprocess.run([server.FFMPEG, '-v', 'error', '-y', '-f', 'lavfi', '-i',
                            'color=black:s=320x180:r=60:d=0.4', '-c:v', 'libx264', str(src)], check=True, capture_output=True)
            segment = {'type': 'speech', 'ar': 'اختبار', 'en': 'SHORT CUE', 'start': .111, 'end': .121}
            row = {'id': folder.name, 'filename': src.name, 'duration': .4, 'style': '{"size":42}', 'segments': json.dumps([segment])}
            output = server.render_video(row)
            raw = subprocess.run([server.FFMPEG, '-v', 'error', '-i', str(output), '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                                 capture_output=True, check=True).stdout
            frame = 320 * 180
            self.assertEqual(len(raw), frame * 24)
            self.assertFalse(any(value > 100 for value in raw[frame * 6:frame * 7]))
            self.assertTrue(any(value > 100 for value in raw[frame * 7:frame * 8]))
            self.assertFalse(any(value > 100 for value in raw[frame * 8:frame * 9]))
            # Corrupt local manifests must not strand a previously successful export.
            output.with_name('render-manifest.json').write_text('{interrupted')
            self.assertTrue(server.render_video(row).is_file())
            self.assertEqual(json.loads(output.with_name('render-manifest.json').read_text())['renderer'], server.SUBTITLE_RENDER_VERSION)

    @unittest.skipUnless(server.FFMPEG, 'FFmpeg required for unusual dimensions')
    def test_odd_dimensions_render_on_an_even_h264_canvas(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(server, 'DATA', Path(temp)):
            folder = server.DATA / ('a' * 32); folder.mkdir()
            src = folder / 'original.mkv'
            subprocess.run([server.FFMPEG, '-v', 'error', '-y', '-f', 'lavfi', '-i',
                            'color=black:s=321x181:r=25:d=0.3,format=yuv444p', '-c:v', 'ffv1', str(src)], check=True, capture_output=True)
            segment = {'type': 'speech', 'ar': 'اختبار', 'en': 'Odd dimensions', 'start': 0, 'end': .3}
            row = {'id': folder.name, 'filename': src.name, 'duration': .3, 'style': '{}', 'segments': json.dumps([segment])}
            self.assertEqual(server.media_info(server.render_video(row))[:2], (322, 182))

    @unittest.skipUnless(server.FFMPEG, 'FFmpeg required for rotation and aspect')
    def test_anamorphic_rotated_video_uses_display_dimensions(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(server, 'DATA', Path(temp)):
            folder = server.DATA / ('a' * 32); folder.mkdir()
            raw, src = folder / 'landscape.mp4', folder / 'original.mp4'
            subprocess.run([server.FFMPEG, '-v', 'error', '-y', '-f', 'lavfi', '-i',
                            'testsrc=s=320x180:r=25:d=0.4,setsar=4/3', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(raw)], check=True, capture_output=True)
            rotated = subprocess.run([server.FFMPEG, '-v', 'error', '-y', '-display_rotation:v:0', '90', '-i', str(raw), '-c', 'copy',
                                      str(src)], capture_output=True)
            if rotated.returncode:  # Older FFmpeg versions use the rotate metadata tag.
                subprocess.run([server.FFMPEG, '-v', 'error', '-y', '-i', str(raw), '-c', 'copy',
                                '-metadata:s:v:0', 'rotate=90', str(src)], check=True, capture_output=True)
            self.assertEqual(server.media_info(src)[:2], (180, 428))
            segment = {'type': 'speech', 'ar': 'اختبار', 'en': 'Portrait caption', 'start': 0, 'end': .4}
            row = {'id': folder.name, 'filename': src.name, 'duration': .4, 'style': '{}', 'segments': json.dumps([segment])}
            output = server.render_video(row)
            self.assertEqual(server.media_info(output)[:2], (180, 428))

    def test_png_alpha_decoder_handles_all_filters(self):
        rows = [bytes(12), bytes([255, 128, 64, 255] * 3), bytes(12)]
        for method in range(5):
            with self.subTest(filter=method):
                encoded = bytearray()
                previous = bytes(12)
                for row in rows:
                    encoded.append(method)
                    for x, value in enumerate(row):
                        left, up = row[x - 4] if x >= 4 else 0, previous[x]
                        corner = previous[x - 4] if x >= 4 else 0
                        p = left + up - corner
                        dl, du, dc = abs(p - left), abs(p - up), abs(p - corner)
                        paeth = left if dl <= du and dl <= dc else up if du <= dc else corner
                        encoded.append((value - (0, left, up, (left + up) // 2, paeth)[method]) & 255)
                    previous = row
                png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 3, 3, 8, 6, 0, 0, 0))
                png += chunk(b'IDAT', zlib.compress(encoded)) + chunk(b'IEND', b'')
                self.assertEqual(alpha_bounds(png), (1, 1))

    def test_draft_export_keeps_review_flags_and_partial_transcript(self):
        segment = {'start': 0, 'end': 4, 'type': 'quran', 'ar': 'الجزء المسموع', 'en': '', 'needs_review': True,
                   'source': {'partial': True, 'arabic': 'مرجع كامل غير مسموع', 'title': 'مرجع للمراجعة'}}
        row = {'status': 'ready', 'segments': json.dumps([segment])}
        self.assertTrue(server.exportable(row))
        self.assertFalse(server.publishable(row))
        self.assertGreaterEqual(len(server.export_warnings(row)), 2)
        srt = server.make_srt([segment])
        self.assertIn('الجزء المسموع', srt)
        self.assertIn('[Translation unavailable]', srt)
        self.assertNotIn('مرجع كامل غير مسموع', srt)
        self.assertTrue(segment['needs_review'])
        self.assertFalse(server.exportable({**row, 'status': 'processing'}))

    @unittest.skipUnless(server.FFMPEG, 'FFmpeg required for shared rasterizer')
    def test_large_bilingual_text_fits_and_preview_cache_changes_with_style(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(server, 'DATA', Path(temp)):
            row = {'id': 'a' * 32}
            (server.DATA / row['id']).mkdir()
            segment = {'type': 'quran', 'ar': 'إنا لا نضيع أجر من أحسن عملا',
                       'en': 'Indeed, We will not allow to be lost the reward of any who did well in deeds.',
                       'needs_review': True, 'source': {'title': 'الكهف، الآية 30', 'arabic': 'إنا لا نضيع أجر من أحسن عملا'}}
            style = {'font': 'amiri', 'size': 42}
            image, fitted = server.subtitle_image(row, segment, style, 640, 360)
            data = image.read_bytes()
            self.assertEqual(struct.unpack('>II', data[16:24]), (640, 360))
            top, bottom = alpha_bounds(data)
            self.assertGreaterEqual(top, 360 * .10)
            self.assertLess(bottom, 360)
            self.assertGreater(bottom - top, 100)
            same, same_size = server.subtitle_image(row, segment, style, 640, 360)
            self.assertEqual((image, fitted), (same, same_size))
            image.with_suffix('.json').write_text('{interrupted')
            repaired, _ = server.subtitle_image(row, segment, style, 640, 360)
            self.assertEqual(repaired.read_bytes(), data)
            smaller, _ = server.subtitle_image(row, segment, {**style, 'size': 18}, 640, 360)
            self.assertNotEqual(smaller.read_bytes(), data)
            long = {**segment, 'ar': segment['ar'] * 4, 'en': segment['en'] * 5}
            long_image, size = server.subtitle_image(row, long, style, 640, 360)
            self.assertLess(size, 42)
            self.assertGreaterEqual(alpha_bounds(long_image.read_bytes())[0], 360 * .10)
            blank, _ = server.subtitle_image(row, None, style, 640, 360)
            self.assertIsNone(alpha_bounds(blank.read_bytes()))


if __name__ == '__main__':
    unittest.main()
