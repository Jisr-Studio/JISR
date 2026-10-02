"""Approved commentary stays separate from Quran text and keeps its scope."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


INDEX = '<select id="soora"><option value="2">سورة البقرة</option></select><select id="sect"><option value="0">Introduction</option><option value="37">الآيات (215 - 220)</option><option value="38">الآيات (221 - 224)</option><option value="42">الآية (253)</option></select>'
ARTICLE = '<nav>Unrelated navigation</nav><article id="tt4"><h5>تفسير الآيات</h5><p>Commentary from the source.<br>Another paragraph.</p><p>Reference: book and page.</p><script>do not include scripts</script></article><footer>Unrelated footer</footer>'


class TafsirTests(unittest.TestCase):
    def setUp(self):
        self.cache_patch = patch.object(server, "TAFSIR_INDEX", {})
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)

    @patch.object(server, "get_html", side_effect=[INDEX, ARTICLE, ARTICLE])
    def test_tafsir_uses_indexed_section_and_preserves_scope_and_references(self, get_html):
        source = server.lookup_tafsir(2, 222)
        self.assertEqual(source["explanation_url"], "https://dorar.net/tafseer/2/38")
        self.assertEqual(source["surah_name"], "سورة البقرة")
        self.assertEqual(source["explanation_scope"], "الآيات (221 - 224)")
        self.assertEqual(source["explanation_status"], "available")
        self.assertIn("Reference: book and page.", source["explanation"])
        self.assertIn("Commentary from the source.\nAnother paragraph.", source["explanation"])
        self.assertNotIn("Unrelated", source["explanation"])
        self.assertNotIn("include scripts", source["explanation"])
        self.assertIn("222", source["explanation"])
        server.lookup_tafsir(2, 223)
        self.assertEqual(get_html.call_count, 3)  # Surah metadata reused; content fetched live.

    @patch.object(server, "get_html", return_value=INDEX)
    def test_unindexed_ayah_does_not_invent_section_link(self, get_html):
        with self.assertRaises(ValueError):
            server.lookup_tafsir(2, 225)
        self.assertEqual(get_html.call_count, 1)

    @patch.object(server, "get_html", side_effect=[INDEX, '<article id="other">Unrelated content</article>'])
    def test_changed_site_structure_does_not_attach_unrelated_content(self, get_html):
        with self.assertRaises(ValueError):
            server.lookup_tafsir(2, 222)

    @patch.object(server, "lookup_tafsir", side_effect=ValueError("source unavailable"))
    @patch.object(server, "get_json", side_effect=[{"text": "إن الله يحب التوابين ويحب المتطهرين"}, {"translation_text": "Reference translation"}])
    def test_missing_commentary_does_not_generate_an_explanation(self, get_json, lookup):
        segment = {"ar": "إن الله يحب التوابين ويحب المتطهرين", "candidate": {"surah": 2, "ayah": 222}}
        self.assertTrue(server.verify_quran(segment))
        source = segment["source"]
        self.assertNotIn("explanation", source)
        self.assertEqual(source["explanation_status"], "unavailable")
        self.assertEqual(source["explanation_url"], "https://dorar.net/tafseer/2")
        self.assertTrue(segment["needs_review"])


if __name__ == "__main__":
    unittest.main()
