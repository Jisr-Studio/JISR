import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

SPOKEN = 'إن الله حيي كريم يستحي أن يرد يد عبده سفرا'
CANONICAL = 'عن سلمان قال قال رسول الله إن ربكم حيي كريم يستحيي من عبده إذا رفع يديه إليه أن يردهما صفرا'
SOURCE = {'kind': 'hadith', 'id': '5499', 'title': 'حديث رفع اليدين في الدعاء', 'arabic': CANONICAL,
          'translation': 'Source translation quotation.', 'narrator': 'سلمان', 'grade': 'حسن', 'attribution': 'أبو داود والترمذي وابن ماجه',
          'url': 'https://hadeethenc.com/ar/browse/hadith/5499', 'quotation_mode': 'paraphrase',
          'relation_method': 'editor_selected', 'partial': True}


class HadithSuggestionTests(unittest.TestCase):
    def segment(self):
        return {'ar': SPOKEN, 'translation': 'Speaker draft.', 'type': 'speech', 'source': None,
                'candidate': {'kind': 'hadith', 'hadith_query': SPOKEN.replace('سفرا', 'صفرا')}}

    @patch.object(server, 'search_hadeethenc', return_value=[{'id': '5499', 'arabic': CANONICAL}])
    @patch.object(server, 'lookup_hadith', return_value=SOURCE)
    @patch.object(server, 'verify_hadith', return_value=False)
    def test_saved_asr_and_abbreviated_wording_get_source_choice_not_false_literal_match(self, verify, lookup, search):
        segment = self.segment()
        self.assertFalse(server.resolve_segment_citation(segment))
        self.assertEqual(segment['citation_lookup']['status'], 'suggested')
        self.assertEqual(segment['citation_suggestions'][0]['id'], '5499')
        self.assertIsNone(segment['source'])
        self.assertEqual(segment['ar'], SPOKEN)
        self.assertEqual(segment['translation'], 'Speaker draft.')
        self.assertTrue(segment['needs_review'])
        self.assertFalse(server.publishable({'status': 'ready', 'segments': json.dumps([segment])}))
        self.assertLessEqual(search.call_count, 3)
        lookup.assert_called_once_with('5499', SPOKEN, paraphrase=True)

    @patch.object(server, 'search_hadeethenc', return_value=[{'id': '1', 'arabic': 'لا إله إلا الله العظيم الحليم لا إله إلا الله رب العرش الكريم'}])
    @patch.object(server, 'lookup_hadith')
    def test_generic_religious_words_do_not_admit_unrelated_search_results(self, lookup, search):
        segment = self.segment()
        self.assertFalse(server.suggest_hadith_references(segment))
        self.assertNotIn('citation_suggestions', segment)
        lookup.assert_not_called()

    @patch.object(server, 'search_hadeethenc', side_effect=OSError('outage'))
    def test_fallback_failure_is_bounded_and_keeps_candidate(self, search):
        segment = self.segment()
        self.assertFalse(server.suggest_hadith_references(segment))
        self.assertEqual(segment['citation_suggestion_status'], 'unavailable')
        self.assertIn('candidate', segment)
        self.assertLessEqual(search.call_count, 3)

    @patch.object(server, 'search_hadeethenc', return_value=[{'id': '5499', 'arabic': CANONICAL}])
    @patch.object(server, 'lookup_hadith', return_value={**SOURCE, 'arabic': 'حديث مختلف تماما لا يتعلق بنص البحث'})
    def test_complete_record_is_rechecked_after_a_matching_snippet(self, lookup, search):
        segment = self.segment()
        self.assertFalse(server.suggest_hadith_references(segment))
        self.assertNotIn('citation_suggestions', segment)

    @patch.object(server, 'search_hadeethenc', return_value=[{'id': '5499', 'arabic': CANONICAL}])
    @patch.object(server, 'lookup_hadith', return_value={**SOURCE, 'grade': ''})
    def test_incomplete_source_is_not_offered(self, lookup, search):
        segment = self.segment()
        self.assertFalse(server.suggest_hadith_references(segment))
        self.assertNotIn('citation_suggestions', segment)

    @patch.object(server, 'search_hadeethenc', return_value=[{'id': '5499', 'arabic': CANONICAL}])
    @patch.object(server, 'lookup_hadith', return_value={**SOURCE, 'quotation_mode': 'quotation'})
    @patch.object(server, 'prepare_quote_subtitles', side_effect=lambda spoken, source: source)
    def test_unique_exact_source_can_attach_without_dorar(self, prepare, lookup, search):
        segment = self.segment()
        segment['ar'] = 'إن ربكم حيي كريم يستحيي من عبده إذا رفع يديه إليه أن يردهما صفرا'
        self.assertTrue(server.suggest_hadith_references(segment))
        self.assertEqual(segment['source']['id'], '5499')
        self.assertFalse(segment['reviewed'])


if __name__ == '__main__':
    unittest.main()
