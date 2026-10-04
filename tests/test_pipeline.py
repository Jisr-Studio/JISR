import sys
import json
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class PipelineTests(unittest.TestCase):
    @patch.object(server, "get_json")
    def test_paraphrase_reference_keeps_spoken_text_and_requires_review(self, get_json):
        ar = {"id": 4817, "hadeeth": "عن أبي هريرة رضي الله عنه عن النبي قال: أذنب عبد ذنبا فقال اللهم اغفر لي ذنبي", "grade": "صحيح", "attribution": "متفق عليه"}
        en = {"id": 4817, "hadeeth": "A servant committed a sin and asked for forgiveness."}
        spoken = "أذنب عبد ذنبا فقال اللهم إني أذنب ذنبا اللهم اغفر لي"
        get_json.return_value = ar
        with self.assertRaises(ValueError):
            server.lookup_hadith("4817", spoken)
        get_json.side_effect = [ar, en]
        source = server.lookup_hadith("4817", spoken, paraphrase=True)
        self.assertEqual(source["narrator"], "أبي هريرة")
        segment = {"ar": spoken, "en": "Speaker's translation", "candidate": {"kind": "hadith"}}
        server.attach_source(segment, "hadith", source)
        self.assertEqual(segment["ar"], spoken)
        self.assertEqual(segment["en"], "Speaker's translation")
        self.assertEqual(segment["source"]["english"], en["hadeeth"])
        self.assertTrue(segment["needs_review"])
        self.assertFalse(segment["reviewed"])
        row = {"status": "ready", "segments": json.dumps([segment])}
        self.assertFalse(server.publishable(row))
        segment.update(start=1.88, end=6.46, reviewed=True, needs_review=False)
        row["segments"] = json.dumps([segment])
        self.assertTrue(server.publishable(row))
        self.assertIn("[Hadith paraphrase]", server.make_srt([segment]))
        self.assertIn("[Hadith paraphrase]", server.make_ass([segment], {}))
        self.assertEqual(server.make_sources([segment])[0]["quotation_mode"], "paraphrase")
        with self.assertRaises(ValueError):
            server.select_source_english(source, spoken, {"start": 0, "end": 10})

    def test_audio_gap_marks_untranscribed_sound_for_review(self):
        log = "silence_start: 0\nsilence_end: 1 | silence_duration: 1\nsilence_start: 7\nsilence_end: 8 | silence_duration: 1"
        spoken = [{"start": 1.0, "end": 3.0, "ar": "كلام مسموع"}]
        gaps = server.audio_gaps_from_log(log, spoken, 8.0)
        self.assertEqual(len(gaps), 1)
        self.assertEqual((gaps[0]["start"], gaps[0]["end"]), (3.35, 7.0))
        self.assertTrue(gaps[0]["audio_gap"] and gaps[0]["needs_review"])
        self.assertEqual(gaps[0]["en"], "")

    def test_proxy_client_identity_requires_explicit_trust(self):
        headers = {"X-Real-IP": "203.0.113.9"}
        with patch.dict("os.environ", {"JISR_TRUST_PROXY": "0"}):
            self.assertEqual(server.client_identity("127.0.0.1", headers), "127.0.0.1")
        with patch.dict("os.environ", {"JISR_TRUST_PROXY": "1"}):
            self.assertEqual(server.client_identity("127.0.0.1", headers), "203.0.113.9")
            self.assertEqual(server.client_identity("127.0.0.1", {"X-Real-IP": "not-an-ip"}), "127.0.0.1")

    @unittest.skipUnless(server.FFMPEG or server.FFPROBE, "FFmpeg probe unavailable")
    def test_video_probe_rejects_nonvideo(self):
        self.assertTrue(server.has_video_stream(server.DIST / "demo.mp4"))
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder) / "not-video.mp4"
            fake.write_bytes(b"not video data")
            self.assertFalse(server.has_video_stream(fake))

    def test_render_proxy_separates_judges_and_ignores_untrusted_real_ip(self):
        headers = {"X-Forwarded-For": "203.0.113.9, 10.0.0.1", "X-Real-IP": "198.51.100.4"}
        with patch.dict("os.environ", {"JISR_TRUST_PROXY": "render"}):
            self.assertEqual(server.client_identity("10.0.0.2", headers), "203.0.113.9")
            self.assertEqual(server.client_identity("10.0.0.2", {"X-Forwarded-For": "2001:db8::1"}), "2001:db8::1")
            self.assertEqual(server.client_identity("10.0.0.2", {"X-Forwarded-For": "invalid"}), "10.0.0.2")
            self.assertEqual(server.client_identity("10.0.0.2", {"X-Real-IP": "198.51.100.4"}), "10.0.0.2")
        with patch.dict("os.environ", {"JISR_TRUST_PROXY": "0"}):
            self.assertEqual(server.client_identity("10.0.0.2", headers), "10.0.0.2")

    def test_multipart_upload_streams_binary_across_chunk_boundaries(self):
        boundary = "----jisr-test-boundary"
        video_bytes = b"x" * 65_530 + b"\r\n--" + boundary.encode() + b"NO" + b"y" * 100_000
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"video\"; filename=\"clip.mp4\"\r\nContent-Type: video/mp4\r\n\r\n".encode()
                + video_bytes + f"\r\n--{boundary}--\r\n".encode())
        with tempfile.TemporaryDirectory() as folder:
            name, filename = server.save_video_upload(io.BytesIO(body), len(body), f"multipart/form-data; boundary={boundary}", Path(folder))
            self.assertEqual((name, filename), ("clip.mp4", "original.mp4"))
            self.assertEqual((Path(folder) / filename).read_bytes(), video_bytes)
            with self.assertRaises(ValueError):
                server.save_video_upload(io.BytesIO(body[:-8]), len(body) - 8, f"multipart/form-data; boundary={boundary}", Path(folder))

    @patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test-key"})
    @patch.object(server.urllib.request, "urlopen")
    def test_scribe_upload_streams_file(self, urlopen):
        urlopen.return_value = io.BytesIO(b'{"words": []}')
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder) / "clip.mp4"
            video.write_bytes(b"video-bytes")
            self.assertEqual(server.transcribe(video), {"words": []})
            request = urlopen.call_args.args[0]
            self.assertFalse(isinstance(request.data, bytes))
            body = b"".join(request.data)
        self.assertIn(b"video-bytes", body)
        self.assertEqual(int(request.get_header("Content-length")), len(body))

    def test_word_grouping_and_review(self):
        words = [
            {"type": "word", "text": "الوضوء", "start": 0.0, "end": .5, "logprob": -.2},
            {"type": "word", "text": "عبادة.", "start": .6, "end": 1.1, "logprob": -1.9},
            {"type": "word", "text": "الحمد", "start": 3.0, "end": 3.4, "logprob": -.2},
        ]
        segments = server.words_to_segments(words)
        self.assertEqual(len(segments), 2)
        self.assertTrue(segments[0]["needs_review"])
        self.assertEqual((segments[0]["start"], segments[0]["end"]), (0.0, 1.1))

    @patch.object(server, "lookup_tafsir", return_value={"explanation": "شرح الآية.", "explanation_url": "https://dorar.net/tafseer/2/38", "explanation_status": "available"})
    @patch.object(server, "get_json")
    def test_quran_verification_uses_reference_translation(self, get_json, lookup_tafsir):
        get_json.side_effect = [
            {"text": "\ufeff\ufeffإِنَّ اللَّهَ يُحِبُّ التَّوَّابِينَ وَيُحِبُّ الْمُتَطَهِّرِينَ"},
            {"translation_text": "Indeed, Allah loves those who are constantly repentant."},
            {"book": {"name": "تيسير التفسير"}, "content": [{"text": "شرح الآية."}]},
        ]
        seg = {"ar": "إن الله يحب التوابين ويحب المتطهرين", "en": "machine draft", "type": "speech", "candidate": {"surah": 2, "ayah": 222}}
        self.assertTrue(server.verify_quran(seg))
        self.assertEqual(seg["source"]["translator"], "Saheeh International")
        self.assertFalse(seg["source"]["arabic"].startswith("\ufeff"))
        self.assertEqual(seg["source"]["explanation"], "شرح الآية.")
        self.assertNotEqual(seg["en"], "machine draft")
        self.assertTrue(seg["needs_review"])
        self.assertFalse(seg["reviewed"])
        self.assertNotIn("candidate", seg)

    @patch.object(server, "get_json")
    def test_quran_rejects_unrelated_text(self, get_json):
        get_json.return_value = {"text": "قُلْ هُوَ اللَّهُ أَحَدٌ"}
        seg = {"ar": "الوضوء عبادة عظيمة", "en": "Ablution is worship", "type": "speech", "candidate": {"surah": 112, "ayah": 1}}
        self.assertFalse(server.verify_quran(seg))
        self.assertEqual(get_json.call_count, 1)

    @patch.object(server, "enrich_hadith_translation", side_effect=lambda spoken, query, reference: reference)
    def test_dorar_parser_and_review_gate(self, enrich):
        fragment = '<div class="hadith">1 - الطُّهُورُ شَطْرُ الإِيمَانِ</div><div class="hadith-info"><span class="info-subtitle">الراوي :</span> أبو مالك الأشعري <span class="info-subtitle">المحدث :</span> مسلم <span class="info-subtitle">المصدر :</span> صحيح مسلم <span class="info-subtitle">الصفحة أو الرقم :</span> 223 <span class="info-subtitle">خلاصة حكم المحدث :</span> صحيح</div>'
        parsed = server.parse_dorar(fragment)
        self.assertEqual(parsed[0]["narrator"], "أبو مالك الأشعري")
        self.assertEqual(parsed[0]["grade"], "صحيح")
        with patch.object(server, "get_json", return_value={"ahadith": {"result": fragment}}), patch.object(server, "get_html", return_value=""):
            seg = {"start": 0, "end": 4, "ar": "الطهور شطر الإيمان", "en": "Purification is half of faith.", "candidate": {"hadith_query": "الطهور شطر الإيمان"}, "type": "speech"}
            self.assertTrue(server.verify_hadith(seg))
            self.assertTrue(seg["needs_review"])
            self.assertEqual(server.make_sources([seg]), [])
            seg["needs_review"] = False
            self.assertEqual(len(server.make_sources([seg])), 1)
        with patch.object(server, "get_json", return_value={"ahadith": [{"th": fragment}]}):
            seg = {"ar": "الطهور شطر الإيمان", "en": "Purification is half of faith.", "candidate": {"hadith_query": "الطهور شطر الإيمان"}, "type": "speech"}
            self.assertTrue(server.verify_hadith(seg))

    @patch.object(server, "get_json")
    def test_hadeethenc_id_requires_text_match(self, get_json):
        get_json.side_effect = [
            {"hadeeth": "عن أبي مالك الأشعري -رضي الله عنه- قَالَ: الطهور شطر الإيمان", "grade": "صحيح", "attribution": "رواه مسلم", "title": "الطهور شطر الإيمان"},
            {"hadeeth": "Purification is half of faith."},
        ]
        source = server.lookup_hadith("123", "الطهور شطر الإيمان")
        self.assertEqual(source["english"], "Purification is half of faith.")
        self.assertEqual(source["grade"], "صحيح")
        self.assertEqual(source["narrator"], "أبي مالك الأشعري")
        with self.assertRaises(ValueError):
            server.lookup_hadith("bad-id", "الطهور شطر الإيمان")

    def test_subtitle_exports(self):
        segments = [{"start": 1.25, "end": 3.5, "type": "speech", "ar": "بسم الله", "en": "In the name of Allah.", "source": None}]
        self.assertIn("00:00:01,250 --> 00:00:03,500", server.make_srt(segments))
        self.assertIn("In the name of Allah.", server.make_ass(segments, {"backdrop": True, "color": "#ffffff"}))
        segments[0].update(type="quran", needs_review=False, reviewed=True)
        self.assertIn("بسم الله\\NIn the name of Allah.", server.make_ass(segments, {"bilingual": True}))
        segments[0]["source"] = {"arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"}
        self.assertIn("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", server.make_srt(segments))
        self.assertIn("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", server.make_ass(segments, {"bilingual": True}))
        row = {"status": "ready", "segments": json.dumps(segments)}
        self.assertTrue(server.publishable(row))
        segments[0]["reviewed"] = False
        row["segments"] = json.dumps(segments)
        self.assertFalse(server.publishable(row))
        segments[0]["reviewed"] = True
        segments[0]["candidate"] = {"kind": "quran", "surah": 1, "ayah": 1}
        row["segments"] = json.dumps(segments)
        self.assertFalse(server.publishable(row))
        del segments[0]["candidate"]
        segments[0]["needs_review"] = True
        row["segments"] = json.dumps(segments)
        self.assertFalse(server.publishable(row))

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "post_json")
    def test_openai_responses_contract(self, post_json):
        post_json.return_value = {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": '{"items":[{"id":"one","english":"Ablution is worship.","kind":"speech","terms":[]}]}'}]}]}
        segments = [{"id": "one", "ar": "الوضوء عبادة", "en": "", "needs_review": False},
                    {"id": "gap", "ar": "", "en": "", "audio_gap": True, "needs_review": True}]
        server.translate_segments(segments)
        self.assertEqual(segments[0]["en"], "Ablution is worship.")
        self.assertEqual(segments[1]["en"], "")
        url, payload, headers = post_json.call_args.args
        self.assertEqual(url, "https://api.openai.com/v1/responses")
        self.assertIsInstance(payload["input"], str)
        self.assertEqual(payload["model"], server.OPENAI_MODEL)
        self.assertTrue(payload["text"]["format"]["strict"])
        self.assertEqual(headers["Authorization"], "Bearer test-key")

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "post_json")
    def test_translation_retry_skips_completed_batches(self, post_json):
        size = server.TRANSLATION_BATCH_SIZE
        segments = [{"id": str(i), "ar": "الوضوء", "en": "", "needs_review": False} for i in range(size + 1)]
        first = {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps({"items": [{"id": str(i), "english": "Ablution", "kind": "speech", "terms": []} for i in range(size)]})}]}]}
        last = {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps({"items": [{"id": str(size), "english": "Ablution", "kind": "speech", "terms": []}]})}]}]}
        snapshots = []
        post_json.side_effect = [first, RuntimeError("temporary failure")]
        with self.assertRaises(RuntimeError):
            server.translate_segments(segments, checkpoint=lambda items: snapshots.append(json.dumps(items)))
        self.assertEqual(len(snapshots), 1)
        self.assertTrue(all(item["en"] for item in segments[:size]))
        self.assertFalse(segments[size]["en"])
        post_json.side_effect = [last]
        server.translate_segments(segments)
        self.assertEqual(len(json.loads(post_json.call_args.args[1]["input"].split("Input: ", 1)[1])), 1)
        self.assertTrue(all(item["en"] for item in segments))

    @patch.object(server, "project_row")
    @patch.object(server, "save_project")
    @patch.object(server, "transcribe")
    @patch.object(server, "translate_segments")
    @patch.object(server, "verify_quran")
    def test_background_processing_reaches_review_state(self, verify_quran, translate_segments, transcribe, save_project, project_row):
        project_row.return_value = {"id": "a" * 32, "filename": "original.mp4", "segments": "[]", "duration": 0}
        transcribe.return_value = {"words": [{"type": "word", "text": "الوضوء", "start": 0, "end": .5}, {"type": "word", "text": "عبادة.", "start": .6, "end": 1.0}]}
        def classify(items, checkpoint=None):
            items[0]["en"] = "Ablution is worship."
            items[0]["candidate"] = {"kind": "quran", "surah": 1, "ayah": 1}
            return items
        translate_segments.side_effect = classify
        verify_quran.return_value = False
        self.assertTrue(server.PROCESS_SLOTS.acquire(blocking=False))
        server.process_project("a" * 32)
        final = save_project.call_args_list[-1].kwargs
        self.assertEqual(final["status"], "ready")
        self.assertIn('"needs_review": true', final["segments"])
        self.assertIn('"candidate": {"kind": "quran"', final["segments"])

    @patch.object(server, "project_row")
    @patch.object(server, "save_project")
    @patch.object(server, "transcribe")
    @patch.object(server, "translate_segments")
    def test_retry_reuses_saved_transcript_and_translation(self, translate_segments, transcribe, save_project, project_row):
        segment = {"id": "one", "ar": "الوضوء عبادة", "en": "Ablution is worship.", "start": 0, "end": 1,
                   "type": "speech", "source": None, "needs_review": False, "candidate": {"kind": "speech"}}
        project_row.return_value = {"id": "a" * 32, "filename": "original.mp4", "segments": json.dumps([segment]), "duration": 3}
        self.assertTrue(server.PROCESS_SLOTS.acquire(blocking=False))
        server.process_project("a" * 32)
        transcribe.assert_not_called()
        translate_segments.assert_not_called()
        self.assertEqual(save_project.call_args_list[-1].kwargs["status"], "ready")


if __name__ == "__main__":
    unittest.main()
