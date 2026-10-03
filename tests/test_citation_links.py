"""Record links must retain full text and attribution, never just a phrase."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from scripts.refresh_source_links import refresh_source

TEXT = "خذوا جنتكم من النار قولوا سبحان الله والحمد لله"
REFERENCE = {"arabic": TEXT, "narrator": "-", "scholar": "المقبلي", "attribution": "المصابيح في الأحاديث المتواترة · 609", "grade": "متواتر معنى [كما قال في المقدمة]"}


def card(record="lS2wNsu7", source=None, extra=""):
    s = {**REFERENCE, **(source or {})}
    book, number = s["attribution"].split(" · ")
    return f'<div class="border-bottom py-4"><article><h5 class="h5-responsive">1 - {s["arabic"]}</h5></article><p>خلاصة حكم المحدث : {s["grade"]} الراوي : {s["narrator"]} | المحدث : {s["scholar"]} | المصدر : {book} الصفحة أو الرقم : {number} التصنيف الموضوعي: أذكار</p><a href="/h/{record}?copy=1">نسخ</a><a href="/h/{record}?osoul=1">أصول الحديث</a>{extra}</div>'


class CitationLinksTests(unittest.TestCase):
    def setUp(self):
        cache = patch.object(server, "DORAR_LINK_CACHE", {})
        cache.start()
        self.addCleanup(cache.stop)

    def test_modern_cards_keep_metadata_and_link_in_same_record(self):
        other = {"scholar": "ابن حجر العسقلاني", "narrator": "أبو هريرة", "grade": "حسن", "attribution": "الأمالي المطلقة · 224"}
        records = server.parse_dorar_search(card("VEwtTm6i", other) + card())
        self.assertEqual(records[0]["grade"], "حسن")
        self.assertEqual(records[1]["attribution"], REFERENCE["attribution"])
        self.assertEqual(records[1]["url"], "https://dorar.net/h/lS2wNsu7")
        self.assertEqual(records[1]["origins_url"], "https://dorar.net/h/lS2wNsu7?osoul=1")

    @patch.object(server, "get_html")
    def test_same_words_different_grade_never_replace_record(self, get_html):
        get_html.return_value = card("VEwtTm6i", {"grade": "حسن"}) + card()
        original = copy.deepcopy(REFERENCE)
        result = server.resolve_dorar_reference(REFERENCE, TEXT)
        self.assertEqual(result["url"], "https://dorar.net/h/lS2wNsu7")
        self.assertEqual(REFERENCE, original)
        self.assertEqual(result["grade"], REFERENCE["grade"])

    @patch.object(server, "get_html")
    def test_all_attribution_fields_and_full_text_are_required(self, get_html):
        for wrong in ({"grade": "صحيح"}, {"scholar": "آخر"}, {"narrator": "آخر"},
                      {"attribution": "المصابيح في الأحاديث المتواترة · 610"}, {"arabic": TEXT + " كلام آخر"}):
            with self.subTest(wrong=wrong), patch.object(server, "DORAR_LINK_CACHE", {}):
                get_html.return_value = card(source=wrong)
                result = server.resolve_dorar_reference(REFERENCE, TEXT)
                self.assertEqual(result["link_status"], "search_only")
                self.assertIn("/hadith/search?", result["url"])

    @patch.object(server, "get_html")
    def test_ambiguous_ids_abstain_but_duplicate_links_deduplicate(self, get_html):
        get_html.return_value = card() + card("Another1")
        self.assertEqual(server.resolve_dorar_reference(REFERENCE, TEXT)["link_status"], "search_only")
        with patch.object(server, "DORAR_LINK_CACHE", {}):
            get_html.return_value = card() + card()
            self.assertEqual(server.resolve_dorar_reference(REFERENCE, TEXT)["link_status"], "direct")

    @patch.object(server, "get_html", side_effect=OSError("offline"))
    def test_outage_retains_citation_with_explicit_search_fallback(self, get_html):
        result = server.resolve_dorar_reference(REFERENCE, TEXT)
        self.assertEqual(result["link_status"], "search_only")
        self.assertEqual(result["attribution"], REFERENCE["attribution"])

    def test_legacy_api_links_are_kept_and_no_extra_lookup_needed(self):
        fragment = '<div class="hadith">' + TEXT + '</div><div class="hadith-info">الراوي : - | المحدث : المقبلي | المصدر : المصابيح في الأحاديث المتواترة | الصفحة أو الرقم : 609 | خلاصة حكم المحدث : متواتر معنى [كما قال في المقدمة]<a href="/h/lS2wNsu7">عرض</a></div>'
        parsed = server.parse_dorar(fragment)[0]
        # Link text must not become part of a scholar's grade.
        self.assertEqual(parsed["url"], "https://dorar.net/h/lS2wNsu7")
        self.assertEqual(parsed["grade"], REFERENCE["grade"])
        with patch.object(server, "get_html") as get_html:
            server.resolve_dorar_reference(parsed, TEXT)
            get_html.assert_not_called()

    def test_unsafe_or_unrelated_urls_are_rejected(self):
        for url in ("javascript:alert(1)", "http://dorar.net/h/Test1234", "https://other.example/h/Test1234",
                    "https://dorar.net@other.example/h/Test1234", "/feedback/error-report?link=https://dorar.net/h/Test1234"):
            self.assertIsNone(server.dorar_record_url(url))

    @patch.object(server, "get_html", return_value=card())
    def test_saved_citation_repair_preserves_text_translation_and_attribution(self, get_html):
        old = {**REFERENCE, "url": "https://dorar.net/hadith/search?q=test", "english": "Existing draft", "explanation_status": "unavailable"}
        result = refresh_source(old, "hadith")
        self.assertEqual(result["url"], "https://dorar.net/h/lS2wNsu7")
        for field in (*REFERENCE, "english", "explanation_status"):
            self.assertEqual(result[field], old[field])
        self.assertIn("/hadith/search?", old["url"])

    def test_old_surah_index_is_not_an_ayah_explanation(self):
        old = {"url": "https://quranpedia.net/embed?surah=2&ayah=222", "explanation_status": "unavailable", "explanation_url": "https://dorar.net/tafseer/2"}
        result = refresh_source(old, "quran")
        self.assertNotIn("explanation_url", result)
        self.assertEqual(result["explanation_index_url"], old["explanation_url"])


if __name__ == "__main__":
    unittest.main()
