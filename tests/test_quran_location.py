import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class QuranLocationTests(unittest.TestCase):
    def test_translation_html_and_footnotes_stay_out_of_subtitles(self):
        raw = '(96) Indeed, those who have believed - the Most Merciful will appoint affection.[829]<br /><div class="foot-notes">[829]- From Himself and from among each other.</div>'
        text, notes = server.quran_translation_content(raw, 96)
        self.assertEqual(text, "Indeed, those who have believed - the Most Merciful will appoint affection.")
        self.assertEqual(notes, "[829]- From Himself and from among each other.")
        self.assertEqual(server.quran_translation_content("A plain source translation.", 1), ("A plain source translation.", ""))

    @patch.object(server, "lookup_tafsir", return_value={})
    @patch.object(server, "get_json")
    def test_missing_verse_uses_unique_source_match(self, get_json, tafsir):
        text = "إن الذين آمنوا وعملوا الصالحات سيجعل لهم الرحمن ودا"
        get_json.side_effect = [[{"number": 96, "text": text}, {"number": 97, "text": "كلام آخر"}],
                               {"text": text}, {"translation_text": "Sourced verse translation."}]
        seg = {"ar": text, "en": "Draft", "type": "speech", "candidate": {"kind": "quran", "surah": 19, "ayah": None}}
        self.assertTrue(server.verify_quran(seg))
        self.assertEqual(seg["source"]["ayah"], 96)
        self.assertEqual(seg["en"], "Sourced verse translation.")
        self.assertFalse(seg["reviewed"])
        self.assertTrue(seg["needs_review"])

    @patch.object(server, "get_json")
    def test_repeated_excerpt_does_not_guess_location(self, get_json):
        text = "إن الذين آمنوا وعملوا الصالحات"
        get_json.return_value = [{"number": 1, "text": text + " كلام أول"}, {"number": 2, "text": text + " كلام ثان"}]
        seg = {"ar": text, "en": "Draft", "candidate": {"surah": 19, "ayah": None}}
        self.assertFalse(server.verify_quran(seg))
        self.assertEqual(get_json.call_count, 1)
        self.assertEqual(seg["en"], "Draft")

    @patch.object(server, "get_json")
    def test_explicit_wrong_location_is_not_replaced(self, get_json):
        get_json.return_value = {"text": "قل هو الله أحد"}
        seg = {"ar": "نص مختلف", "candidate": {"surah": 19, "ayah": 1}}
        self.assertFalse(server.verify_quran(seg))
        self.assertTrue(get_json.call_args.args[0].endswith("/19/1"))
        self.assertEqual(get_json.call_count, 1)

    @patch.object(server, "get_json")
    def test_missing_surah_stays_unresolved(self, get_json):
        self.assertFalse(server.verify_quran({"ar": "نص", "candidate": {"surah": None, "ayah": None}}))
        get_json.assert_not_called()
