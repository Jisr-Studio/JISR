# Jisr API and data contract

UTF-8 JSON; all timings are seconds from the original Arabic video. API and frontend share one origin. Errors use `{"error":"message"}`. The Arabic editor uses `X-Edit-Token`; upload returns this private token once. The share token only opens a reviewed, read-only project. No accounts are required.

## Project and language

```json
{
  "id": "32-character-hex-id",
  "title": "Video title",
  "filename": "original.mp4",
  "target_language": "ur",
  "translation_direction": "rtl",
  "translation_font": "noto-urdu",
  "status": "ready",
  "error": "",
  "stage": "جاهز للمراجعة",
  "duration": 48.0,
  "created": 1790876907.0,
  "updated": 1790876908.0,
  "segments": [],
  "style": {},
  "publishable": false,
  "exportable": true,
  "export_warnings": ["توجد مقاطع لم تكتمل مراجعتها"],
  "retryable": false,
  "video_url": "/api/projects/ID/video",
  "share_url": "/view/SHARE_TOKEN",
  "editable": true
}
```

`target_language` is allowlisted on the server: `en` (default), `es`, `ur`, `hi`, `id`, `zh-Hans`, `tr`. Urdu translations are RTL; the others are LTR. Input speech and canonical references remain Arabic. The shared catalog is `dist/languages.json`; provider codes are separate from project codes. Quranpedia/HadeethEnc use `zh` for the chosen Chinese sources.

Upload multipart order is `target_language` (one small text field), then `video` (one streamed file). Omitting the language accepts a legacy upload as English. Unknown/duplicate fields and multiple videos are rejected; video bytes are not loaded entirely into RAM.

Old SQLite schemas gain `target_language DEFAULT 'en'`. Legacy `segment.en` and source `english`, `subtitle_english`, `english_span` migrate to `translation`, `subtitle_translation`, `translation_span`. Human changes, captions, approvals, Arabic and word timings remain intact; migration is idempotent. Conflicting duplicate fields are retained in `legacy_fields`. Old Dorar machine translations retain their segment text but are removed from the published-source translation fields.

New responses use neutral fields. A legacy English client may send `en` or `source_english_span` at the segment endpoint only for an English project. Other languages must use the new contract; foreign-language aliases cannot overwrite their translations.

## Segment

```json
{
  "id": "12-character-hex-id",
  "target_language": "ur",
  "start": 0.0,
  "end": 3.2,
  "display_end": 3.5,
  "type": "quran",
  "ar": "Original Arabic transcript",
  "translation": "Target-language subtitle",
  "translation_origin": "source",
  "words": [{"text":"Original word", "start":0.0, "end":0.4}],
  "reviewed": false,
  "needs_review": true,
  "unclear_words": [],
  "source": {
    "kind": "quran",
    "source_name": "Quranpedia",
    "surah": 1,
    "ayah": 1,
    "arabic": "Full canonical Arabic",
    "translation": "Full published target-language translation",
    "target_language": "ur",
    "translation_language": "ur",
    "provider_language": "ur",
    "provider_language_id": 12,
    "translation_book_id": 1966,
    "translator": "Published translator",
    "translation_status": "sourced",
    "url": "Arabic reference link",
    "translation_url": "Translation entry link",
    "partial": true,
    "subtitle_arabic": "Exact corresponding Arabic excerpt",
    "subtitle_translation": "Exact corresponding translated excerpt",
    "subtitle_translation_origin": "source",
    "translation_span": {"start": 10, "end": 40},
    "alignment_status": "selected"
  }
}
```

`type`: `speech`, `quran`, `hadith`. `translation_origin`: `machine`, `source`, `human`, or `unavailable`. Arabic `ar` preserves ASR/editor input. Displayed quote Arabic prefers the verified source excerpt; saving it unchanged preserves ASR and its reference. Subtitle text can be empty only with a review warning/placeholder.

`words` are immutable provider timestamps during translation; the model returns inclusive `first_word`/`last_word` ranges covering every Arabic word exactly once in order. It cannot invent times or drop/reorder words. Explicit Arabic/timing edits invalidate stale word alignment. `display_end` is derived, never an ASR edit: gaps up to 0.5 seconds hold the preceding cue until the next starts; long silence/final cue do not extend. Preview and exports use the same derived end.

`readability` reports `characters_per_second`, duration and issues, using per-language character limits/CPS (Chinese counts characters rather than space-separated words). `quality_review`, `quality_input_hash`, `review_issues` expose independent meaning checks; their hash includes target language. A checked machine output does not confirm human review. Human edits and approvals are protected from normal retry.

`terminology` contains retrieved Al-Jamhara definitions and provenance. Optional English dictionary data has `translation_language: "en"`; it is semantic context, not an approved equivalent in another language. The target-language wording remains an AI/editor translation.

## Religious sources and availability

Canonical Arabic and reference identity are independent of target translation availability. `source.translation_status: "sourced"` means a published translation was actually retrieved for `translation_language`. It does not certify model alignment, religious correctness, or human acceptance.

When the requested translation is missing, empty, inaccessible or invalid:

```json
{
  "translation": "",
  "translation_status": "unavailable",
  "translation_language": "hi",
  "translator": "",
  "translation_url": "",
  "translation_notice": "لا تتوفر ترجمة موثقة بهذه اللغة",
  "alignment_status": "unavailable"
}
```

Optional `translation_fetch_error` reports a failed fetch. Arabic remains documented. The segment can carry an explicitly labelled machine/human alternative, without placing it in the published source's `translation` field or attributing it to that source. A human can review the alternative while the publication status remains unavailable. Source-wording mode requires a sourced exact excerpt; it cannot silently display ASR translation as the reference's translation.

Partial published translations need an exact contiguous substring in the **selected language**. `translation_span` uses Unicode code-point offsets (not JavaScript UTF-16 units), `start` inclusive / `end` exclusive. Selection must be nonempty and cannot select the entire translation for a partial quotation. AI alignment selects existing text only; ambiguous matches remain `needs_selection`. No English span is valid for another language.

Hadith additionally records `id`, `narrator`, Arabic `grade`/`attribution`, and `quotation_mode` (`quotation` or `paraphrase`). Requested-language records may supply `grade_translated` and `attribution_translated`. HadeethEnc lacks individual translator metadata: `translator: "HadeethEnc"`, `translator_status: "not_specified"`. Dorar records retain `record_id`, `link_status` (`direct`/`search_only`), `search_url`, and optional `origins_url`; HadeethEnc's separate `verification` object can record Dorar evidence.

Literal attachment requires strict wording matching, including conditionals/pronouns. Paraphrase/related narration linking is explicit (`paraphrase: true`), keeping the speaker's words and translation; it never declares the related narration literal. Connected parts can share `citation_group`; `apply_to_group: true` validates every target before saving, while reviewed/manual/custom-caption parts prevent bulk overwrite. `citation_suggestions` are comparison candidates with their own language/status/provenance, not confirmed sources.

For a related Hadith, `use_source_wording: true` adds `source.subtitle_mode: "source_excerpt"` while preserving `quotation_mode: "paraphrase"`. It keeps Arabic ASR/reference identity/times and stores the current-language speech draft in `speech_translation` / `speech_translation_origin`. Partial source wording requires exact target-language selection. `use_source_wording: false` restores that draft. Mode changes clear review. Video captions distinguish source wording from a related narration; full reference text stays in the source dialog rather than replacing every short subtitle with the full report.

`citation_lookup` reports failed reference discovery (`not_matched`, `unavailable`, `invalid_response`, `suggested`), provider, message and optional HTTP status. Successful/explicitly rejected references clear stale candidates. Retry reuses the saved transcript and existing translations. It never treats source-service failure as evidence of a literal match.

## Explicit retranslation

`POST /api/projects/ID/retranslate`:

```json
{"target_language":"es", "confirm":true}
```

Requires editor access, a saved nonempty transcript, ready/error state, a translation key, a different allowed language and an available job slot. Missing confirmation or incompatible state returns 409; invalid language returns 400. Returns 202 and project JSON; poll the project endpoint.

Before starting, the previous segment JSON is archived privately under `translation-history/OLD_LANGUAGE-TIMESTAMP.json`. Language and reset JSON are committed together. Existing Arabic, word timings, verified Arabic identity and quotation/paraphrase/source-wording choices remain. Target text, translated metadata, source translation/selection, speech-translation backup, quality hashes, approval, custom viewer caption and suggestions are cleared. References carry `reference_preserved` and are refreshed by the same source identity, independently of new model detection. The job never retranscribes the video. Old download tickets fail with 409 after the project revision changes; stale edits are rejected using language and revision guards.

## Endpoints

| Method | Path | Request / result |
|---|---|---|
| GET | `/api/health` | Key-presence and FFmpeg flags, not billing/model readiness |
| GET | `/languages.json` | Shared allowlist, script/fonts, source IDs and viewer labels |
| POST | `/api/projects` | Multipart language then video; 201 project + private edit token |
| GET | `/api/projects/ID` | Editor project JSON |
| POST | `/api/projects/ID/process` | `{}`; 202; resumes saved stages |
| POST | `/api/projects/ID/retranslate` | Explicit language change + confirmation |
| POST | `/api/projects/ID/manual` | `{"segments":[{"start":0,"end":5,"ar":"...","translation":"..."}]}`; replaces transcript in project's language |
| POST | `/api/projects/ID/segments/SEGMENT_ID` | Partial `ar`, `translation`, timing, `reviewed`, `reject_source`, `source_translation_span`, `use_source_wording`, `source_caption`; `dismiss_gap:true` removes a gap cue |
| POST | `/api/projects/ID/quran/SEGMENT_ID` | `{"surah":2,"ayah":222}`; Arabic match + target source; unreviewed |
| POST | `/api/projects/ID/hadith/SEGMENT_ID` | `{"hadith_id":"123","paraphrase":false,"apply_to_group":false}`; unreviewed |
| POST | `/api/projects/ID/style` | Font/size/color/backdrop/bilingual/position |
| POST | `/api/projects/ID/title` | `{"title":"..."}` |
| GET | `/api/projects/ID/video` | Original Arabic video, single byte range supported |
| GET | `/api/projects/ID/subtitle/SEGMENT_ID` | Shared RGBA subtitle PNG, optional style query overrides; editor or reviewed project |
| POST | `/api/projects/ID/export/KIND` | `{}` prepares `srt`, `mp4`, `sources`, `sources-draft`; expiring ticket |
| GET | `/api/projects/ID/export/{srt,sources,mp4}` | Legacy direct exports, same project language/review policy |
| GET | `/api/downloads/TICKET` | Attachment/byte range; invalidated on any project revision, expires after 600 seconds |
| GET | `/api/share/SHARE_TOKEN` | Reviewed read-only project, includes target language |
| GET | `/view/SHARE_TOKEN` | Read-only viewer |
| DELETE | `/api/projects/ID` | Deletes project/files; blocked during processing |

All editing/export-preparation endpoints require `X-Edit-Token`. Transcript edits are blocked during processing; stale language/revision writes cannot overwrite a new project state. Private SRT/MP4 drafts are allowed with warnings. Public sharing requires explicit review of all segments and resolved citation/alignment decisions.

## Captions, rendering and source lists

`source_caption` is optional editable viewer text, separate from provenance; empty string hides it, null restores the default. It uses the target language by default and resets on language changes. It is a single line, maximum 200 characters. Canonical metadata remains in the source list even when the viewer line is hidden.

Viewer labels in `languages.json` identify Quranic meaning translation, related narration, source wording, draft/editor alternatives, unavailable translation and grading availability. English chapter names come from `source-caption-labels.json`; other languages use localized Quran labels and numeric verse locations. Unknown Arabic grading is not guessed or labelled English in another language.

`style` accepts bundled font ID, integer size 10–42, `#RRGGBB` color, boolean `backdrop`/`bilingual`. Position is bottom. The chosen Arabic font renders the quote; target script selects a bundled Noto family with Latin/Plex fallbacks. Urdu uses bidi shaping, Hindi Devanagari shaping, Chinese explicit character breaks. `BorderStyle=4` covers combining marks in a continuous padded backdrop. `shared-png-v10-multilingual` caches include language, content, style and dimensions; MP4 uses exact preview image bytes and fitted size. MP4 files/manifests and downloads include language. SRT supports Unicode/text/timing, not enforced player styling.

Confirmed `sources` is a JSON array of reference objects with spoken start/end; language, translator, publication status and URLs stay with each entry. A reviewed alternative does not change an unavailable source into a published translation. `sources-draft` contains `status: "draft"`, `target_language`, a localized `notice`, and `citations` with segment timing/review/source/candidate/lookup/suggestions. Private snapshots, edit tokens and uploaded video filenames are never exposed in these inventories.

See [language/source coverage](languages.md) and [multilingual verification](verification-multilingual-2026-10-06.md) for actual source limits and test evidence. AI alignment/review is assistance, not scholarly approval.
