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
    def test_brief_gaps_are_shared_display_timing_not_transcript_edits(self):
        segments = [{'id': str(i), 'start': start, 'end': end, 'type': 'speech',
                     'ar': 'اختبار', 'translation': str(i), 'display_end': 999}
                    for i, (start, end) in enumerate(((1, 2), (2.5, 3), (3.500001, 4), (3.9, 5)))]
        original = json.dumps(segments)
        display = server.subtitle_display_segments(segments)
        self.assertEqual([s['display_end'] for s in display], [2.5, 3, 4, 5])
        self.assertEqual(json.dumps(segments), original)
        self.assertEqual(server.subtitle_display_segments(display), display)
        self.assertEqual(server.subtitle_display_segments([]), [])
        srt = server.make_srt(segments)
        ass = server.make_ass(segments, {})
        self.assertIn('00:00:01,000 --> 00:00:02,500', srt)
        self.assertIn('Dialogue: 0,0:00:01.00,0:00:02.50', ass)
        # Source documentation always uses the actual spoken end.
        quote = {**segments[0], 'type': 'quran', 'source': {'arabic': 'اختبار', 'translation': '0'},
                 'reviewed': True, 'needs_review': False}
        self.assertEqual(server.make_sources([quote, *segments[1:]])[0]['end'], 2)

    @unittest.skipUnless(server.FFMPEG, 'FFmpeg required for transition timing')
    def test_export_holds_brief_gap_but_clears_long_silence_and_final_cue(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(server, 'DATA', Path(temp)):
            folder = server.DATA / ('a' * 32); folder.mkdir()
            src = folder / 'original.mp4'
            subprocess.run([server.FFMPEG, '-v', 'error', '-y', '-f', 'lavfi', '-i',
                            'color=black:s=320x180:r=30:d=3', '-c:v', 'libx264', str(src)], check=True, capture_output=True)
            segments = [{'type': 'speech', 'ar': 'اختبار', 'translation': text, 'start': start, 'end': end}
                        for text, start, end in [('FIRST', .2, .7), ('SECOND', 1, 1.3), ('LAST', 2, 2.5)]]
            row = {'id': folder.name, 'filename': src.name, 'duration': 3, 'style': '{"size":42}', 'segments': json.dumps(segments)}
            output = server.render_video(row)
            raw = subprocess.run([server.FFMPEG, '-v', 'error', '-i', str(output), '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True).stdout
            frame_size = 320 * 180
            for frame, visible in [(3, False), (24, True), (31, True), (48, False), (66, True), (81, False)]:
                with self.subTest(frame=frame):
                    self.assertEqual(any(v > 100 for v in raw[frame_size * frame:frame_size * (frame + 1)]), visible)
            manifest = json.loads(output.with_name('render-manifest-en.json').read_text())
            self.assertEqual([(c['start'], c['end']) for c in manifest['cues']],
                             [(0, .2), (.2, 1), (1, 1.3), (1.3, 2), (2, 2.5), (2.5, 3)])

    @unittest.skipUnless(server.FFMPEG, 'FFmpeg required for diacritic backdrops')
    def test_vowelled_arabic_has_one_solid_backdrop_and_background_can_be_disabled(self):
        segment = {'type': 'quran', 'start': 0, 'end': 1,
                   'ar': 'إِنَّا لَا نُضِيعُ أَجْرَ مَنْ أَحْسَنَ عَمَلًا',
                   'translation': 'Indeed, We will not allow to be lost the reward of any who did well in deeds.',
                   'source': {'surah': 18, 'ayah': 30, 'translator': 'Saheeh International'}}
        with tempfile.TemporaryDirectory() as temp, patch.object(server, 'DATA', Path(temp)):
            row = {'id': 'a' * 32}; (server.DATA / row['id']).mkdir()
            for font in ('amiri', 'plex', 'noto-naskh'):
                for size in (18, 42):
                    with self.subTest(font=font, size=size):
                        image, _ = server.subtitle_image(row, segment, {'font': font, 'size': size}, 640, 360)
                        raw = subprocess.run([server.FFMPEG, '-v', 'error', '-i', str(image), '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], capture_output=True, check=True).stdout
                        alpha = raw[3::4]
                        points = [i for i, value in enumerate(alpha) if value >= 128]
                        left, right = min(i % 640 for i in points), max(i % 640 for i in points)
                        top, bottom = min(points) // 640, max(points) // 640
                        self.assertGreater(right - left, 100)
                        # A combining mark must not create a detached box or a
                        # step in the translucent background's silhouette.
                        for y in range(top + 2, bottom - 1):
                            self.assertGreaterEqual(min(alpha[y * 640 + left + 2:y * 640 + right - 1]), 128)
            plain, _ = server.subtitle_image(row, segment, {'font': 'amiri', 'size': 42, 'backdrop': False}, 640, 360)
            raw = subprocess.run([server.FFMPEG, '-v', 'error', '-i', str(plain), '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], capture_output=True, check=True).stdout
            alpha = raw[3::4]
            points = [i for i, value in enumerate(alpha) if value >= 128]
            left, right = min(i % 640 for i in points), max(i % 640 for i in points)
            top, bottom = min(points) // 640, max(points) // 640
            # Disabling the backdrop leaves actual transparent gaps between text.
            interior = [value for y in range(top + 2, bottom - 1) for value in alpha[y * 640 + left + 2:y * 640 + right - 1]]
            self.assertGreater(interior.count(0), len(interior) / 3)

    def test_sources_exclude_unconfirmed_and_unaligned_records(self):
        source = {'kind': 'quran', 'arabic': 'نص', 'translation': 'Source', 'start': 99, 'end': 100}
        quote = {'type': 'quran', 'start': 1, 'end': 3, 'ar': 'نص', 'translation': 'Source', 'source': source,
                 'reviewed': True, 'needs_review': False}
        self.assertEqual(server.make_sources([quote])[0]['start'], 1)
        for changes in ({'reviewed': False}, {'reviewed': 'true'}, {'translation': '  '}, {'candidate': {'kind': 'quran'}},
                        {'source': {**source, 'partial': True, 'alignment_status': 'needs_selection'}}):
            with self.subTest(changes=changes):
                segment = {**quote, **changes}
                self.assertTrue(server.segment_review_pending(segment))
                self.assertEqual(server.make_sources([segment]), [])

    def test_whitespace_translation_has_the_same_placeholder_in_srt_and_ass(self):
        segment = {'type': 'speech', 'ar': 'اختبار', 'translation': ' \n ', 'start': 0, 'end': 1}
        for output in (server.make_srt([segment]), server.make_ass([segment], {})):
            self.assertIn('[Documented translation unavailable]', output)

    @unittest.skipUnless(server.FFMPEG, 'FFmpeg required for frame timing')
    def test_short_cue_is_visible_only_on_its_60fps_video_frame(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(server, 'DATA', Path(temp)):
            folder = server.DATA / ('a' * 32); folder.mkdir()
            src = folder / 'original.mp4'
            subprocess.run([server.FFMPEG, '-v', 'error', '-y', '-f', 'lavfi', '-i',
                            'color=black:s=320x180:r=60:d=0.4', '-c:v', 'libx264', str(src)], check=True, capture_output=True)
            segment = {'type': 'speech', 'ar': 'اختبار', 'translation': 'SHORT CUE', 'start': .111, 'end': .121}
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
            output.with_name('render-manifest-en.json').write_text('{interrupted')
            self.assertTrue(server.render_video(row).is_file())
            self.assertEqual(json.loads(output.with_name('render-manifest-en.json').read_text())['renderer'], server.SUBTITLE_RENDER_VERSION)

    @unittest.skipUnless(server.FFMPEG, 'FFmpeg required for unusual dimensions')
    def test_odd_dimensions_render_on_an_even_h264_canvas(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(server, 'DATA', Path(temp)):
            folder = server.DATA / ('a' * 32); folder.mkdir()
            src = folder / 'original.mkv'
            subprocess.run([server.FFMPEG, '-v', 'error', '-y', '-f', 'lavfi', '-i',
                            'color=black:s=321x181:r=25:d=0.3,format=yuv444p', '-c:v', 'ffv1', str(src)], check=True, capture_output=True)
            segment = {'type': 'speech', 'ar': 'اختبار', 'translation': 'Odd dimensions', 'start': 0, 'end': .3}
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
            segment = {'type': 'speech', 'ar': 'اختبار', 'translation': 'Portrait caption', 'start': 0, 'end': .4}
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
        segment = {'start': 0, 'end': 4, 'type': 'quran', 'ar': 'الجزء المسموع', 'translation': '', 'needs_review': True,
                   'source': {'partial': True, 'arabic': 'مرجع كامل غير مسموع', 'title': 'مرجع للمراجعة'}}
        row = {'status': 'ready', 'segments': json.dumps([segment])}
        self.assertTrue(server.exportable(row))
        self.assertFalse(server.publishable(row))
        self.assertGreaterEqual(len(server.export_warnings(row)), 2)
        srt = server.make_srt([segment])
        self.assertIn('الجزء المسموع', srt)
        self.assertIn('[Documented translation unavailable]', srt)
        self.assertNotIn('مرجع كامل غير مسموع', srt)
        self.assertTrue(segment['needs_review'])
        self.assertFalse(server.exportable({**row, 'status': 'processing'}))

    @unittest.skipUnless(server.FFMPEG, 'FFmpeg required for shared rasterizer')
    def test_large_bilingual_text_fits_and_preview_cache_changes_with_style(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(server, 'DATA', Path(temp)):
            row = {'id': 'a' * 32}
            (server.DATA / row['id']).mkdir()
            segment = {'type': 'quran', 'ar': 'إنا لا نضيع أجر من أحسن عملا',
                       'translation': 'Indeed, We will not allow to be lost the reward of any who did well in deeds.',
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
            long = {**segment, 'ar': segment['ar'] * 4, 'translation': segment['translation'] * 5}
            long_image, size = server.subtitle_image(row, long, style, 640, 360)
            self.assertLess(size, 42)
            self.assertGreaterEqual(alpha_bounds(long_image.read_bytes())[0], 360 * .10)
            blank, _ = server.subtitle_image(row, None, style, 640, 360)
            self.assertIsNone(alpha_bounds(blank.read_bytes()))


if __name__ == '__main__':
    unittest.main()
