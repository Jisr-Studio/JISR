"""Regression cases from the six-video audit. No external calls."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
import pipeline_quality as quality


def cue(id="one", ar="ولا تنسى أن", en="And do not forget the whole following hadith", **changes):
    return {"id": id, "ar": ar, "en": en, "start": 1, "end": 1.6,
            "type": "speech", "reviewed": False, "needs_review": False, **changes}


def response(items):
    return {"status": "completed", "text": json.dumps({"quality_items": items})}


class PipelineQualityTests(unittest.TestCase):
    def check(self, segments, request):
        quality.check_meaning(segments, request, "fake", server.normalize_ar)

    def test_introduction_does_not_keep_borrowed_hadith_or_candidate(self):
        segment = cue(candidate={"kind": "hadith"})
        original_ar = segment["ar"]
        request = Mock(return_value=response([{"id": "one", "english": "And do not forget that",
                            "confident": True, "issues": ["boundary", "duplicate"]}]))
        self.check([segment], request)
        self.assertEqual(segment["en"], "And do not forget that")
        self.assertEqual(segment["ar"], original_ar)
        self.assertEqual((segment["start"], segment["end"]), (1, 1.6))
        self.assertNotIn("candidate", segment)
        self.assertTrue(segment["needs_review"])
        self.assertFalse(segment["reviewed"])
        self.check([segment], request)
        request.assert_called_once()  # Saved check is reusable, not billed again.

    def test_bad_ids_do_not_commit_partial_corrections(self):
        segments = [cue(), cue(id="two")]
        request = Mock(return_value=response([{"id": "one", "english": "Changed", "confident": True, "issues": []},
                                             {"id": "invented", "english": "Changed", "confident": True, "issues": []}]))
        before = [s["en"] for s in segments]
        self.check(segments, request)
        self.assertEqual([s["en"] for s in segments], before)
        self.assertTrue(all(s["quality_review"]["status"] == "unavailable" for s in segments))

    def test_uncertain_attribution_is_flagged_not_reconstructed(self):
        segment = cue(ar="إن الله يقول عليه الصلاة والسلام", en="God says, blessings upon him")
        request = Mock(return_value=response([{"id": "one", "english": "The Prophet said", "confident": True,
                                             "issues": ["transcript"]}]))
        self.check([segment], request)
        self.assertEqual(segment["en"], "God says, blessings upon him")
        quality.annotate_readability([segment])
        self.assertIn("transcript", [i["code"] for i in segment["review_issues"]])

    def test_outage_preserves_draft_and_is_retryable(self):
        segment = cue()
        self.check([segment], Mock(side_effect=OSError("offline")))
        self.assertEqual(segment["quality_review"]["status"], "unavailable")
        self.assertNotIn("quality_input_hash", segment)
        self.assertIn("whole following", segment["en"])

    def test_protects_human_translations_reviewed_texts_and_sources(self):
        segments = [cue(reviewed=True), cue(translation_origin="human"), cue(source={"arabic": "source"}),
                    cue(candidate={"kind": "quran"})]
        before = copy.deepcopy(segments)
        request = Mock()
        self.check(segments, request)
        request.assert_not_called()
        self.assertEqual(segments, before)

    def test_fast_reading_warns_without_moving_timing_or_blocking_confirmation(self):
        segment = cue(en="a" * 90)
        quality.annotate_readability([segment])
        self.assertEqual(segment["readability"]["characters_per_second"], 150)
        self.assertEqual(segment["readability"]["issues"], ["reading_speed", "short_display"])
        self.assertEqual((segment["start"], segment["end"]), (1, 1.6))
        segment.update(reviewed=True, needs_review=False)
        quality.annotate_readability([segment])
        self.assertFalse(server.segment_review_pending(segment))

    def test_all_unreviewed_speech_is_pending_but_private_export_still_works(self):
        segment = cue()
        row = {"status": "ready", "segments": json.dumps([segment])}
        self.assertFalse(server.publishable(row))
        self.assertTrue(server.exportable(row))
        self.assertTrue(server.export_warnings(row))
        self.assertTrue(server.ready_for_retry(row))
        segment.update(reviewed=True, needs_review=False)
        row["segments"] = json.dumps([segment])
        self.assertFalse(server.ready_for_retry(row))
        segment.update(reviewed=False, translation_origin="human")
        row["segments"] = json.dumps([segment])
        self.assertFalse(server.ready_for_retry(row))
        segment.pop("translation_origin")
        segment["source_caption"] = "Custom"
        row["segments"] = json.dumps([segment])
        self.assertFalse(server.ready_for_retry(row))

    def test_shared_hadith_identity_preserves_each_display_range(self):
        first = "من تقرب إلي شبرا تقربت إليه ذراعا"
        last = "ومن أتاني يمشي أتيته هرولة"
        segments = [cue(ar=first, candidate={"kind": "hadith"}),
                    cue(id="two", ar=last, start=1.8, end=3, candidate={"kind": "hadith"})]
        full = first + " " + last
        def verify(combined):
            self.assertEqual(combined["ar"], full)
            combined["source"] = {"kind": "hadith", "arabic": full, "english": "Source English",
                                  "url": "https://hadeethenc.com/ar/browse/hadith/1", "translation_status": "sourced"}
            return True
        def attach(child, kind, source):
            child.update(type=kind, source=source)
        quality.coherent_hadith_groups(segments, verify, Mock(), attach, server.quotation_matches, server.quotation_is_partial)
        self.assertEqual(segments[0]["citation_group"], segments[1]["citation_group"])
        self.assertEqual(segments[0]["source"]["url"], segments[1]["source"]["url"])
        self.assertEqual([(s["start"], s["end"]) for s in segments], [(1, 1.6), (1.8, 3)])
        self.assertTrue(all(s["source"]["partial"] for s in segments))

    def test_group_does_not_replace_one_child_if_other_child_fails(self):
        segments = [cue(candidate={"kind": "hadith"}), cue(id="two", start=1.8, candidate={"kind": "hadith"})]
        before = copy.deepcopy(segments)
        def verify(combined):
            combined["source"] = {"arabic": "unrelated", "translation_status": "sourced"}
            return True
        attach = Mock()
        quality.coherent_hadith_groups(segments, verify, Mock(), attach, lambda a, b: False, server.quotation_is_partial)
        attach.assert_not_called()
        self.assertEqual(segments, before)

    def test_group_cannot_cross_human_review_or_large_gap(self):
        for barrier in (cue(reviewed=True, candidate={"kind": "hadith"}), cue(start=10, end=11, candidate={"kind": "hadith"})):
            verify = Mock()
            quality.coherent_hadith_groups([cue(candidate={"kind": "hadith"}), barrier], verify, Mock(), Mock(), Mock(), Mock())
            verify.assert_not_called()

    def test_group_choices_are_paraphrases_if_any_child_differs(self):
        source = "من تقرب إلي شبرا تقربت إليه ذراعا ومن أتاني يمشي أتيته هرولة"
        first = cue(ar="من تقرب إلي شبرا تقربت إليه ذراعا", citation_group="g",
                    citation_suggestions=[{"arabic": source, "quotation_mode": "quotation"}])
        other = cue(id="two", ar="كلام مختلف تماما عن هذه الرواية", citation_group="g")
        quality.classify_hadith_choices([first, other], server.quotation_matches)
        self.assertEqual(first["citation_suggestions"][0]["quotation_mode"], "paraphrase")

    def test_source_translation_choices_survive_a_retry_of_linked_hadith(self):
        segment = cue(type="hadith", source={"arabic": "source"}, citation_suggestions=[{"id": "1"}])
        server.resolve_segment_citation(segment)
        self.assertEqual(segment["citation_suggestions"], [{"id": "1"}])

    def test_quran_meanings_and_machine_hadith_are_labeled_in_exports(self):
        quran = cue(type="quran", source={"title": "سورة", "translator": "Saheeh International"})
        hadith = cue(type="hadith", source={"attribution": "مرجع", "translation_status": "machine_draft"})
        self.assertIn("Translation of Quranic meanings", server.make_srt([quran]))
        self.assertIn("Saheeh International", server.make_ass([quran], {}))
        self.assertIn("English: machine draft", server.make_srt([hadith]))
        quran["source_caption"] = ""
        self.assertEqual(server.source_caption(quran), "")

    def test_draft_inventory_includes_pending_source_without_publishing_it(self):
        segment = cue(type="hadith", source={"arabic": "source", "translation_status": "machine_draft"})
        self.assertEqual(server.make_sources([segment]), [])
        draft = server.make_draft_sources([segment])
        self.assertEqual(draft["status"], "draft")
        self.assertTrue(draft["citations"][0]["review_pending"])

    @patch.object(server, "lookup_hadith")
    @patch.object(server, "search_hadeethenc")
    def test_translation_search_uses_anchors_and_does_not_require_commentary(self, search, lookup):
        from test_hadith_translation import SPOKEN, REFERENCE, SOURCED, candidate
        search.side_effect = [[], [candidate()]]
        lookup.return_value = {**SOURCED, "explanation": ""}
        result = server.enrich_hadith_translation(SPOKEN, SPOKEN, REFERENCE)
        self.assertEqual(result["translation_lookup_status"], "matched")
        self.assertEqual(result["translation_status"], "sourced")

    @patch.object(server, "get_json")
    def test_explicit_comma_attribution_and_multiple_narrators_are_preserved(self, get):
        quote = "إن العبد ليتكلم بالكلمة لا يلقي لها بالا"
        get.side_effect = [{"id": "3608", "hadeeth": "عن أبي هريرة، عن النبي قال: " + quote +
                            "\nوعن أبي عبد الرحمن بلال رضي الله عنه : أن رسول الله قال: رواية أخرى",
                            "grade": "صحيحان", "attribution": "البخاري والترمذي"},
                           {"id": "3608", "hadeeth": "Both published reports."}]
        source = server.lookup_hadith("3608", quote)
        self.assertEqual(source["narrator"], "أبي هريرة؛ أبي عبد الرحمن بلال")

    def test_related_words_scattered_in_a_long_story_do_not_make_a_source(self):
        quote = "إن الله حيي كريم يستحي أن يرد يد عبده سفرا"
        story = " ثم ذهب إلى السوق " * 20
        scattered = story.join(["حيي", "كريم", "يستحي", "يرد", "عبده", "سفرا"])
        self.assertLess(server.hadith_related_score(quote, scattered), .65)


if __name__ == "__main__":
    unittest.main()
