import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


def response(parts):
    return {'status': 'completed', 'text': json.dumps({'items': [{'id': 'cue', 'terms': [], 'parts': parts}]})}


class CueReadabilityTests(unittest.TestCase):
    @patch.object(server, 'translate_segments', side_effect=AssertionError('Existing clauses need no AI request'))
    def test_existing_hadith_clauses_split_locally_without_losing_translation_or_words(self, translate):
        text = 'من تقرب إلي شبرا تقربت إليه ذراعا، ومن تقرب إلي ذراعا تقربت إليه باعا، ومن أتاني يمشي أتيت له هرولة.'
        words = [{'text': w, 'start': i * .7, 'end': i * .7 + .6} for i, w in enumerate(text.split())]
        segment = {'id': 'quote', 'type': 'hadith', 'ar': text,
                   'translation': 'Whoever draws near a span, I draw near a cubit; whoever draws near a cubit, I draw near a fathom; whoever comes walking, I come running.',
                   'words': words, 'start': 0, 'end': words[-1]['end'], 'source': {'arabic': 'Previous variant'}}
        original = copy.deepcopy(segment)
        clauses = [segment]; server.reflow_hadith_cues(clauses)
        self.assertEqual(len(clauses), 3)
        self.assertEqual([w for s in clauses for w in s['words']], original['words'])
        self.assertEqual(' '.join(s['translation'] for s in clauses), original['translation'])
        self.assertEqual([(round(s['start'], 3), round(s['end'], 3)) for s in clauses], [(0, 4.8), (4.9, 9.7), (9.8, 13.9)])
        self.assertTrue(all(s['reviewed'] is False and s['source'] is None for s in clauses))
        self.assertIsNone(server.split_saved_hadith_clauses({**original, 'translation': 'One complete translation sentence.'}))
        translate.assert_not_called()

    def segment(self):
        words = [{'text': str(i), 'start': i * .5, 'end': i * .5 + .4} for i in range(24)]
        return {'id': 'cue', 'ar': ' '.join(w['text'] for w in words), 'words': words,
                'start': 0, 'end': 11.9, 'translation': '', 'type': 'speech', 'needs_review': False}

    def test_long_speech_requires_repartition_instead_of_translation_word_ratio_split(self):
        segment = self.segment()
        with self.assertRaisesRegex(RuntimeError, 'too long for subtitles'):
            server.translation_parts(segment, {'parts': [{'first_word': 0, 'last_word': 23, 'kind': 'speech', 'translation': 'A paragraph.'}]})

    def test_translation_density_is_checked_even_in_short_arabic_cue(self):
        segment = self.segment()
        segment['words'] = segment['words'][:5]
        with self.assertRaisesRegex(RuntimeError, '180 translation characters'):
            server.translation_parts(segment, {'parts': [{'first_word': 0, 'last_word': 4, 'kind': 'speech', 'translation': 'Long text ' * 25}]})

    @patch.object(server, 'ground_terminology')
    @patch.object(server, 'translation_request')
    @patch.object(server, 'translation_key', return_value='test-key')
    def test_model_repair_preserves_every_word_and_only_commits_readable_cues(self, key, request, ground):
        segment = self.segment()
        before = copy.deepcopy(segment)
        request.side_effect = [response([{'first_word': 0, 'last_word': 23, 'kind': 'speech', 'translation': 'Long passage.'}]),
                                response([{'first_word': 0, 'last_word': 11, 'kind': 'speech', 'translation': 'First connected clause.'},
                                          {'first_word': 12, 'last_word': 23, 'kind': 'speech', 'translation': 'Second connected clause.'}])]
        segments, checkpoints = [segment], []
        server.translate_segments(segments, checkpoint=lambda cues: checkpoints.append(copy.deepcopy(cues)))
        self.assertEqual(request.call_count, 2)
        self.assertEqual(len(checkpoints), 1)
        self.assertEqual([w for cue in segments for w in cue['words']], before['words'])
        self.assertEqual([(s['start'], s['end']) for s in segments], [(0, 5.9), (6, 11.9)])
        self.assertEqual(' '.join(s['ar'] for s in segments), before['ar'])
        self.assertIn('too long for subtitles', request.call_args.args[0]['input'])

    @patch.object(server, 'translation_request', return_value=response([{'first_word': 0, 'last_word': 23, 'kind': 'speech', 'translation': 'Still too long.'}]))
    @patch.object(server, 'translation_key', return_value='test-key')
    def test_repeated_unreadable_response_is_bounded_and_does_not_mutate_input(self, key, request):
        segments = [self.segment()]
        before = copy.deepcopy(segments)
        with self.assertRaisesRegex(RuntimeError, 'too long for subtitles'):
            server.translate_segments(segments)
        self.assertEqual(segments, before)
        self.assertEqual(request.call_count, 2)

    def test_short_greeting_remains_connected_and_long_reference_is_not_misclassified(self):
        text = 'السلام عليكم ورحمة الله وبركاته'
        segment = server.words_to_segments([{'type': 'word', 'text': w, 'start': i * .2, 'end': i * .2 + .15} for i, w in enumerate(text.split())])[0]
        result = server.translation_parts(segment, {'parts': [{'first_word': 0, 'last_word': 4, 'kind': 'speech', 'translation': 'Peace be upon you, and Allah’s mercy and blessings.'}]})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['ar'], text)
        with self.assertRaisesRegex(RuntimeError, 'too long for subtitles'):
            server.translation_parts(self.segment(), {'parts': [{'first_word': 0, 'last_word': 23, 'kind': 'hadith', 'translation': 'Reference draft ' * 20}]})
        result = server.translation_parts(self.segment(), {'parts': [
            {'first_word': 0, 'last_word': 11, 'kind': 'hadith', 'translation': 'First quotation clause.'},
            {'first_word': 12, 'last_word': 23, 'kind': 'hadith', 'translation': 'Second quotation clause.'}]})
        self.assertTrue(all(s['candidate']['kind'] == 'hadith' for s in result))

    @patch.object(server, 'translation_request', return_value=response([
        {'first_word': 0, 'last_word': 11, 'kind': 'hadith', 'translation': 'First quotation clause.'},
        {'first_word': 12, 'last_word': 23, 'kind': 'hadith', 'translation': 'Second quotation clause.'}]))
    @patch.object(server, 'translation_key', return_value='test-key')
    def test_legacy_hadith_paragraph_reflows_with_all_words_and_real_timestamps(self, key, request):
        quote = self.segment()
        quote.update(type='hadith', translation='Long saved quote.', source={'arabic': 'Previous variant'}, candidate={'kind': 'hadith'})
        original = copy.deepcopy(quote)
        segments = [quote]
        self.assertTrue(server.needs_hadith_reflow(quote))
        server.reflow_hadith_cues(segments)
        self.assertEqual([w for s in segments for w in s['words']], original['words'])
        self.assertEqual([(s['start'], s['end']) for s in segments], [(0, 5.9), (6, 11.9)])
        self.assertTrue(all(s['source'] is None and s['candidate']['kind'] == 'hadith' for s in segments))
        for change in ({'reviewed': True}, {'translation_origin': 'human'}, {'source_caption': 'Custom'},
                       {'source': {'quotation_mode': 'paraphrase'}}):
            with self.subTest(change=change):
                self.assertFalse(server.needs_hadith_reflow({**original, **change}))

    @patch.object(server, 'translate_segments', side_effect=RuntimeError('provider failure'))
    def test_hadith_reflow_failure_keeps_original_reference_and_translation(self, translate):
        quote = self.segment()
        quote.update(type='hadith', translation='Saved quote.', source={'arabic': 'Original source'})
        segments = [quote]; original = copy.deepcopy(segments)
        with self.assertRaises(RuntimeError):
            server.reflow_hadith_cues(segments)
        self.assertEqual(segments, original)

    @patch.object(server, 'translate_segments', side_effect=RuntimeError('provider failure'))
    def test_reflow_outage_preserves_existing_translation(self, translate):
        segment = self.segment()
        segment['translation'] = 'Existing saved translation paragraph.'
        segments = [segment]
        before = copy.deepcopy(segments)
        with self.assertRaises(RuntimeError):
            server.reflow_speech_cues(segments)
        self.assertEqual(segments, before)

    @patch.object(server, 'translate_segments')
    def test_reflow_preserves_reviewed_segments_and_unresolved_scripture(self, translate):
        segment = self.segment()
        segment['translation'] = 'Existing translation.'
        segment['reviewed'] = True
        quote = copy.deepcopy(segment)
        quote.update(id='quote', reviewed=False, candidate={'kind': 'hadith'})
        segments = [segment, quote]
        before = copy.deepcopy(segments)
        server.reflow_speech_cues(segments)
        self.assertEqual(segments, before)
        translate.assert_not_called()

    @patch.object(server, 'lookup_term', return_value={'term': 'الإيمان', 'definition_ar': 'التصديق'})
    @patch.object(server, 'translation_request', return_value={'status': 'completed', 'text': json.dumps({'items': [{'id': 'cue', 'translation': 'An expanded dictionary explanation. ' * 10}]})})
    def test_dictionary_refinement_cannot_expand_a_readable_cue_into_a_paragraph(self, request, lookup):
        segment = self.segment()
        segment.update(words=segment['words'][:5], end=2.4, translation='Faith.', detected_terms=['الإيمان'])
        with self.assertRaisesRegex(RuntimeError, 'too long'):
            server.ground_terminology([segment], 'test-key')
        self.assertEqual(segment['translation'], 'Faith.')


if __name__ == '__main__':
    unittest.main()
