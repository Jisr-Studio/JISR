"""Fetch exact dictionary records and keep source-guided translation auditable."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


AR = '<div class="entry-wraper"><h1>الاجْتِهَاد</h1><div class="entry-main-content"><h5>Dictionary source</h5><p>تعريف موثّق للاجتهاد.</p><div class="footnotes">Reference: book and page.</div><script>ignore this</script></div><section><a href="/dictionary/word/196/en">translation</a></section></div><footer>Unrelated navigation</footer>'
EN = '<div class="entry-wraper"><h1>Ijtihad (الاجتهاد)</h1><div class="entry-main-content"><p>Definition from the translation source.</p></div></div>'
SEARCH = {"table_data": '<a href="https://islamic-content.com/legacy-dictionary/word/196">الاجْتِهَاد</a>'}
REFERENCE = {"term": "الاجتهاد", "definition_ar": "تعريف موثّق", "translation_term": "Ijtihad", "definition_en": "Source definition", "url": "https://islamic-content.com/dictionary/word/196", "provider": "Al-Jamhara", "status": "bilingual"}


def response(items):
    return {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps({"items": items})}]}]}


class TerminologyTests(unittest.TestCase):
    def setUp(self):
        self.cache = patch.object(server, "TERM_CACHE", {})
        self.cache.start()
        self.addCleanup(self.cache.stop)

    @patch.object(server, "get_html", side_effect=[AR, EN])
    @patch.object(server, "get_json", return_value=SEARCH)
    def test_exact_source_translation_definitions_and_cache(self, get_json, get_html):
        source = server.lookup_term("الاجتهاد")
        self.assertEqual(source["translation_term"], "Ijtihad")
        self.assertEqual(source["status"], "bilingual")
        self.assertIn("Reference: book and page.", source["definition_ar"])
        self.assertNotIn("ignore this", source["definition_ar"])
        self.assertNotIn("Unrelated navigation", source["definition_ar"])
        self.assertEqual(get_html.call_args_list[0].args[0], REFERENCE["url"])
        self.assertEqual(get_json.call_args.kwargs["headers"]["X-Requested-With"], "XMLHttpRequest")
        source["term"] = "mutated"
        self.assertNotEqual(server.lookup_term("والاجتهاد")["term"], "mutated")
        self.assertEqual(get_json.call_count, 1)

    def test_similar_ambiguous_and_foreign_search_links_are_rejected(self):
        fragments = ['<a href="/dictionary/word/196">الاجتهاد الجماعي</a>',
                     '<a href="https://other.example/dictionary/word/196">الاجتهاد</a>',
                     '<a href="/dictionary/word/196">الاجتهاد</a><a href="/dictionary/word/197">الاجتهاد</a>']
        for fragment in fragments:
            with self.subTest(fragment=fragment), patch.object(server, "get_json", return_value={"table_data": fragment}), patch.object(server, "get_html") as get_html:
                with self.assertRaises(ValueError):
                    server.lookup_term("الاجتهاد")
                get_html.assert_not_called()

    @patch.object(server, "get_json", return_value=SEARCH)
    @patch.object(server, "get_html", return_value=AR.replace("الاجْتِهَاد</h1>", "الصلاة</h1>"))
    def test_detail_title_mismatch_is_rejected(self, get_html, get_json):
        with self.assertRaises(ValueError):
            server.lookup_term("الاجتهاد")

    @patch.object(server, "get_html", side_effect=[AR, EN])
    @patch.object(server, "get_json", side_effect=[{"table_data": '<a href="/dictionary/word/204">الاجتهاد الجماعي</a>'}, SEARCH])
    def test_tatweel_search_fallback_still_requires_complete_title(self, get_json, get_html):
        self.assertEqual(server.lookup_term("الاجتهاد")["translation_term"], "Ijtihad")
        self.assertEqual(get_json.call_count, 2)
        self.assertTrue(get_json.call_args.args[0].endswith(server.urllib.parse.quote("تهاد")))

    @patch.object(server, "get_json", return_value=SEARCH)
    @patch.object(server, "get_html", return_value=AR.replace('/dictionary/word/196/en', '/dictionary/word/196/fr'))
    def test_arabic_only_record_does_not_invent_translation_link(self, get_html, get_json):
        source = server.lookup_term("الاجتهاد")
        self.assertEqual(source["status"], "arabic_only")
        self.assertNotIn("translation_term", source)
        self.assertEqual(get_html.call_count, 1)

    @patch.object(server, "get_json", return_value=SEARCH)
    @patch.object(server, "get_html", side_effect=[AR, OSError("unavailable")])
    def test_failed_translation_fetch_keeps_arabic_with_explicit_status(self, get_html, get_json):
        self.assertEqual(server.lookup_term("الاجتهاد")["status"], "translation_unavailable")

    @patch.object(server, "get_json", return_value=SEARCH)
    @patch.object(server, "get_html", side_effect=[AR, EN.replace("الاجتهاد", "الصلاة")])
    def test_wrong_translation_headword_is_not_attached(self, get_html, get_json):
        source = server.lookup_term("الاجتهاد")
        self.assertEqual(source["status"], "translation_unavailable")
        self.assertNotIn("translation_term", source)

    def test_invented_terms_rejected_and_scripture_not_refined(self):
        segment = {"id": "one", "ar": "الاجتهاد علم", "translation": "", "needs_review": False}
        with self.assertRaises(RuntimeError):
            server.translation_parts(segment, {"kind": "speech", "translation": "Draft", "terms": ["الوضوء"]})
        child = server.translation_parts(segment, {"kind": "quran", "translation": "Draft", "terms": ["الاجتهاد"]})[0]
        self.assertEqual(child["detected_terms"], [])
        self.assertTrue(server.term_in_text("الاجتهاد", "والاجتهاد علم"))
        self.assertFalse(server.term_in_text("صلاة", "صلاته"))

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "lookup_term", return_value=REFERENCE)
    @patch.object(server, "post_json")
    def test_grounding_revises_speech_and_keeps_provenance(self, post_json, lookup):
        segments = [{"id": "one", "ar": "الاجتهاد علم", "translation": "", "needs_review": False}]
        post_json.side_effect = [response([{"id": "one", "kind": "speech", "translation": "Draft", "terms": ["الاجتهاد"]}]),
                                 response([{"id": "one", "translation": "Ijtihad is a discipline."}])]
        server.translate_segments(segments)
        self.assertEqual(segments[0]["translation"], "Ijtihad is a discipline.")
        self.assertEqual(segments[0]["terminology"][0]["url"], REFERENCE["url"])
        self.assertIsNone(segments[0]["source"])
        sent = json.loads(post_json.call_args.args[1]["input"].split("Input: ", 1)[1])
        self.assertEqual(sent[0]["dictionary"][0]["definition_en"], REFERENCE["definition_en"])

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "lookup_term", side_effect=ValueError("no match"))
    @patch.object(server, "post_json", return_value=response([{"id": "one", "kind": "speech", "translation": "Draft", "terms": ["الاجتهاد"]}]))
    def test_unavailable_dictionary_requires_review(self, post_json, lookup):
        segments = [{"id": "one", "ar": "الاجتهاد علم", "translation": "", "needs_review": False}]
        server.translate_segments(segments)
        self.assertTrue(segments[0]["needs_review"])
        self.assertEqual(segments[0]["terminology_warning"]["unavailable_terms"], ["الاجتهاد"])
        self.assertEqual(post_json.call_count, 1)
        self.assertFalse(server.publishable({"status": "ready", "segments": json.dumps(segments)}))

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "lookup_term", return_value=REFERENCE)
    @patch.object(server, "post_json")
    def test_invalid_refinement_does_not_commit_draft(self, post_json, lookup):
        segments = [{"id": "one", "ar": "الاجتهاد علم", "translation": "", "needs_review": False}]
        original = copy.deepcopy(segments)
        post_json.side_effect = [response([{"id": "one", "kind": "speech", "translation": "Draft", "terms": ["الاجتهاد"]}]), response([{"id": "wrong", "translation": "Revised"}])]
        with self.assertRaises(RuntimeError):
            server.translate_segments(segments)
        self.assertEqual(segments, original)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch.object(server, "post_json", return_value=response([{"id": "one", "kind": "speech", "translation": "Draft"}]))
    def test_missing_detection_does_not_silently_skip_dictionary(self, post_json):
        segments = [{"id": "one", "ar": "الاجتهاد علم", "translation": "", "needs_review": False}]
        original = copy.deepcopy(segments)
        with self.assertRaises(RuntimeError):
            server.translate_segments(segments)
        self.assertEqual(segments, original)


if __name__ == "__main__":
    unittest.main()
