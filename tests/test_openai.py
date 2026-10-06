"""Responses transport, exact word coverage, and source safety; no live calls."""
import copy
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


def response(value):
    return {"status": "completed", "model": "gpt-6-luna", "output": [
        {"type": "reasoning", "summary": []},
        {"type": "message", "content": [{"type": "output_text", "text": json.dumps(value)}]},
    ]}


@patch.dict(os.environ, {"OPENAI_API_KEY": "fake-openai"})
class OpenAIIntegrationTests(unittest.TestCase):
    def test_greeting_stays_whole_across_old_duration_and_word_limits(self):
        texts = ("السلام عليكم ورحمة الله وبركاته").split()
        words = [{"type": "word", "text": text, "start": 5 + i * 1.8, "end": 6 + i * 1.8} for i, text in enumerate(texts)]
        segments = server.words_to_segments(words)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["ar"], " ".join(texts))
        self.assertEqual(segments[0]["end"], 13.2)
        wordy = [{"type": "word", "text": "كلمة", "start": i * .2, "end": i * .2 + .1} for i in range(30)]
        self.assertEqual(len(server.words_to_segments(wordy)), 1)

    def test_real_sentence_end_and_long_silence_remain_boundaries(self):
        words = [{"type": "word", "text": "أهلاً.", "start": 0, "end": .5},
                 {"type": "word", "text": "مرحباً", "start": .6, "end": 1},
                 {"type": "word", "text": "جديد", "start": 4, "end": 4.5}]
        self.assertEqual(len(server.words_to_segments(words)), 3)

    @patch.object(server, "post_json")
    def test_responses_schema_and_translation_use_original_timing(self, post):
        words = [{"type": "word", "text": text, "start": 5 + i * .3, "end": 5.2 + i * .3}
                 for i, text in enumerate("السلام عليكم ورحمة الله وبركاته".split())]
        segments = server.words_to_segments(words)
        post.return_value = response({"items": [{"id": segments[0]["id"], "terms": [], "parts": [
            {"first_word": 0, "last_word": 4, "translation": "Peace be upon you, and Allah's mercy and blessings.",
             "kind": "speech", "surah": None, "ayah": None, "hadith_query": None}]}]})
        server.translate_segments(segments)
        self.assertEqual((segments[0]["start"], segments[0]["end"]), (5, 6.4))
        url, payload, headers = post.call_args.args
        self.assertEqual(url, "https://api.openai.com/v1/responses")
        self.assertEqual(payload["model"], "gpt-6-luna")
        self.assertEqual(headers, {"Authorization": "Bearer fake-openai"})
        self.assertFalse(payload["store"])
        self.assertTrue(payload["text"]["format"]["strict"])
        part = payload["text"]["format"]["schema"]["properties"]["items"]["items"]["properties"]["parts"]["items"]
        self.assertFalse(part["additionalProperties"])
        self.assertEqual(set(part["required"]), set(part["properties"]))
        self.assertIn({"type": "null"}, part["properties"]["surah"]["anyOf"])

    @patch.object(server, "post_json")
    def test_incomplete_and_refused_output_never_checkpoint_translation(self, post):
        segments = server.words_to_segments([{"type": "word", "text": "مرحبا", "start": 0, "end": 1}])
        before = copy.deepcopy(segments)
        cases = [{"status": "incomplete", "output": []},
                 {"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal"}]}]},
                 {"status": "completed", "output": []}]
        for data in cases:
            with self.subTest(data=data):
                post.return_value = data
                with self.assertRaises(RuntimeError):
                    server.translate_segments(segments)
                self.assertEqual(segments, before)

    @patch.object(server, "post_json")
    def test_partial_quote_only_selects_verbatim_reference(self, post):
        source = {"arabic": "إن الله يحب التوابين ويحب المتطهرين", "translation": "Allah loves those who repent and those who purify themselves.", "partial": True}
        post.return_value = response({"translation_excerpt": "those who purify themselves.", "confident": True})
        selected = server.prepare_quote_subtitles("ويحب المتطهرين", source)
        self.assertEqual(selected["alignment_status"], "matched")
        post.return_value = response({"translation_excerpt": "New invented scripture", "confident": True})
        self.assertEqual(server.prepare_quote_subtitles("ويحب المتطهرين", source)["alignment_status"], "needs_selection")

    @patch.object(server, "lookup_term", return_value={"arabic_term": "الوضوء", "definition": "تعريف", "url": "https://islamic-content.com/dictionary/test"})
    @patch.object(server, "post_json")
    def test_terminology_review_uses_openai(self, post, lookup):
        segments = [{"id": "s", "ar": "الوضوء عبادة", "translation": "Washing is worship", "detected_terms": ["الوضوء"]}]
        post.return_value = response({"items": [{"id": "s", "translation": "Ablution is worship."}]})
        server.ground_terminology(segments, "fake-openai")
        self.assertEqual(segments[0]["translation"], "Ablution is worship.")
        self.assertEqual(post.call_args.args[0], "https://api.openai.com/v1/responses")


if __name__ == "__main__":
    unittest.main()
