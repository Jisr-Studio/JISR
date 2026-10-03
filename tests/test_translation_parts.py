"""Keep timed speech intact while separating scriptural quotations."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


def model_response(items):
    items = [{"terms": [], **item} for item in items]
    return {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps({"items": items})}]}]}


class TranslationPartsTests(unittest.TestCase):
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "post_json")
    def test_invalid_word_ranges_are_corrected_once_before_any_checkpoint(self, post_json):
        segments = self.transcript()
        original_ar = segments[0]["ar"]
        segment_id = segments[0]["id"]
        bad = model_response([{"id": segment_id, "parts": [{"first_word": 0, "last_word": 15, "kind": "speech", "english": "Bad coverage"}]}])
        good = model_response([{"id": segment_id, "parts": [
            {"first_word": 0, "last_word": 1, "kind": "speech", "english": "Always remember"},
            {"first_word": 2, "last_word": 7, "kind": "quran", "english": "Verse draft", "surah": 2, "ayah": 222},
            {"first_word": 8, "last_word": 14, "kind": "speech", "english": "Remaining speech draft"},
        ]}])
        bad["model"] = server.OPENAI_MODEL
        post_json.side_effect = [bad, good]
        snapshots = []
        server.translate_segments(segments, checkpoint=lambda items: snapshots.append(copy.deepcopy(items)))
        self.assertEqual(post_json.call_count, 2)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(" ".join(s["ar"] for s in segments), original_ar)
        self.assertEqual(segments[1]["candidate"]["kind"], "quran")
        self.assertAlmostEqual(segments[1]["start"], .6)
        repair_payload = post_json.call_args.args[1]
        self.assertEqual(repair_payload["model"], server.OPENAI_MODEL)
        prompt = repair_payload["input"]
        self.assertIn("Indices restart at zero", prompt)
        inputs = json.loads(prompt.rsplit("Input: ", 1)[1])
        self.assertEqual(inputs[0]["word_count"], 15)
        self.assertEqual(inputs[0]["last_word_index"], 14)

    def transcript(self):
        text = "تذكر دائما إن الله يحب التوابين ويحب المتطهرين وقول النبي الطهور شطر الإيمان في حياتنا"
        return server.words_to_segments([{"type": "word", "text": token, "start": i * .3, "end": i * .3 + .25,
                                         "logprob": -2 if i == 0 else -.1} for i, token in enumerate(text.split())])

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "post_json")
    def test_mixed_speech_quran_hadith_preserve_all_words_and_timing(self, post_json):
        segments = self.transcript()
        original_id, original_ar = segments[0]["id"], segments[0]["ar"]
        parts = [
            {"first_word": 0, "last_word": 1, "english": "Always remember", "kind": "speech"},
            {"first_word": 2, "last_word": 7, "english": "Verse draft", "kind": "quran", "surah": 2, "ayah": 222},
            {"first_word": 8, "last_word": 9, "english": "and the Prophet's saying", "kind": "speech"},
            {"first_word": 10, "last_word": 12, "english": "Hadith draft", "kind": "hadith", "hadith_query": "الطهور شطر الإيمان"},
            {"first_word": 13, "last_word": 14, "english": "in our lives", "kind": "speech"},
        ]
        post_json.return_value = model_response([{"id": original_id, "parts": parts}])
        server.translate_segments(segments)
        self.assertEqual(len(segments), 5)
        self.assertEqual(len({s["id"] for s in segments}), 5)
        self.assertEqual(segments[0]["id"], original_id)
        self.assertEqual(" ".join(s["ar"] for s in segments), original_ar)
        self.assertAlmostEqual(segments[1]["start"], .6)
        self.assertAlmostEqual(segments[1]["end"], 2.35)
        self.assertAlmostEqual(segments[3]["start"], 3.0)
        self.assertAlmostEqual(segments[3]["end"], 3.85)
        self.assertTrue(segments[0]["needs_review"])
        self.assertFalse(segments[1]["needs_review"])
        with patch.object(server, "lookup_tafsir", return_value={}), patch.object(server, "get_json", side_effect=[{"text": "إن الله يحب التوابين ويحب المتطهرين"},
                                                           {"translation_text": "Reference verse translation"}, {}]):
            self.assertTrue(server.verify_quran(segments[1]))
        server.attach_source(segments[3], "hadith", {"arabic": "الطهور شطر الإيمان", "english": "Reference hadith translation"})
        self.assertEqual([segments[i]["en"] for i in (0, 2, 4)], ["Always remember", "and the Prophet's saying", "in our lives"])
        self.assertEqual(segments[1]["en"], "Reference verse translation")
        self.assertEqual(segments[3]["en"], "Reference hadith translation")
        self.assertTrue(segments[1]["needs_review"] and segments[3]["needs_review"])
        prompt = post_json.call_args.args[1]["input"]
        sent = json.loads(prompt.split("Input: ", 1)[1])
        self.assertEqual(sent[0]["words"][2], {"index": 2, "text": "إن"})
        self.assertNotIn("start", sent[0]["words"][2])
        self.assertIn(server.TERMINOLOGY_GUIDE, prompt)
        for seg in segments:
            seg.update(reviewed=True, needs_review=False)
        subtitles = server.make_srt(segments)
        for line in ("Always remember", "and the Prophet's saying", "in our lives", "Reference verse translation", "Reference hadith translation"):
            self.assertIn(line, subtitles)
        self.assertIn("00:00:00,600 --> 00:00:02,350", subtitles)
        self.assertEqual(len(server.make_sources(segments)), 2)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "post_json")
    def test_invalid_partition_does_not_commit_any_batch_changes(self, post_json):
        invalid = [(0, 13), (1, 14), (0, 15), (False, 14)]
        for first, last in invalid:
            with self.subTest(first=first, last=last):
                segments = self.transcript()
                second = copy.deepcopy(segments[0])
                second["id"] = "second"
                segments.append(second)
                before = copy.deepcopy(segments)
                good = {"first_word": 0, "last_word": 14, "english": "Full draft", "kind": "speech"}
                bad = {**good, "first_word": first, "last_word": last}
                post_json.return_value = model_response([{"id": segments[0]["id"], "parts": [good]}, {"id": second["id"], "parts": [bad]}])
                with self.assertRaises(RuntimeError):
                    server.translate_segments(segments)
                self.assertEqual(segments, before)

    def test_overlap_and_unknown_output_ids_are_rejected(self):
        segment = self.transcript()[0]
        part = {"first_word": 0, "last_word": 7, "english": "Draft", "kind": "speech"}
        with self.assertRaises(RuntimeError):
            server.translation_parts(segment, {"parts": [part, {**part, "first_word": 7, "last_word": 14}]})
        for ids in (["unknown"], [segment["id"], segment["id"]], []):
            with self.subTest(ids=ids), patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}), patch.object(server, "post_json", return_value=model_response([{"id": ident, "parts": [{**part, "last_word": 14}]} for ident in ids])):
                with self.assertRaises(RuntimeError):
                    server.translate_segments([copy.deepcopy(segment)])

    def test_quotation_match_rejects_surrounding_speech(self):
        quote = "إن الله يحب التوابين ويحب المتطهرين"
        self.assertTrue(server.quotation_matches(quote, quote))
        self.assertTrue(server.quotation_matches("يحب التوابين ويحب المتطهرين", quote))
        self.assertFalse(server.quotation_matches("تذكر دائما " + quote + " في حياتنا", quote))


if __name__ == "__main__":
    unittest.main()
