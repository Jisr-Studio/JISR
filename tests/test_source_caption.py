"""Editable video attribution leaves the canonical citation untouched."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class SourceCaptionTests(unittest.TestCase):
    def setUp(self):
        self.segment = {"start": 0, "end": 4, "type": "quran", "ar": "تفريغ", "en": "Translation",
                        "needs_review": False, "reviewed": True,
                        "source": {"kind": "quran", "title": "الكهف، الآية 30", "arabic": "نص المصدر",
                                   "english": "Translation", "url": "https://quranpedia.net/ar/surah/18/30"}}

    def test_custom_default_and_hidden_caption_in_video_and_srt(self):
        source = copy.deepcopy(self.segment["source"])
        for caption in (None, "Al-Kahf 18:30", ""):
            with self.subTest(caption=caption):
                segment = copy.deepcopy(self.segment)
                if caption is not None:
                    segment["source_caption"] = caption
                expected = source["title"] if caption is None else caption
                ass = server.make_ass([segment], {})
                srt = server.make_srt([segment])
                if expected:
                    self.assertIn(expected, ass)
                    self.assertIn(expected, srt)
                else:
                    self.assertNotIn(source["title"], ass)
                    self.assertNotIn(source["title"], srt)
                self.assertEqual(server.make_sources([segment])[0]["url"], source["url"])
                self.assertEqual(segment["source"], source)
                self.assertIn(source["arabic"], ass)
                self.assertIn("Translation", srt)

    def test_ass_control_text_is_escaped(self):
        self.segment["source_caption"] = r"Custom {\pos(0,0)} caption"
        ass = server.make_ass([self.segment], {})
        self.assertNotIn(r"{\pos(0,0)}", ass)
        self.assertIn("Custom (/pos(0,0)) caption", ass)

    def test_private_draft_keeps_caption_but_orphaned_source_does_not(self):
        self.segment["needs_review"] = True
        self.assertIn(self.segment["source"]["title"], server.make_ass([self.segment], {}))
        self.assertIn(self.segment["source"]["title"], server.make_srt([self.segment]))
        self.segment.update(source=None, source_caption="Stale caption")
        self.assertEqual(server.source_caption(self.segment), "")

    @patch.object(server, "prepare_quote_subtitles", side_effect=lambda ar, source: source)
    def test_replacing_reference_resets_custom_caption(self, prepare):
        self.segment["source_caption"] = "Old source label"
        server.attach_source(self.segment, "quran", self.segment["source"])
        self.assertNotIn("source_caption", self.segment)


if __name__ == "__main__":
    unittest.main()
