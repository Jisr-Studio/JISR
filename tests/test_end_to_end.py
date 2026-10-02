"""Full HTTP pipeline with fake external transports and real FFmpeg.

Reference bodies below are synthetic test fixtures, not approved datasets.
No paid API or public-source request is allowed to escape this test.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from email.message import Message
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


VERSE = "إن الله يحب التوابين ويحب المتطهرين"
VERSE_AR = "ويسألونك عن المحيض قل هو أذى " + VERSE
VERSE_EXCERPT = "Indeed, Allah loves those who repent and purify themselves."
VERSE_EN = "Synthetic verse prefix. " + VERSE_EXCERPT
HADITH = "من توضأ فأحسن الوضوء خرجت خطاياه"
HADITH_AR = "عن عثمان بن عفان قال: " + HADITH + " من جسده حتى تخرج من تحت أظفاره"
HADITH_EXCERPT = "Whoever performs ablution well, his sins leave"
HADITH_EN = "Uthman reported: " + HADITH_EXCERPT + " his body, even from under his nails."
TRANSCRIPT = "الوضوء عبادة " + VERSE + " وقال النبي " + HADITH + " فلنحافظ عليه"


class ExternalResponse(io.BytesIO):
    def __init__(self, value):
        raw = json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value
        super().__init__(raw.encode("utf-8"))
        self.headers = Message()
        self.headers["Content-Type"] = "text/plain; charset=utf-8"


@unittest.skipUnless(server.FFMPEG, "FFmpeg is required for the full integration test")
class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.calls = []
        self.media = self.root / "fixture.mp4"
        # Real audio from 6s to 8s deliberately has no returned transcript.
        result = subprocess.run([
            server.FFMPEG, "-y", "-i", str(server.DIST / "demo.mp4"),
            "-f", "lavfi", "-i", "sine=frequency=500:duration=2",
            "-filter_complex", "[1:a]adelay=6000|6000[a]", "-map", "0:v",
            "-map", "[a]", "-t", "8", "-c:v", "copy", "-c:a", "aac", str(self.media),
        ], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr[-1000:])
        for item in (
            patch.object(server, "DATA", self.root),
            patch.object(server, "DB", self.root / "test.sqlite3"),
            patch.object(server, "RECENT_UPLOADS", {}),
            patch.object(server, "TAFSIR_INDEX", {}),
            patch.object(server, "TERM_CACHE", {}),
            patch.dict(os.environ, {"ELEVENLABS_API_KEY": "fake-stt", "GEMINI_API_KEY": "fake-translation"}),
        ):
            item.start()
            self.addCleanup(item.stop)
        server.initialize_db()
        self.real_urlopen = urllib.request.urlopen
        transport = patch.object(server.urllib.request, "urlopen", side_effect=self.external_transport)
        transport.start()
        self.addCleanup(transport.stop)
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.base = f"http://127.0.0.1:{self.httpd.server_port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def external_transport(self, request, *args, **kwargs):
        url = request.full_url if isinstance(request, urllib.request.Request) else request
        parsed = urllib.parse.urlsplit(url)
        if parsed.netloc == urllib.parse.urlsplit(self.base).netloc:
            return self.real_urlopen(request, *args, **kwargs)
        self.calls.append(url)
        if url == "https://api.elevenlabs.io/v1/speech-to-text":
            self.assertEqual(request.get_header("Xi-api-key"), "fake-stt")
            self.assertFalse(isinstance(request.data, bytes))  # Stream media from disk.
            body = b"".join(request.data)
            self.assertEqual(len(body), int(request.get_header("Content-length")))
            self.assertIn(b"scribe_v2", body)
            self.assertIn(self.media.read_bytes(), body)
            return ExternalResponse({"words": [
                {"type": "word", "text": text, "start": i * .25, "end": i * .25 + .2,
                 "logprob": -2 if i == 0 else -.1}
                for i, text in enumerate(TRANSCRIPT.split())
            ]})
        if parsed.netloc == "generativelanguage.googleapis.com":
            self.assertEqual(request.get_header("X-goog-api-key"), "fake-translation")
            payload = json.loads(request.data)
            self.assertFalse(payload["store"])
            self.assertEqual(parsed.path, "/v1/interactions")
            self.assertEqual(payload["input"][0]["type"], "user_input")
            inputs = json.loads(payload["input"][0]["content"][0]["text"].split("Input: ", 1)[1])
            if isinstance(inputs, dict):
                excerpt = VERSE_EXCERPT if inputs["full_english"] == VERSE_EN else HADITH_EXCERPT
                result = {"english_excerpt": excerpt, "confident": True}
            elif "dictionary" in inputs[0]:
                self.assertEqual(len(inputs), 1)
                self.assertEqual(inputs[0]["dictionary"][0]["english_term"], "Ablution")
                result = {"items": [{"id": inputs[0]["id"], "english": "Ablution is worship."}]}
            else:
                self.assertEqual(len(inputs), 1)
                self.assertEqual(inputs[0]["arabic"], TRANSCRIPT)
                result = {"items": [{"id": inputs[0]["id"], "terms": ["الوضوء"], "parts": [
                    {"first_word": 0, "last_word": 1, "kind": "speech", "english": "Ritual washing is worship."},
                    {"first_word": 2, "last_word": 7, "kind": "quran", "english": "Verse machine draft", "surah": 2, "ayah": 222},
                    {"first_word": 8, "last_word": 9, "kind": "speech", "english": "And the Prophet said"},
                    {"first_word": 10, "last_word": 15, "kind": "hadith", "english": "Hadith machine draft", "hadith_query": HADITH},
                    {"first_word": 16, "last_word": 17, "kind": "speech", "english": "So let us maintain it."},
                ]}]}
            return ExternalResponse({"status": "completed", "steps": [{"type": "model_output", "content": [{"type": "text", "text": json.dumps(result)}]}]})
        if url.startswith("https://islamic-content.com/api/search_words?"):
            self.assertEqual(request.get_header("X-requested-with"), "XMLHttpRequest")
            return ExternalResponse({"table_data": '<a href="/dictionary/word/10922">الوضوء</a>'})
        if url == "https://islamic-content.com/dictionary/word/10922":
            return ExternalResponse('<div class="entry-wraper"><h1>الوضوء</h1><div class="entry-main-content"><p>تعريف عربي للاختبار.</p></div><a href="/dictionary/word/10922/en">English</a></div>')
        if url == "https://islamic-content.com/dictionary/word/10922/en":
            return ExternalResponse('<div class="entry-wraper"><h1>Ablution (الوضوء)</h1><div class="entry-main-content"><p>A synthetic dictionary definition.</p></div></div>')
        if url == "https://api.quranpedia.net/v1/mushafs/1/2/222":
            return ExternalResponse({"text": VERSE_AR})
        if url == "https://api.quranpedia.net/v1/translation/1947/2/222":
            return ExternalResponse({"translation_text": VERSE_EN})
        if url == "https://dorar.net/tafseer/2":
            return ExternalResponse('<select id="soora"><option value="2">سورة البقرة</option></select><select id="sect"><option value="38">الآيات (221 - 224)</option></select>')
        if url == "https://dorar.net/tafseer/2/38":
            return ExternalResponse('<article id="tt4"><p>Synthetic tafsir explanation.</p><p>Source reference.</p></article>')
        if url.startswith("https://dorar.net/dorar_api.json?"):
            return ExternalResponse({"ahadith": {"result": f'<div>{HADITH_AR}</div><div class="hadith-info">الراوي : عثمان بن عفان | المحدث : مسلم | المصدر : صحيح مسلم | الصفحة أو الرقم : 245 | خلاصة حكم المحدث : صحيح</div>'}})
        if url == "https://hadeethenc.com/ar/ajax/search":
            self.assertEqual(urllib.parse.parse_qs(request.data.decode())["term"], [HADITH])
            return ExternalResponse(f'<a href="/ar/browse/hadith/6263">{HADITH_AR}</a>')
        if url.startswith("https://hadeethenc.com/api/v1/hadeeths/one/?"):
            query = urllib.parse.parse_qs(parsed.query)
            self.assertEqual(query["id"], ["6263"])
            if query["language"] == ["ar"]:
                return ExternalResponse({"id": "6263", "hadeeth": HADITH_AR, "narrator": "عثمان بن عفان",
                                         "grade": "صحيح", "attribution": "رواه مسلم", "explanation": "شرح للاختبار."})
            return ExternalResponse({"id": "6263", "hadeeth": HADITH_EN, "explanation": "Synthetic English explanation."})
        raise AssertionError("Unexpected external request: " + url)

    def request(self, path, method="GET", body=None, token=None, content_type="application/json"):
        headers = {"Content-Type": content_type}
        if token:
            headers["X-Edit-Token"] = token
        request = urllib.request.Request(self.base + path, data=body, headers=headers, method=method)
        with self.real_urlopen(request, timeout=40) as response:
            return response.status, response.read()

    def test_mixed_transcript_sources_review_exports_and_share(self):
        boundary = "end-to-end-upload"
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="video"; filename="fixture.mp4"\r\nContent-Type: video/mp4\r\n\r\n'.encode()
                + self.media.read_bytes() + f"\r\n--{boundary}--\r\n".encode())
        status, raw = self.request("/api/projects", "POST", body, content_type=f"multipart/form-data; boundary={boundary}")
        self.assertEqual(status, 201)
        project = json.loads(raw)
        project_id, token = project["id"], project["edit_token"]
        prefix = f"/api/projects/{project_id}"
        self.assertEqual(self.request(prefix + "/process", "POST", b"{}", token)[0], 202)
        deadline = time.monotonic() + 15
        while True:
            _, raw = self.request(prefix, token=token)
            project = json.loads(raw)
            if project["status"] != "processing":
                break
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.05)
        self.assertEqual(project["status"], "ready", project["error"])
        self.assertFalse(project["publishable"])
        parts = [s for s in project["segments"] if not s.get("audio_gap")]
        gaps = [s for s in project["segments"] if s.get("audio_gap")]
        self.assertEqual([s["type"] for s in parts], ["speech", "quran", "speech", "hadith", "speech"])
        self.assertEqual(" ".join(s["ar"] for s in parts), TRANSCRIPT)
        self.assertEqual(parts[0]["en"], "Ablution is worship.")
        self.assertTrue(parts[0]["unclear_words"])
        self.assertEqual(parts[0]["terminology"][0]["status"], "bilingual")
        self.assertEqual(parts[1]["en"], VERSE_EXCERPT)
        self.assertEqual(parts[1]["source"]["english"], VERSE_EN)
        self.assertIn("Source reference.", parts[1]["source"]["explanation"])
        self.assertEqual(parts[3]["en"], HADITH_EXCERPT)
        self.assertEqual(parts[3]["source"]["english"], HADITH_EN)
        self.assertEqual(parts[3]["source"]["verification"]["provider"], "Dorar")
        self.assertEqual(parts[3]["source"]["translation_status"], "sourced")
        for quote in (parts[1], parts[3]):
            self.assertTrue(quote["needs_review"])
            self.assertEqual(quote["source"]["alignment_status"], "matched")
            self.assertIn(quote["source"]["subtitle_arabic"], quote["source"]["arabic"])
        self.assertEqual((parts[1]["start"], parts[1]["end"]), (.5, 1.95))
        self.assertEqual((parts[3]["start"], parts[3]["end"]), (2.5, 3.95))
        self.assertEqual(len(gaps), 1)
        self.assertGreaterEqual(gaps[0]["start"], 5.9)
        share_path = "/api/share/" + project["share_url"].split("/")[-1]
        for path in (prefix + "/export/srt", prefix + "/export/mp4", share_path):
            with self.assertRaises(urllib.error.HTTPError) as blocked:
                self.request(path, token=token)
            self.assertEqual(blocked.exception.code, 409)
        # Every flagged phrase is confirmed, then the intentionally synthetic tone is dismissed.
        for segment in parts:
            if segment["needs_review"]:
                self.request(prefix + "/segments/" + segment["id"], "POST", b'{"reviewed":true}', token)
        _, raw = self.request(prefix, token=token)
        self.assertFalse(json.loads(raw)["publishable"])  # The audio gap still blocks publication.
        self.request(prefix + "/segments/" + gaps[0]["id"], "POST", b'{"dismiss_gap":true}', token)
        self.request(prefix + "/style", "POST", b'{"font":"amiri","size":26,"position":"bottom","bilingual":true}', token)
        _, raw = self.request(prefix, token=token)
        self.assertTrue(json.loads(raw)["publishable"])
        _, subtitles = self.request(prefix + "/export/srt")
        subtitle_text = subtitles.decode()
        for expected in ("Ablution is worship.", VERSE_EXCERPT, "And the Prophet said", HADITH_EXCERPT, "So let us maintain it."):
            self.assertIn(expected, subtitle_text)
        for unspoken in ("Synthetic verse prefix.", "under his nails", "machine draft"):
            self.assertNotIn(unspoken, subtitle_text)
        self.assertIn("00:00:00,500 --> 00:00:01,950", subtitle_text)
        _, raw = self.request(prefix + "/export/sources")
        references = json.loads(raw)
        self.assertEqual(len(references), 2)
        self.assertEqual(references[0]["english"], VERSE_EN)
        self.assertEqual(references[1]["english"], HADITH_EN)
        _, raw = self.request(share_path)
        shared = json.loads(raw)
        self.assertFalse(shared["editable"])
        self.assertNotIn("edit_token", shared)
        self.assertNotIn(token, raw.decode())
        with self.assertRaises(urllib.error.HTTPError) as private:
            self.request(prefix + "/style", "POST", b'{"size":30}')
        self.assertEqual(private.exception.code, 403)
        _, rendered = self.request(prefix + "/export/mp4", token=token)
        self.assertIn(b"ftyp", rendered[:32])
        target = self.root / project_id / "translated.mp4"
        self.assertTrue(server.has_video_stream(target))
        self.assertAlmostEqual(server.video_duration(target), 8, delta=.3)
        self.assertGreater(target.stat().st_size, 1000)
        ass = target.with_name("subtitles.ass").read_text(encoding="utf-8")
        self.assertIn(HADITH_EXCERPT, ass)
        self.assertNotIn("under his nails", ass)
        self.assertEqual(sum("generativelanguage.googleapis.com" in url for url in self.calls), 4)
        self.assertEqual(sum("api.elevenlabs.io" in url for url in self.calls), 1)
        self.assertEqual(self.request(prefix, "DELETE", token=token)[0], 200)
        self.assertFalse(target.parent.exists())
        self.assertIsNone(server.project_row(project_id))


if __name__ == "__main__":
    unittest.main()
