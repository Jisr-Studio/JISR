"""Exercise the real HTTP job flow without paid service calls."""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class ProcessingHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.patches = [
            patch.object(server, "DATA", root),
            patch.object(server, "DB", root / "test.sqlite3"),
            patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-elevenlabs", "GEMINI_API_KEY": "test-gemini"}),
            patch.object(server, "lookup_tafsir", return_value={"explanation": "شرح موثق للآية.", "explanation_url": "https://dorar.net/tafseer/2/38", "explanation_status": "available"}),
            patch.object(server, "transcribe", return_value={"words": [
                {"type": "word", "text": "إن", "start": 1, "end": 1.2},
                {"type": "word", "text": "الله", "start": 1.3, "end": 1.5},
                {"type": "word", "text": "يحب", "start": 1.6, "end": 1.8},
                {"type": "word", "text": "التوابين", "start": 1.9, "end": 2.3},
                {"type": "word", "text": "ويحب", "start": 2.4, "end": 2.7},
                {"type": "word", "text": "المتطهرين.", "start": 2.8, "end": 3.4},
            ]}),
            patch.object(server, "post_json", return_value={"status": "completed", "steps": [{"type": "model_output", "content": [{"type": "text", "text": '{"items":[{"id":"SEGMENT_ID","english":"Machine draft","kind":"quran","surah":2,"ayah":222}]}'}]}]}),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        server.initialize_db()
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.base = f"http://127.0.0.1:{self.httpd.server_port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def request(self, path, method="GET", body=None, token=None, content_type="application/json"):
        headers = {"Content-Type": content_type}
        if token:
            headers["X-Edit-Token"] = token
        request = urllib.request.Request(self.base + path, data=body, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read()

    @unittest.skipUnless(server.FFMPEG or server.FFPROBE, "video probe unavailable")
    def test_upload_process_verify_publish(self):
        video = (server.DIST / "demo.mp4").read_bytes()
        boundary = "jisr-http-test"
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="video"; filename="demo.mp4"\r\nContent-Type: video/mp4\r\n\r\n'.encode()
                + video + f"\r\n--{boundary}--\r\n".encode())
        status, raw = self.request("/api/projects", "POST", body, content_type=f"multipart/form-data; boundary={boundary}")
        self.assertEqual(status, 201)
        project = json.loads(raw)
        project_id, token = project["id"], project["edit_token"]

        def source_response(url, timeout=15):
            if "/mushafs/" in url:
                return {"text": "إِنَّ اللَّهَ يُحِبُّ التَّوَّابِينَ وَيُحِبُّ الْمُتَطَهِّرِينَ"}
            if "/translation/" in url:
                return {"translation_text": "Indeed, Allah loves those who repent and purify themselves."}
            return {"book": {"name": "تيسير التفسير"}, "content": [{"text": "شرح موثق للآية."}]}

        original_post = server.post_json
        def model_response(url, payload, headers, timeout=90):
            segment_id = json.loads(payload["input"][0]["content"][0]["text"].split("Input: ", 1)[1])[0]["id"]
            result = json.loads(original_post.return_value["steps"][0]["content"][0]["text"].replace("SEGMENT_ID", segment_id))
            for item in result["items"]:
                item["terms"] = []
                item["parts"] = [{"first_word": 0, "last_word": 5, **{k: item[k] for k in ("english", "kind", "surah", "ayah")}}]
            return {"status": "completed", "steps": [{"type": "model_output", "content": [{"type": "text", "text": json.dumps(result)}]}]}

        with patch.object(server, "get_json", side_effect=source_response), patch.object(server, "post_json", side_effect=model_response):
            status, _ = self.request(f"/api/projects/{project_id}/process", "POST", b"{}", token)
            self.assertEqual(status, 202)
            deadline = time.monotonic() + 5
            while True:
                _, raw = self.request(f"/api/projects/{project_id}", token=token)
                project = json.loads(raw)
                if project["status"] != "processing":
                    break
                self.assertLess(time.monotonic(), deadline)
                time.sleep(.05)

        self.assertEqual(project["status"], "ready", project["error"])
        self.assertFalse(project["publishable"])
        quote = project["segments"][0]
        self.assertEqual(quote["type"], "quran")
        self.assertEqual(quote["source"]["ayah"], 222)
        self.assertEqual(quote["source"]["explanation"], "شرح موثق للآية.")
        self.assertEqual(quote["en"], quote["source"]["english"])
        self.assertTrue(quote["needs_review"])
        self.assertNotIn("candidate", quote)
        with self.assertRaises(urllib.error.HTTPError) as unreviewed:
            self.request(f"/api/projects/{project_id}/export/srt")
        self.assertEqual(unreviewed.exception.code, 409)
        _, raw = self.request(f"/api/projects/{project_id}/segments/{quote['id']}", "POST", b'{"reviewed":true}', token)
        project = json.loads(raw)
        self.assertTrue(project["publishable"])
        _, subtitles = self.request(f"/api/projects/{project_id}/export/srt")
        self.assertIn(quote["source"]["arabic"], subtitles.decode())
        _, public = self.request("/api/share/" + project["share_url"].split("/")[-1])
        self.assertFalse(json.loads(public)["editable"])
        with self.assertRaises(urllib.error.HTTPError) as repeat:
            self.request(f"/api/projects/{project_id}/process", "POST", b"{}", token)
        self.assertEqual(repeat.exception.code, 409)
        self.assertIn("words", quote)
        _, raw = self.request(f"/api/projects/{project_id}/segments/{quote['id']}", "POST", b'{"start":0.9}', token)
        corrected = json.loads(raw)["segments"][0]
        self.assertNotIn("words", corrected)
        self.assertEqual(corrected["type"], "quran")
        _, raw = self.request(f"/api/projects/{project_id}/segments/{quote['id']}", "POST", b'{"ar":"corrected transcript"}', token)
        corrected = json.loads(raw)
        self.assertFalse(corrected["publishable"])
        self.assertIsNone(corrected["segments"][0]["source"])

    def test_manual_citation_link_resolves_candidate_then_requires_confirmation(self):
        for kind, letter in (("quran", "a"), ("hadith", "b")):
            with self.subTest(kind=kind):
                project_id, segment_id = letter * 32, letter * 12
                token, share = "private-edit-token", ("c" if kind == "quran" else "d") * 32
                segment = {"id": segment_id, "start": 0, "end": 5, "ar": "test quotation",
                           "en": "Machine draft", "type": "speech", "source": None,
                           "needs_review": True, "reviewed": False, "candidate": {"kind": kind}}
                with server.db() as con:
                    con.execute("INSERT INTO projects(id,edit_token,share_token,title,filename,status,duration,segments,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?)",
                                (project_id, token, share, "Citation review", "original.mp4", "ready", 5, json.dumps([segment]), time.time(), time.time()))
                source = {"kind": kind, "arabic": "reference quotation", "english": "Reference translation",
                          "narrator": "Reference narrator", "grade": "Reference grade", "attribution": "Reference book"}
                method = "lookup_quran" if kind == "quran" else "lookup_hadith"
                payload = {"surah": 2, "ayah": 222} if kind == "quran" else {"hadith_id": "123"}
                with patch.object(server, method, return_value=source):
                    _, raw = self.request(f"/api/projects/{project_id}/{kind}/{segment_id}", "POST", json.dumps(payload).encode(), token)
                linked = json.loads(raw)
                item = linked["segments"][0]
                self.assertNotIn("candidate", item)
                self.assertEqual(item["en"], source["english"])
                self.assertTrue(item["needs_review"])
                self.assertFalse(item["reviewed"])
                self.assertFalse(linked["publishable"])
                with self.assertRaises(urllib.error.HTTPError) as invalid_review:
                    self.request(f"/api/projects/{project_id}/segments/{segment_id}", "POST", b'{"reviewed":"false"}', token)
                self.assertEqual(invalid_review.exception.code, 400)
                with self.assertRaises(urllib.error.HTTPError) as hidden:
                    self.request("/api/share/" + share)
                self.assertEqual(hidden.exception.code, 409)
                _, raw = self.request(f"/api/projects/{project_id}/segments/{segment_id}", "POST", b'{"reviewed":true}', token)
                self.assertTrue(json.loads(raw)["publishable"])
                _, public = self.request("/api/share/" + share)
                self.assertEqual(json.loads(public)["segments"][0]["source"]["english"], source["english"])

    def test_importing_backend_does_not_reset_a_running_job(self):
        with server.db() as con:
            con.execute("INSERT INTO projects(id,edit_token,share_token,title,filename,status,created,updated) VALUES(?,?,?,?,?,?,?,?)",
                        ("a" * 32, "private", "b" * 32, "Running job", "original.mp4", "processing", time.time(), time.time()))
        target = server.DATA / "jisr.sqlite3"
        shutil.copy2(server.DB, target)
        env = {**os.environ, "JISR_DATA_DIR": str(server.DATA)}
        result = subprocess.run([sys.executable, "-c", "import server"], cwd=Path(server.__file__).parent, env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        with closing(sqlite3.connect(target)) as con:
            self.assertEqual(con.execute("SELECT status FROM projects").fetchone()[0], "processing")

    def test_disconnected_client_does_not_receive_a_second_response(self):
        handler = object.__new__(server.Handler)
        for operation, route in (("get", "do_GET"), ("post", "do_POST")):
            for error in (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                with self.subTest(operation=operation, error=error.__name__):
                    with patch.object(handler, operation, side_effect=error("client disconnected")), patch.object(handler, "fail") as fail:
                        getattr(handler, route)()
                        fail.assert_not_called()

    def test_terminology_provenance_tracks_editor_changes(self):
        project_id, token = "e" * 32, "private-editor"
        segment = {"id": "f" * 12, "start": 0, "end": 5, "ar": "الاجتهاد علم", "en": "Ijtihad is a discipline.",
                   "type": "speech", "source": None, "needs_review": False, "reviewed": False,
                   "detected_terms": ["الاجتهاد"], "terminology": [{"term": "الاجتهاد", "url": "https://islamic-content.com/dictionary/word/196"}]}
        with server.db() as con:
            con.execute("INSERT INTO projects(id,edit_token,share_token,title,filename,status,duration,segments,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (project_id, token, "f" * 32, "Dictionary review", "original.mp4", "ready", 5, json.dumps([segment]), time.time(), time.time()))
        path = f"/api/projects/{project_id}/segments/{segment['id']}"
        _, raw = self.request(path, "POST", b'{"en":"Edited by the reviewer."}', token)
        item = json.loads(raw)["segments"][0]
        self.assertTrue(item["terminology_edited"])
        self.assertEqual(item["terminology"][0]["url"], segment["terminology"][0]["url"])
        _, raw = self.request(path, "POST", json.dumps({"ar": "نص جديد"}).encode(), token)
        item = json.loads(raw)["segments"][0]
        for field in ("terminology", "detected_terms", "terminology_edited"):
            self.assertNotIn(field, item)

    def test_automatic_hadith_translation_requires_confirmation_before_export(self):
        project_id, token, segment_id = "7" * 32, "test-editor", "8" * 12
        spoken = "الطهور شطر الإيمان"
        segment = {"id": segment_id, "start": 0, "end": 4, "ar": spoken, "en": "", "type": "speech", "source": None, "needs_review": False}
        with server.db() as con:
            con.execute("INSERT INTO projects(id,edit_token,share_token,title,filename,status,duration,segments,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (project_id, token, "9" * 32, "Automatic Hadith", "original.mp4", "uploaded", 5, json.dumps([segment]), time.time(), time.time()))
        translated = {"status": "completed", "steps": [{"type": "model_output", "content": [{"type": "text", "text": json.dumps({"items": [{"id": segment_id, "english": "Machine draft", "kind": "hadith", "hadith_query": spoken, "terms": []}]})}]}]}
        fragment = f'<div>{spoken}</div><div class="hadith-info">الراوي : أبو مالك الأشعري | المحدث : مسلم | المصدر : صحيح مسلم | خلاصة حكم المحدث : صحيح</div>'
        reference = {"kind": "hadith", "arabic": spoken, "english": "Source translation", "explanation": "شرح موثق", "narrator": "أبو مالك الأشعري", "grade": "صحيح", "attribution": "مسلم", "url": "https://hadeethenc.com/ar/browse/hadith/65004", "translation_status": "sourced", "verification": {"provider": "Dorar"}}
        with patch.object(server, "post_json", return_value=translated), patch.object(server, "get_json", return_value={"ahadith": {"result": fragment}}), patch.object(server, "enrich_hadith_translation", return_value=reference):
            self.request(f"/api/projects/{project_id}/process", "POST", b"{}", token)
            deadline = time.monotonic() + 5
            while True:
                _, raw = self.request(f"/api/projects/{project_id}", token=token)
                project = json.loads(raw)
                if project["status"] != "processing": break
                self.assertLess(time.monotonic(), deadline)
                time.sleep(.05)
        self.assertEqual(project["status"], "ready", project["error"])
        self.assertFalse(project["publishable"])
        self.assertEqual(project["segments"][0]["en"], "Source translation")
        self.assertEqual(project["segments"][0]["source"]["explanation"], "شرح موثق")
        _, raw = self.request(f"/api/projects/{project_id}/segments/{segment_id}", "POST", b'{"reviewed":true}', token)
        self.assertTrue(json.loads(raw)["publishable"])
        _, subtitles = self.request(f"/api/projects/{project_id}/export/srt")
        self.assertIn(b"Source translation", subtitles)
        self.assertNotIn(b"Machine draft", subtitles)

    def test_partial_quote_selects_source_excerpt_before_review_and_export(self):
        project_id, token, segment_id = "4" * 32, "partial-editor", "5" * 12
        spoken = "الطهور شطر الإيمان"
        english = "The Prophet said: Purity is half of faith, and praise fills the Scale."
        excerpt = "Purity is half of faith,"
        segment = {"id": segment_id, "start": 0, "end": 4, "ar": spoken, "en": "Machine draft"}
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            server.attach_source(segment, "hadith", {"arabic": spoken + " والحمد لله تملأ الميزان", "english": english, "partial": True})
        with server.db() as con:
            con.execute("INSERT INTO projects(id,edit_token,share_token,title,filename,status,duration,segments,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (project_id, token, "6" * 32, "Partial quote", "original.mp4", "ready", 5, json.dumps([segment]), time.time(), time.time()))
        path = f"/api/projects/{project_id}/segments/{segment_id}"
        with self.assertRaises(urllib.error.HTTPError) as pending:
            self.request(path, "POST", b'{"reviewed":true}', token)
        self.assertEqual(pending.exception.code, 409)
        start = english.index(excerpt)
        span = {"start": start, "end": start + len(excerpt)}
        with self.assertRaises(urllib.error.HTTPError) as inconsistent:
            self.request(path, "POST", json.dumps({"source_english_span": span, "en": "Generated wording"}).encode(), token)
        self.assertEqual(inconsistent.exception.code, 400)
        _, raw = self.request(path, "POST", json.dumps({"source_english_span": span, "en": excerpt, "reviewed": True, "start": 0, "end": 4}).encode(), token)
        project = json.loads(raw)
        self.assertTrue(project["publishable"])
        self.assertEqual(project["segments"][0]["type"], "hadith")
        self.assertEqual(project["segments"][0]["source"]["english"], english)
        self.assertEqual(project["segments"][0]["source"]["alignment_status"], "selected")
        _, subtitles = self.request(f"/api/projects/{project_id}/export/srt")
        self.assertIn(excerpt.encode(), subtitles)
        self.assertNotIn(b"praise fills", subtitles)
        _, sources = self.request(f"/api/projects/{project_id}/export/sources")
        self.assertEqual(json.loads(sources)[0]["english"], english)


if __name__ == "__main__":
    unittest.main()
