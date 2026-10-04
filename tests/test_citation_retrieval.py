"""Reference retrieval must handle excerpts/ASR boundaries without hiding errors."""
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

CANONICAL = "من تقرب إلي شبرا تقربت إليه ذراعا ومن تقرب إلي ذراعا تقربت إليه باعا ومن أتاني يمشي أتيته هرولة"
SPOKEN = CANONICAL.replace("أتيته", "أتيت له")


def dorar_response(text):
    return {"ahadith": {"result": '<div>' + text + '</div><div class="hadith-info">الراوي : أبو هريرة | المحدث : مسلم | المصدر : صحيح مسلم | الصفحة أو الرقم : 1 | خلاصة حكم المحدث : صحيح</div>'}}


@patch.dict("os.environ", {"OPENAI_API_KEY": ""})
class CitationRetrievalTests(unittest.TestCase):
    def test_one_asr_word_boundary_error_matches_saved_case(self):
        self.assertGreater(server.similarity(SPOKEN, CANONICAL), .98)
        self.assertTrue(server.quotation_matches(SPOKEN, CANONICAL))
        self.assertEqual(server.canonical_arabic_excerpt(SPOKEN, CANONICAL), CANONICAL)
        self.assertFalse(server.quotation_is_partial(SPOKEN, CANONICAL))

    def test_surrounding_speech_is_not_absorbed_into_quotation(self):
        quote = "الطهور شطر الإيمان"
        self.assertFalse(server.quotation_matches("ولا تنسى أن " + quote, quote))
        self.assertFalse(server.quotation_matches("لكن " + quote, quote))
        self.assertFalse(server.quotation_matches("لا " + quote, quote))
        self.assertFalse(server.quotation_matches("كلام لا يتعلق بالحديث إطلاقا", CANONICAL))

    @patch.object(server, "resolve_dorar_reference", side_effect=lambda source, query: source)
    @patch.object(server, "enrich_hadith_translation", side_effect=lambda spoken, query, source: source)
    @patch.object(server, "get_json")
    def test_short_excerpt_in_long_report_is_retrieved(self, get_json, enrich, resolve):
        quote = "الطهور شطر الإيمان"
        report = "عن أبي مالك الأشعري قال قال رسول الله " + quote + " والحمد لله تملأ الميزان وسبحان الله والحمد لله تملآن ما بين السماوات والأرض"
        self.assertLess(server.similarity(quote, report), .86)
        get_json.return_value = dorar_response(report)
        segment = {"ar": quote, "en": "Draft", "candidate": {"kind": "hadith", "hadith_query": quote}}
        self.assertTrue(server.resolve_segment_citation(segment))
        self.assertEqual(segment["source"]["arabic"], report)
        self.assertTrue(segment["source"]["partial"])
        self.assertEqual(segment["source"]["alignment_status"], "needs_selection")
        self.assertTrue(segment["needs_review"])
        self.assertFalse(segment["reviewed"])
        self.assertNotIn("candidate", segment)
        get_json.assert_called_once()

    @patch.object(server, "resolve_dorar_reference", side_effect=lambda source, query: source)
    @patch.object(server, "enrich_hadith_translation", side_effect=lambda spoken, query, source: source)
    @patch.object(server, "get_json", return_value=dorar_response(CANONICAL))
    def test_boundary_error_attaches_reference_without_changing_transcript(self, get_json, enrich, resolve):
        segment = {"ar": SPOKEN, "en": "Speaker draft", "candidate": {"kind": "hadith", "hadith_query": CANONICAL}}
        self.assertTrue(server.resolve_segment_citation(segment))
        self.assertEqual(segment["ar"], SPOKEN)
        self.assertEqual(segment["en"], "Speaker draft")
        self.assertEqual(segment["source"]["subtitle_arabic"], CANONICAL)
        self.assertEqual(segment["source"]["translation_status"], "machine_draft")
        self.assertFalse(server.publishable({"status": "ready", "segments": json.dumps([segment])}))

    @patch.object(server, "resolve_dorar_reference", side_effect=lambda source, query: source)
    @patch.object(server, "enrich_hadith_translation", side_effect=lambda spoken, query, source: source)
    @patch.object(server, "get_json")
    def test_long_query_retries_a_short_anchor_only_after_no_match(self, get_json, enrich, resolve):
        get_json.side_effect = [{"ahadith": {"result": ""}}, dorar_response(CANONICAL)]
        segment = {"ar": CANONICAL, "en": "Draft", "candidate": {"kind": "hadith", "hadith_query": CANONICAL}}
        self.assertTrue(server.verify_hadith(segment))
        queries = [server.urllib.parse.parse_qs(server.urllib.parse.urlsplit(call.args[0]).query)["skey"][0] for call in get_json.call_args_list]
        self.assertEqual(len(queries), 2)
        self.assertEqual(queries[1], " ".join(server.normalize_ar(CANONICAL[:100]).split()[:6]))

    @patch.object(server, "get_json", return_value={"ahadith": {"result": ""}})
    def test_failed_search_is_bounded_and_keeps_candidate(self, get_json):
        segment = {"ar": SPOKEN, "en": "Draft", "candidate": {"kind": "hadith", "hadith_query": CANONICAL}}
        self.assertFalse(server.resolve_segment_citation(segment))
        self.assertLessEqual(get_json.call_count, 3)
        self.assertEqual(segment["citation_lookup"]["status"], "not_matched")
        self.assertEqual(segment["candidate"]["kind"], "hadith")
        self.assertEqual(segment["en"], "Draft")

    @patch.object(server, "verify_hadith", side_effect=urllib.error.HTTPError("https://dorar.net", 503, "unavailable", {}, None))
    def test_source_outage_is_visible_and_retryable(self, verify):
        segment = {"ar": SPOKEN, "en": "Draft", "candidate": {"kind": "hadith"}, "reviewed": True}
        self.assertFalse(server.resolve_segment_citation(segment))
        self.assertEqual(segment["citation_lookup"]["status"], "unavailable")
        self.assertEqual(segment["citation_lookup"]["http_status"], 503)
        self.assertIn("candidate", segment)
        self.assertFalse(segment["reviewed"])

    @patch.object(server, "verify_quran", side_effect=ValueError("bad source JSON"))
    def test_invalid_source_response_is_distinct_from_no_match(self, verify):
        segment = {"ar": "النص", "en": "Draft", "candidate": {"kind": "quran"}}
        self.assertFalse(server.resolve_segment_citation(segment))
        self.assertEqual(segment["citation_lookup"]["status"], "invalid_response")

    @patch.object(server, "verify_quran", side_effect=RuntimeError("programming failure"))
    def test_unexpected_errors_are_not_silently_disguised_as_no_match(self, verify):
        with self.assertRaises(RuntimeError):
            server.resolve_segment_citation({"candidate": {"kind": "quran"}})

    @patch.object(server, "verify_hadith")
    @patch.object(server, "verify_quran")
    def test_ordinary_speech_does_not_trigger_scripture_search(self, quran, hadith):
        segment = {"ar": "كلام عادي", "en": "Normal speech", "candidate": {"kind": "speech"}}
        self.assertTrue(server.resolve_segment_citation(segment))
        quran.assert_not_called()
        hadith.assert_not_called()


if __name__ == "__main__":
    unittest.main()
