"""A related Hadith's selected reference wording must not reuse ASR text."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

SPOKEN = "ومن أتاني يمشي أتيت له هرولة."
ARABIC = "وَإِنْ أَتَانِي يَمْشِي أَتَيْتُهُ هَرْوَلَةً."
ENGLISH = "If he comes to Me walking, I come to him jogging."
FULL_ENGLISH = "The preceding clause. " + ENGLISH

def fixture():
    return {"id": "a" * 12, "start": 20.6, "end": 24.16, "type": "hadith", "ar": SPOKEN,
            "translation": "A machine draft with recognition errors.", "translation_origin": "machine", "reviewed": True,
            "source": {"kind": "hadith", "arabic": "نص سابق " + ARABIC, "translation": FULL_ENGLISH,
                       "partial": True, "quotation_mode": "paraphrase", "relation_method": "editor_selected",
                       "translation_status": "sourced", "alignment_status": "paraphrase", "subtitle_arabic": SPOKEN,
                       "subtitle_translation": "A machine draft with recognition errors.", "url": "https://hadeethenc.com/ar/browse/hadith/3636"}}

def select(segment):
    start = FULL_ENGLISH.index(ENGLISH)
    source = server.select_source_translation(segment["source"], segment["ar"], {"start": start, "end": start + len(ENGLISH)})
    segment.update(source=source, translation=source["subtitle_translation"], translation_origin="source")
    return segment

class SourceWordingTests(unittest.TestCase):
    @patch.object(server, "translation_request", side_effect=AssertionError("Editor mode must not call AI"))
    def test_explicit_source_mode_corrects_arabic_without_overwriting_transcript(self, request):
        segment = fixture()
        self.assertTrue(server.set_hadith_source_wording(segment, True))
        self.assertEqual(segment["ar"], SPOKEN)
        self.assertEqual((segment["start"], segment["end"]), (20.6, 24.16))
        self.assertEqual(server.subtitle_arabic(segment), ARABIC)
        self.assertEqual(segment["source"]["quotation_mode"], "paraphrase")
        self.assertFalse(segment["reviewed"])
        self.assertFalse(server.quote_alignment_ready(segment["source"]))
        request.assert_not_called()

    def test_selected_translation_and_exports_use_only_source_excerpts(self):
        segment = fixture()
        server.set_hadith_source_wording(segment, True)
        select(segment)
        self.assertTrue(server.quote_alignment_ready(segment["source"]))
        for output in (server.make_srt([segment]), server.make_ass([segment], {})):
            self.assertIn(ARABIC, output)
            self.assertIn(ENGLISH, output)
            self.assertIn("[Source wording]", output)
            self.assertNotIn(SPOKEN, output)
            self.assertNotIn("A machine draft", output)
        self.assertIn("Source wording · Related narration", server.source_caption(segment))
        self.assertNotIn("machine draft", server.source_caption(segment))

    def test_unselected_translation_cannot_be_confirmed_as_source(self):
        segment = fixture()
        server.set_hadith_source_wording(segment, True)
        segment.update(reviewed=True, needs_review=False)
        self.assertTrue(server.segment_review_pending(segment))
        self.assertIn("Machine draft · Review required", server.source_caption(segment))
        select(segment)
        segment.update(reviewed=True, needs_review=False)
        self.assertFalse(server.segment_review_pending(segment))
        segment["source"]["subtitle_translation"] = "Invented translation"
        self.assertTrue(server.segment_review_pending(segment))

    def test_disabling_restores_speech_translation_and_review_state(self):
        segment = fixture()
        original = copy.deepcopy(segment)
        server.set_hadith_source_wording(segment, True)
        select(segment)
        self.assertTrue(server.set_hadith_source_wording(segment, False))
        self.assertEqual(segment["ar"], original["ar"])
        self.assertEqual(segment["translation"], original["translation"])
        self.assertEqual(segment["translation_origin"], "machine")
        self.assertEqual(server.subtitle_arabic(segment), SPOKEN)
        self.assertFalse(segment["reviewed"])
        self.assertNotIn("subtitle_mode", segment["source"])

    def test_default_paraphrase_still_preserves_speaker(self):
        segment = fixture()
        self.assertFalse(server.set_hadith_source_wording(segment, False))
        self.assertEqual(server.subtitle_arabic(segment), SPOKEN)
        with self.assertRaises(ValueError):
            server.select_source_translation(segment["source"], SPOKEN, {"start": 0, "end": 10})

    def test_partial_source_wording_drops_unmatched_closing_quote(self):
        segment = fixture()
        segment["source"]["arabic"] = "نص سابق " + ARABIC.rstrip('.') + '».'
        server.set_hadith_source_wording(segment, True)
        select(segment)
        self.assertEqual(server.subtitle_arabic(segment), ARABIC.rstrip('.'))
        self.assertIn(server.subtitle_arabic(segment), segment["source"]["arabic"])

    def test_invalid_source_mode_requests_fail_without_mutation(self):
        for enabled, changes in (("true", {}), (True, {"translation_status": "machine_draft"}),
                                 (True, {"arabic": "كلام مختلف تماما لا يطابق العبارة"}),
                                 (True, {"quotation_mode": "quotation"})):
            with self.subTest(enabled=enabled, changes=changes):
                segment = fixture()
                segment["source"].update(changes)
                before = copy.deepcopy(segment)
                with self.assertRaises(ValueError):
                    server.set_hadith_source_wording(segment, enabled)
                self.assertEqual(segment, before)

if __name__ == "__main__":
    unittest.main()
