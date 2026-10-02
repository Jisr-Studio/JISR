"""Automatic sourced Hadith translation abstains on ambiguity and outages."""
import copy
import json
import sys
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

SPOKEN = "الطهور شطر الإيمان"
FULL = SPOKEN + " والحمد لله تملأ الميزان"
REFERENCE = {"kind": "hadith", "arabic": FULL, "english": "Machine draft", "narrator": "أبو مالك الأشعري", "grade": "صحيح", "attribution": "مسلم · 223", "scholar": "مسلم", "url": "https://dorar.net/hadith/search?q=test", "translation_status": "machine_draft", "explanation_status": "unavailable"}
SOURCED = {"kind": "hadith", "id": "65004", "arabic": "عن أبي مالك الأشعري قال: " + FULL, "english": "Source translation", "narrator": "أبو مالك الأشعري", "grade": "صحيح", "attribution": "رواه مسلم", "explanation": "شرح المصدر", "url": "https://hadeethenc.com/ar/browse/hadith/65004", "translation_status": "sourced", "explanation_status": "available"}


def candidate(hadith_id="65004", arabic=FULL):
    return {"id": hadith_id, "arabic": arabic, "url": "https://hadeethenc.com/ar/browse/hadith/" + hadith_id}


class HadithTranslationTests(unittest.TestCase):
    def test_search_parser_deduplicates_and_rejects_foreign_and_invalid_links(self):
        fragment = f'<a href="https://hadeethenc.com/ar/browse/hadith/65004#:~:text=term"><mark>{FULL}</mark></a><a href="/ar/browse/hadith/65004">Duplicate</a><a href="https://other.example/ar/browse/hadith/1">{FULL}</a><a href="/ar/browse/hadith/not-an-id">{FULL}</a><a href="javascript:alert(1)">{FULL}</a>'
        self.assertEqual(server.parse_hadeethenc_search(fragment), [candidate()])

    @patch.object(server.urllib.request, "urlopen")
    def test_public_search_request_uses_published_fields(self, urlopen):
        class Response:
            headers = Message()
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return f'<a href="/ar/browse/hadith/65004">{FULL}</a>'.encode()
        urlopen.return_value = Response()
        self.assertEqual(server.search_hadeethenc(SPOKEN), [candidate()])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://hadeethenc.com/ar/ajax/search")
        self.assertEqual(server.urllib.parse.parse_qs(request.data.decode()), {"trans": ["ar"], "term": [SPOKEN]})

    @patch.object(server, "search_hadeethenc", return_value=[candidate()])
    @patch.object(server, "lookup_hadith", return_value=SOURCED)
    def test_unique_match_uses_source_english_and_keeps_dorar_verification(self, lookup, search):
        original = copy.deepcopy(REFERENCE)
        result = server.enrich_hadith_translation(SPOKEN, SPOKEN, REFERENCE)
        self.assertEqual(result["english"], "Source translation")
        self.assertEqual(result["explanation"], SOURCED["explanation"])
        self.assertEqual(result["verification"]["attribution"], REFERENCE["attribution"])
        self.assertEqual(result["translation_lookup_status"], "matched")
        self.assertEqual(REFERENCE, original)

    @patch.object(server, "search_hadeethenc", return_value=[candidate(), candidate("66526")])
    @patch.object(server, "lookup_hadith", side_effect=[SOURCED, {**SOURCED, "id": "66526"}])
    def test_multiple_matched_reports_remain_a_draft_with_choices(self, lookup, search):
        result = server.enrich_hadith_translation(SPOKEN, SPOKEN, REFERENCE)
        self.assertEqual(result["english"], "Machine draft")
        self.assertEqual(result["translation_lookup_status"], "ambiguous")
        self.assertEqual([c["id"] for c in result["translation_candidates"]], ["65004", "66526"])

    @patch.object(server, "search_hadeethenc", return_value=[candidate(), candidate("66526")])
    @patch.object(server, "lookup_hadith", side_effect=[SOURCED, OSError("unavailable")])
    def test_failed_candidate_does_not_make_remaining_match_unique(self, lookup, search):
        result = server.enrich_hadith_translation(SPOKEN, SPOKEN, REFERENCE)
        self.assertEqual(result["english"], "Machine draft")
        self.assertEqual(result["translation_lookup_status"], "unavailable")

    @patch.object(server, "search_hadeethenc", return_value=[candidate()])
    @patch.object(server, "lookup_hadith", return_value={**SOURCED, "arabic": SPOKEN + " رواية أخرى مختلفة تماما"})
    def test_matching_short_phrase_does_not_override_different_full_report(self, lookup, search):
        result = server.enrich_hadith_translation(SPOKEN, SPOKEN, REFERENCE)
        self.assertEqual(result["translation_lookup_status"], "not_found")
        self.assertEqual(result["translation_status"], "machine_draft")

    @patch.object(server, "search_hadeethenc", return_value=[candidate()])
    @patch.object(server, "lookup_hadith", return_value={**SOURCED, "grade": ""})
    def test_incomplete_source_is_not_promoted_to_sourced_translation(self, lookup, search):
        self.assertEqual(server.enrich_hadith_translation(SPOKEN, SPOKEN, REFERENCE)["translation_lookup_status"], "not_found")

    @patch.object(server, "search_hadeethenc", return_value=[candidate(str(i)) for i in range(9)])
    @patch.object(server, "lookup_hadith")
    def test_large_result_set_is_visible_and_not_arbitrarily_truncated_to_match(self, lookup, search):
        result = server.enrich_hadith_translation(SPOKEN, SPOKEN, REFERENCE)
        self.assertEqual(result["translation_lookup_status"], "too_many_candidates")
        self.assertEqual(len(result["translation_candidates"]), 8)
        lookup.assert_not_called()

    @patch.object(server, "enrich_hadith_translation", side_effect=OSError("unavailable"))
    @patch.object(server, "get_json", return_value={"ahadith": {"result": f'<div>{FULL}</div><div class="hadith-info">الراوي : أبو مالك الأشعري | المحدث : مسلم | المصدر : صحيح مسلم | خلاصة حكم المحدث : صحيح</div>'}})
    def test_translation_outage_preserves_dorar_reference_and_review_gate(self, get_json, enrich):
        segment = {"ar": SPOKEN, "en": "Machine draft", "candidate": {"kind": "hadith", "hadith_query": SPOKEN}}
        self.assertTrue(server.verify_hadith(segment))
        self.assertEqual(segment["source"]["translation_lookup_status"], "unavailable")
        self.assertTrue(segment["needs_review"])
        self.assertFalse(server.publishable({"status": "ready", "segments": json.dumps([segment])}))

    @patch.object(server, "get_json", side_effect=[{"id": "123", "hadeeth": FULL}, {"id": "999", "hadeeth": "Wrong English"}])
    def test_wrong_english_record_id_is_rejected(self, get_json):
        with self.assertRaises(ValueError):
            server.lookup_hadith("123", SPOKEN)


if __name__ == "__main__":
    unittest.main()
