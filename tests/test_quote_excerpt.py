"""Partial scripture subtitles use source excerpts, never the whole record."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

SPOKEN = "الطهور شطر الإيمان"
AR = "عن أبي مالك قال: الطُّهُورُ شَطْرُ الإِيمَانِ، والحمد لله تملأ الميزان"
EN = 'The Prophet said: "Purity is half of faith, and praise fills the Scale."'
EXCERPT = "Purity is half of faith,"
SOURCE = {"kind": "hadith", "arabic": AR, "translation": EN, "partial": True, "translation_status": "sourced"}


def alignment(excerpt=EXCERPT, confident=True):
    return {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps({"translation_excerpt": excerpt, "confident": confident})}]}]}


class QuoteExcerptTests(unittest.TestCase):
    @patch.dict("os.environ", {"OPENAI_API_KEY": ""})
    @patch.object(server, "lookup_tafsir", return_value={})
    @patch.object(server, "get_json", side_effect=[
        {"text": "ويسألونك عن المحيض قل هو أذى إن الله يحب التوابين ويحب المتطهرين"},
        {"translation_text": "Full verse prefix. Indeed, Allah loves those who repent and purify themselves."},
    ])
    def test_quran_lookup_does_not_replace_partial_draft_with_full_translation(self, get_json, tafsir):
        segment = {"ar": "إن الله يحب التوابين ويحب المتطهرين", "translation": "Partial draft",
                   "candidate": {"surah": 2, "ayah": 222}}
        self.assertTrue(server.verify_quran(segment))
        self.assertEqual(segment["translation"], "Partial draft")
        self.assertEqual(segment["source"]["alignment_status"], "needs_selection")
        self.assertIn("Full verse prefix.", segment["source"]["translation"])
        self.assertTrue(segment["needs_review"])

    def test_canonical_arabic_excerpt_comes_from_source_not_transcript(self):
        excerpt = server.canonical_arabic_excerpt(SPOKEN, AR)
        self.assertIn("الطُّهُورُ", excerpt)
        self.assertIn(excerpt, AR)
        self.assertNotIn("الحمد", excerpt)
        with self.assertRaises(ValueError):
            server.canonical_arabic_excerpt("كلام غير متعلق تماما", AR)

    @patch.dict("os.environ", {"OPENAI_API_KEY": ""})
    def test_without_key_partial_quote_keeps_draft_and_blocks_export(self):
        segment = {"ar": SPOKEN, "translation": "Machine draft", "start": 0, "end": 4}
        server.attach_source(segment, "hadith", SOURCE)
        self.assertEqual(segment["translation"], "Machine draft")
        self.assertEqual(segment["source"]["translation"], EN)
        self.assertEqual(segment["source"]["alignment_status"], "needs_selection")
        segment.update(reviewed=True, needs_review=False)
        self.assertFalse(server.publishable({"status": "ready", "segments": json.dumps([segment])}))

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "post_json", return_value=alignment())
    def test_model_only_selects_verbatim_source_translation(self, post_json):
        segment = {"ar": SPOKEN, "translation": "Machine draft", "start": 0, "end": 4}
        server.attach_source(segment, "hadith", SOURCE)
        self.assertEqual(segment["translation"], EXCERPT)
        self.assertEqual(segment["source"]["translation"], EN)
        self.assertEqual(segment["source"]["alignment_status"], "matched")
        self.assertTrue(segment["needs_review"])
        span = segment["source"]["translation_span"]
        self.assertEqual(EN[span["start"]:span["end"]], EXCERPT)
        segment.update(reviewed=True, needs_review=False)
        subtitles = server.make_srt([segment])
        self.assertIn(EXCERPT, subtitles)
        self.assertNotIn("praise fills", subtitles)
        self.assertNotIn("أبي مالك", subtitles)
        self.assertNotIn("praise fills", server.make_ass([segment], {"bilingual": True}))

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generated_full_or_uncertain_translation_is_not_accepted(self):
        responses = [alignment("Purification is half the faith."), alignment(EN), alignment(EXCERPT, False)]
        for response in responses:
            with self.subTest(response=response), patch.object(server, "post_json", return_value=response):
                source = server.prepare_quote_subtitles(SPOKEN, SOURCE)
                self.assertEqual(source["alignment_status"], "needs_selection")
                self.assertNotIn("subtitle_translation", source)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "post_json", side_effect=OSError("unavailable"))
    def test_alignment_outage_does_not_substitute_full_translation(self, post_json):
        self.assertEqual(server.prepare_quote_subtitles(SPOKEN, SOURCE)["alignment_status"], "needs_selection")

    def test_human_selection_preserves_reference_and_is_publishable_after_review(self):
        start = EN.index(EXCERPT)
        source = server.select_source_translation(SOURCE, SPOKEN, {"start": start, "end": start + len(EXCERPT)})
        segment = {"ar": SPOKEN, "translation": "Draft", "start": 0, "end": 4}
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}):
            server.attach_source(segment, "hadith", source)
        self.assertEqual(segment["translation"], EXCERPT)
        self.assertEqual(segment["source"]["alignment_status"], "selected")
        segment.update(reviewed=True, needs_review=False)
        self.assertTrue(server.publishable({"status": "ready", "segments": json.dumps([segment])}))

    def test_invalid_or_full_source_selection_is_rejected(self):
        for span in ({"start": True, "end": 5}, {"start": -1, "end": 2}, {"start": 3, "end": 2}, {"start": 0, "end": len(EN)+1}, {"start": 0, "end": len(EN)}):
            with self.subTest(span=span), self.assertRaises(ValueError):
                server.select_source_translation(SOURCE, SPOKEN, span)


if __name__ == "__main__":
    unittest.main()
