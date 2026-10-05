import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


VERSE = "إن الله وملائكته يصلون على النبي يا أيها الذين آمنوا صلوا عليه وسلموا تسليما"
ENGLISH = "Full sourced English translation."


def cue(text, start, ident, source=False):
    words = [{"text": w, "start": start + i * .3, "end": start + i * .3 + .2}
             for i, w in enumerate(text.split())]
    result = {"id": ident, "ar": text, "en": "Original translation", "type": "speech",
              "start": words[0]["start"], "end": words[-1]["end"], "words": words,
              "reviewed": False, "needs_review": True, "unclear_words": []}
    if source:
        result.update(type="quran", source={"kind": "quran", "surah": 33, "ayah": 56,
                      "arabic": VERSE, "english": ENGLISH, "partial": True,
                      "title": "Quran 33:56", "url": "https://example.test/33/56"})
    return result


def fixture():
    return [cue("عباد الله إن الله وملائكته يصلون على النبي.", .34, "intro"),
            cue("يا أيها الذين آمنوا صلوا عليه وسلموا تسليما.", 3.86, "quote", True),
            cue("فاللهم صل وسلم وبارك على عبدك ورسولك الأمين", 7.5, "outro")]


def translate_residual(segments):
    for seg in segments:
        if not seg.get("en"):
            seg["en"] = "Servants of God."
    return segments


class QuranBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.network = patch.object(server, "get_json", side_effect=AssertionError("Unexpected source request")).start()
        self.translation = patch.object(server, "translate_segments", side_effect=translate_residual).start()
        self.addCleanup(patch.stopall)

    def test_intro_is_separated_and_spoken_verse_reunited(self):
        segments = fixture()
        originals = copy.deepcopy(segments)
        self.assertTrue(server.repair_quran_boundaries(segments))
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0]["ar"], "عباد الله")
        quote = segments[1]
        self.assertEqual(server.normalize_ar(quote["ar"]), server.normalize_ar(VERSE))
        self.assertEqual(quote["en"], ENGLISH)
        self.assertFalse(quote["source"]["partial"])
        self.assertFalse(quote["reviewed"])
        self.assertTrue(quote["needs_review"])
        self.assertEqual(quote["start"], originals[0]["words"][2]["start"])
        self.assertEqual(quote["end"], originals[1]["end"])
        self.assertEqual(segments[2], originals[2])
        self.assertEqual([w for s in segments for w in s["words"]], [w for s in originals for w in s["words"]])
        self.assertEqual(len({s["id"] for s in segments}), len(segments))
        self.assertIn(VERSE + "\n" + ENGLISH, server.make_srt(segments))

    def test_repair_is_idempotent(self):
        segments = fixture()
        server.repair_quran_boundaries(segments)
        original = copy.deepcopy(segments)
        self.assertFalse(server.repair_quran_boundaries(segments))
        self.assertEqual(segments, original)

    def test_protects_reviewed_edited_and_other_citation_neighbors(self):
        for change in ({"reviewed": True}, {"source_caption": ""}, {"ar": "تعديل المستخدم"},
                       {"type": "hadith"}, {"candidate": {"kind": "hadith"}},
                       {"candidate": {"kind": "quran", "surah": 2, "ayah": 1}}, {"words": []}):
            with self.subTest(change=change):
                segments = fixture()
                segments[0].update(change)
                original = copy.deepcopy(segments)
                with patch.object(server, "get_json", return_value={"text": "الم"}):
                    self.assertFalse(server.repair_quran_boundaries(segments))
                self.assertEqual(segments, original)

    def test_silence_prevents_join(self):
        segments = fixture()[:2]
        segments[1]["start"] = segments[0]["end"] + 3
        self.assertFalse(server.repair_quran_boundaries(segments))

    def test_partial_recitation_is_never_completed(self):
        segments = [fixture()[1]]
        original = copy.deepcopy(segments)
        self.assertFalse(server.repair_quran_boundaries(segments))
        self.assertEqual(segments, original)

    def test_intervening_speech_is_not_absorbed(self):
        segments = fixture()
        segments.insert(1, cue("وهذه آية عظيمة", 2.95, "comment"))
        # Refuse partial source alignment in this test: no speculative English.
        with patch.object(server, "translation_key", return_value=""):
            self.assertFalse(server.repair_quran_boundaries(segments))
        self.assertEqual(segments[1]["ar"], "وهذه آية عظيمة")

    def test_translation_failure_does_not_mutate_original(self):
        segments = fixture()
        original = copy.deepcopy(segments)
        self.translation.side_effect = RuntimeError("Provider unavailable")
        with self.assertRaises(RuntimeError):
            server.repair_quran_boundaries(segments)
        self.assertEqual(segments, original)

    def test_source_outage_keeps_unresolved_transcript(self):
        segments = fixture()
        segments[1].pop("source")
        segments[1].update(type="speech", candidate={"kind": "quran", "surah": 33, "ayah": 56})
        self.network.side_effect = OSError("Unavailable")
        original = copy.deepcopy(segments)
        self.assertFalse(server.repair_quran_boundaries(segments))
        self.assertEqual(segments, original)

    def test_two_clean_halves_join_without_machine_translation(self):
        segments = fixture()[:2]
        segments[0]["words"] = segments[0]["words"][2:]
        segments[0]["ar"] = " ".join(w["text"] for w in segments[0]["words"])
        segments[0]["start"] = segments[0]["words"][0]["start"]
        self.assertTrue(server.repair_quran_boundaries(segments))
        self.assertEqual(len(segments), 1)
        self.translation.assert_not_called()

    def test_repeated_recitation_preserves_all_words(self):
        segments = fixture()[:2]
        segments.append(cue(VERSE, 6.5, "repeat", True))
        original_words = [w for s in segments for w in s["words"]]
        self.assertTrue(server.repair_quran_boundaries(segments))
        self.assertEqual([w for s in segments for w in s["words"]], original_words)
        self.assertEqual(segments[-1]["id"], "repeat")

    def test_new_candidate_can_recover_without_existing_source(self):
        segments = fixture()
        source = segments[1].pop("source")
        segments[1].update(type="speech", candidate={"kind": "quran", "surah": 33, "ayah": 56})
        source["partial"] = False
        with patch.object(server, "get_json", return_value={"text": VERSE}), patch.object(server, "lookup_quran", return_value=source):
            self.assertTrue(server.repair_quran_boundaries(segments))
        self.assertEqual(segments[1]["en"], ENGLISH)
        self.assertFalse(segments[1]["source"]["partial"])

    def test_pipeline_saves_recovered_source_boundaries(self):
        row = {"filename": "test.mp4", "duration": 30, "segments": json.dumps(fixture())}
        with patch.object(server, "project_row", return_value=row), patch.object(server, "save_project") as save, \
             patch.object(server, "resolve_segment_citation"), patch.object(server, "check_meaning"), patch.object(server, "PROCESS_SLOTS"):
            server.process_project("test")
        saved = save.call_args.kwargs
        self.assertEqual(saved["status"], "ready")
        segments = json.loads(saved["segments"])
        self.assertEqual(segments[0]["ar"], "عباد الله")
        self.assertFalse(segments[1]["source"]["partial"])


if __name__ == "__main__":
    unittest.main()
