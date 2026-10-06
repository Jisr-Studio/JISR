"""Shared language policy. Provider IDs are separate from project language codes."""
import copy
import json
from contextvars import ContextVar
from pathlib import Path

LANGUAGES = json.loads((Path(__file__).parent / 'dist/languages.json').read_text(encoding='utf-8'))
ACTIVE_LANGUAGE = ContextVar('jisr_target_language', default='en')
MISSING_TRANSLATION = 'لا تتوفر ترجمة موثقة بهذه اللغة'


def validate_language(value):
    if not isinstance(value, str) or value not in LANGUAGES:
        raise ValueError('لغة الترجمة غير مدعومة')
    return value


def language_code(item=None):
    return validate_language((item or {}).get('target_language') or ACTIVE_LANGUAGE.get())


def language_info(item=None):
    return LANGUAGES[language_code(item)]


def label(key, item=None):
    return language_info(item)['labels'][key]


def migrate_segments(segments, target_language='en'):
    """Idempotent, lossless migration of the old English-only JSON contract."""
    target_language = validate_language(target_language)
    aliases = {'en':'translation', 'english':'translation', 'subtitle_english':'subtitle_translation',
               'english_span':'translation_span', 'quality_previous_english':'quality_previous_translation',
               'translator_en':'translator_translated', 'attribution_en':'attribution_translated', 'grade_en':'grade_translated'}
    def visit(value):
        if isinstance(value, list):
            return [visit(x) for x in value]
        if not isinstance(value, dict):
            return value
        output = {key:visit(x) for key,x in value.items() if key not in aliases}
        for old,new in aliases.items():
            if old in value:
                if new in output and output[new] != value[old]:
                    output.setdefault('legacy_fields', {})[old] = copy.deepcopy(value[old])
                else:
                    output[new] = visit(value[old])
        return output
    migrated = visit(segments)
    for segment in migrated:
        segment.setdefault('target_language', target_language)
        source = segment.get('source')
        if source:
            if source.get('translation_status') == 'machine_draft':
                # Old Dorar records stored ASR translations in their reference.
                # Keep the segment's text but remove the false source attribution.
                source.setdefault('legacy_draft_translation',source.get('translation',''))
                source['translation'] = ''
                source['translator'] = ''
                source['translation_url'] = ''
                source['translation_status'] = 'unavailable'
                source['translation_notice'] = MISSING_TRANSLATION
                source.pop('subtitle_translation',None)
                source.pop('translation_span',None)
                source['alignment_status'] = 'unavailable'
            source.setdefault('target_language', target_language)
            source.setdefault('translation_language', target_language)
            source.setdefault('source_name', 'Quranpedia' if segment.get('type') == 'quran' else 'HadeethEnc' if 'hadeethenc.com' in source.get('url','') else 'Dorar')
            source.setdefault('translation_status', 'sourced' if source.get('translation') else 'unavailable')
    return migrated
