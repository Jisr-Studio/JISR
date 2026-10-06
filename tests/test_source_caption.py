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
                        "source": {"kind": "quran", "surah": 18, "ayah": 30, "title": "الكهف، الآية 30", "arabic": "نص المصدر",
                                   "english": "Translation", "url": "https://quranpedia.net/ar/surah/18/30"}}

    def test_custom_default_and_hidden_caption_in_video_and_srt(self):
        source = copy.deepcopy(self.segment["source"])
        for caption in (None, "Al-Kahf 18:30", ""):
            with self.subTest(caption=caption):
                segment = copy.deepcopy(self.segment)
                if caption is not None:
                    segment["source_caption"] = caption
                expected = "Surah Al-Kahf (18:30) · Translation of Quranic meanings" if caption is None else caption
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

    def test_legacy_quran_link_gets_english_reference_without_mutating_source(self):
        del self.segment["source"]["surah"]
        del self.segment["source"]["ayah"]
        source = copy.deepcopy(self.segment["source"])
        self.assertEqual(server.source_caption(self.segment), "Surah Al-Kahf (18:30) · Translation of Quranic meanings")
        self.assertEqual(self.segment["source"], source)

    def test_hadith_caption_preserves_reference_and_does_not_guess_complex_grading(self):
        segment = {"type": "hadith", "source": {"attribution": "صحيح مسلم ٢٢٣", "grade": "صحيح", "translation_status": "sourced"}}
        self.assertEqual(server.source_caption(segment), "Sahih Muslim 223 · Sahih (authentic)")
        segment["source"].update(attribution="مرجع طويل", grade="لم يذكر حكمًا", url="https://dorar.net/h/test123", translation_status="machine_draft")
        self.assertEqual(server.source_caption(segment), "Dorar · Hadith test123 · See source for grading · English: machine draft")

    def test_shared_labels_keep_preview_and_export_attributions_equal(self):
        import shutil
        import subprocess
        node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")
        if not Path(node).is_file():
            self.skipTest("Node is unavailable for the shared caption parity check")
        fixtures = [self.segment, {"type": "hadith", "source": {"attribution": "صحيح مسلم ٢٢٣", "grade": "صحيح", "translation_status": "sourced"}},
                    {"type": "hadith", "source": {"quotation_mode": "paraphrase", "url": "https://hadeethenc.com/ar/browse/hadith/6461"}}]
        import json
        script = "const c=require('./dist/js/citation-text.js');c.configureCaptionLabels(require('./dist/source-caption-labels.json'));console.log(JSON.stringify(JSON.parse(process.argv[1]).map(s=>c.sourceCaption(s))));"
        result = subprocess.run([node, "-e", script, json.dumps(fixtures)], cwd=server.ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
        self.assertEqual(json.loads(result.stdout), [server.source_caption(s) for s in fixtures])

    def test_private_draft_keeps_caption_but_orphaned_source_does_not(self):
        self.segment["needs_review"] = True
        self.assertIn("Surah Al-Kahf (18:30)", server.make_ass([self.segment], {}))
        self.assertIn("Surah Al-Kahf (18:30)", server.make_srt([self.segment]))
        self.segment.update(source=None, source_caption="Stale caption")
        self.assertEqual(server.source_caption(self.segment), "")

    @patch.object(server, "prepare_quote_subtitles", side_effect=lambda ar, source: source)
    def test_replacing_reference_resets_custom_caption(self, prepare):
        self.segment["source_caption"] = "Old source label"
        server.attach_source(self.segment, "quran", self.segment["source"])
        self.assertNotIn("source_caption", self.segment)


if __name__ == "__main__":
    unittest.main()
