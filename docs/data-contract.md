# Jisr API and data contract

JSON uses UTF-8; timestamps are seconds from the start of the video. The API shares the frontend's origin. Errors use `{"error":"message"}`.

## Editor access

Upload returns an `edit_token` once. Send it in the `X-Edit-Token` header for editor operations. Keep it out of public links and logs. The frontend saves it in browser local storage and can recover it from `/?project=ID#edit=TOKEN`. There are no accounts.

## Project

```json
{
  "id": "32-character-hex-id",
  "title": "Video title",
  "filename": "original.mp4",
  "status": "ready",
  "error": "",
  "stage": "Ready for review",
  "duration": 48.0,
  "created": 1790876907.0,
  "updated": 1790876908.0,
  "segments": [],
  "style": {},
  "publishable": false,
  "exportable": true,
  "export_warnings": ["توجد مقاطع لم تكتمل مراجعتها"],
  "video_url": "/api/projects/ID/video",
  "share_url": "/view/SHARE_TOKEN",
  "editable": true
}
```

`status` is `uploaded`, `processing`, `ready`, or `error`. `ready` means processing finished; it does not mean review passed. Use `exportable` for private SRT/MP4 and `publishable` for public sharing. Exportable projects have nonempty segments and status `ready` or `error`; uploaded/processing projects remain unavailable for file export. Show localized `export_warnings` for unresolved review, missing translation, unresolved partial alignment, or incomplete processing. Export does not change review decisions. `stage` and `error` are display text, not identifiers. Poll the editor project endpoint during processing. There is no project-list endpoint.

## Segment

```json
{
  "id": "12-character-hex-id",
  "start": 1.25,
  "end": 5.0,
  "type": "speech",
  "ar": "Arabic transcript",
  "en": "English translation",
  "needs_review": false,
  "reviewed": false,
  "source": null
}
```

- `type`: `speech`, `quran`, or `hadith`.
- `unclear_words` (optional): objects containing `text`, `start`, and `end`, with optional `reasons` (`low_confidence`, `unfinished_word`, `long_word_timing`). These are review hints, not automatic corrections or proof of an error.
- `words` (optional): original transcription words with `text`, `start`, and `end`. New automated transcripts retain these for splitting speech from quotations. The model proposes inclusive word ranges; the server derives Arabic and timestamps from the original words and checks complete coverage before saving a batch. Editing Arabic or timing discards this alignment.
- `audio_gap` (optional): sound was detected without transcript coverage. It may be speech, music, or noise. It requires correction or dismissal.
- `candidate` (optional): proposed `kind`, `surah`, `ayah`, or `hadith_query`. It is not a verified source. An unresolved Quran or Hadith candidate needs verification or explicit rejection before confirmation.
- `source`: a matched reference. Linking it removes the candidate and resets `reviewed` to `false` and `needs_review` to `true`. Verification and human confirmation are separate steps.
- `detected_terms` (optional): up to eight technical terms detected per original model item, validated against its Arabic text and assigned only to speech parts containing them.
- `terminology` (optional): dictionary records used to review a speech translation. Each includes `detected_term`, `term`, `provider`, `url`, `definition_ar`, and `status` (`bilingual`, `arabic_only`, or `english_unavailable`). Bilingual records also include `english_term`, `definition_en`, and `english_url`. These are translation guidance, not Quran/Hadith quotation sources or approval of the whole sentence.
- `terminology_warning` (optional): `{"unavailable_terms":["..."]}`. Missing exact dictionary matches flag the segment with `needs_review: true`; reviewer confirmation can accept the draft after manual checking.
- `terminology_edited` (optional): the editor changed the English after dictionary review. Original dictionary provenance remains for reference; changing Arabic clears the detected terms and all dictionary metadata. Linking a scripture quotation also removes them.

Quran sources include `kind`, `title`, `surah`, `ayah`, `arabic`, `english`, `translator`, `url`, `partial`, `explanation_url`, and `explanation_status`. Dorar tafsir may also supply `surah_name`, `explanation`, `explanation_source`, and `explanation_scope`. The commentary covers the source's indexed verse section, which may include adjacent verses; display its scope alongside it. It is source text, not model-generated explanation. If retrieval fails, `explanation_status` is `unavailable`, the source link remains, and no explanation is fabricated.

Hadith sources include `kind`, `title`, `arabic`, `english`, `narrator`, `grade`, `attribution`, and `url`. HadeethEnc may also supply `id`, `partial`, `explanation`, and `translation_explanation`; Dorar results may include `scholar`. Dorar English remains a machine draft requiring review. Do not infer attribution or approval from a generated translation.

New Hadith sources also record `translation_status` (`sourced`, `machine_draft`, or `unavailable`) and `explanation_status` (`available` or `unavailable`). Sourced HadeethEnc translations include `translator` and `translation_url`. Automatic matching records `translation_lookup_status`: `matched`, `ambiguous`, `not_found`, `unavailable`, or `too_many_candidates`. A unique complete record must match both the transcript and Dorar's Arabic text; a failed candidate lookup prevents a uniqueness claim. Up to eight returned `translation_candidates` contain `id`, `title`, and `url` for manual selection. A larger result set is explicitly flagged rather than selecting from a truncated set.

Automatically attached HadeethEnc sources retain the Dorar record under `verification`, with `provider`, `arabic`, `narrator`, `grade`, `attribution`, `url`, and optional `scholar`. Each provider's attribution and grading remain separate; the model does not synthesize a new judgment. Every source, including an automatically sourced translation, still requires human confirmation before public sharing. Private file export includes a warning when review is unresolved.

Changing a linked citation's Arabic or English removes its reference and flags it for review. Every linked Quran or Hadith citation requires `reviewed: true` before publication. Older records with a source but no human confirmation are also blocked.

Scripture sources retain the full `arabic` and `english` reference texts separately from `subtitle_arabic` and `subtitle_english`. `alignment_status` is `full` for a complete quotation, `matched` for a model-selected verbatim excerpt, `selected` for an editor-selected excerpt, or `needs_selection` when a partial quotation is unresolved. Partial quotations require both excerpt fields and `matched`/`selected` status before publication, including older records. Source text is never replaced with model-generated canonical text. `english_span` contains zero-based, end-exclusive Unicode code-point offsets into the full source English.

For literal Quran/Hadith quotations, the editor, segment list, source cards, and Arabic preview display `source.subtitle_arabic`, falling back to `source.arabic` only for a complete quotation. The original `segment.ar` remains available in the edit dialog for comparison. Saving the displayed source Arabic unchanged sends the original `ar`, so displaying a correction does not invalidate the source link. An actual text edit still invalidates the link. Paraphrases keep the speaker's wording, and an unresolved partial quotation never falls back to the full source text.

`source_caption` is an optional per-segment display override for the attribution line beneath video subtitles. The segment endpoint accepts a single-line string of up to 200 characters; `""` hides the line and `null` restores the automatic label. Editing this field alone preserves canonical source metadata, source URLs, transcript, timing, and review decisions. Preview, MP4, and SRT use the same caption. The JSON sources list continues to contain the original reference. Replacing or removing the reference clears the override. Editing requires the private editor token and a linked Quran/Hadith source.

The editor may send `source_english_span: {"start": 24, "end": 48}` to the segment endpoint. Offsets must select a nonempty source substring; selecting the whole translation for a partial quotation is rejected. If `en` is supplied, it must equal the trimmed selected substring. Arabic must remain unchanged and the source link must exist. This preserves the citation reference and still requires `reviewed: true`; an ordinary free-text English edit removes the reference as before.

## Endpoints

| Method | Path | Request / result |
|---|---|---|
| GET | `/api/health` | Key-presence and FFmpeg flags; not a live-service readiness test |
| POST | `/api/projects` | Multipart field `video`; returns `201`, project, and `edit_token` |
| GET | `/api/projects/ID` | Editor token required; returns project |
| POST | `/api/projects/ID/process` | Editor token; `{}`; returns `202`; poll for completion |
| POST | `/api/projects/ID/manual` | Editor token; `{"segments":[{"start":0,"end":5,"ar":"...","en":"..."}]}`; replaces transcript |
| POST | `/api/projects/ID/segments/SEGMENT_ID` | Editor token; partial `ar`, `en`, `start`, `end`, `reviewed`, `reject_source`, or `source_english_span` |
| POST | `/api/projects/ID/segments/SEGMENT_ID` | Editor token; `{"dismiss_gap":true}` removes an audio-gap segment |
| POST | `/api/projects/ID/quran/SEGMENT_ID` | Editor token; `{"surah":2,"ayah":222}`; source pending human confirmation |
| POST | `/api/projects/ID/hadith/SEGMENT_ID` | Editor token; `{"hadith_id":"123"}`; source pending human confirmation |
| POST | `/api/projects/ID/style` | Editor token; subtitle style fields |
| POST | `/api/projects/ID/title` | Editor token; `{"title":"..."}` |
| GET | `/api/projects/ID/video` | Uploaded video; supports a single byte range |
| GET | `/api/projects/ID/subtitle/SEGMENT_ID` | Exact RGBA PNG used for preview and MP4; editor token or publishable project; optional appearance query overrides |
| GET | `/api/projects/ID/export/srt` | Exportable project; editor token required for an unreviewed draft |
| GET | `/api/projects/ID/export/sources` | JSON list of references eligible for export, with start/end times |
| GET | `/api/projects/ID/export/mp4` | Editor token and exportable project; FFmpeg render |
| POST | `/api/projects/ID/export/KIND` | Editor token; JSON `{}`; prepares `srt`, `sources`, or `mp4` for browser download. SRT/MP4 require an exportable project |
| GET | `/api/downloads/TICKET` | Short-lived attachment download; supports byte ranges |
| GET | `/api/share/SHARE_TOKEN` | Read-only project; requires a publishable project |
| GET | `/view/SHARE_TOKEN` | Read-only viewer page |
| DELETE | `/api/projects/ID` | Editor token; deletes project and files; unavailable during processing |

`reviewed` must be a JSON boolean. Style accepts `font` (`plex`, `amiri`, `cairo`, `tajawal`, `noto-sans`, `noto-naskh`, `system`), `size` (10–42, default 18), `color` (`#RRGGBB`), and boolean `backdrop` and `bilingual`. Subtitles always use bottom placement. Legacy `position` values (`top`, `middle`, `bottom`) are accepted and normalized to `bottom`.

Export preparation returns `download_url`, `filename`, `size` (bytes), `expires_in` (600 seconds), `project_updated`, and `warnings` (localized string array). The browser follows this URL as a normal attachment link, without creating an in-memory Blob or putting the editor token in the URL. Tickets expire after ten minutes, invalidate after project edits or deletion, and disappear on server restart; prepare a new file when needed. The frontend waits for appearance saves before preparing an export and shows preparation failures in the export dialog.

The six named fonts are bundled in `dist/fonts/` for both browser preview and MP4 export. The system option uses the host's Arial fallback. Preview volume is a local player control and does not change the exported audio.

Real-video previews fetch the server-rendered subtitle PNG with the editor token in a header. Query overrides accept `font`, `size`, `color`, and `backdrop`/`bilingual` (`true` or `false`). The response reports `X-Subtitle-Font-Size` (after fitting) and `X-Subtitle-Renderer`. Size is scaled from a 480-pixel logical video width; long cues shrink consistently to fit. Cached images are private to the project and shared with MP4 rendering, which retains native resolution, uses H.264 CRF 18, and copies compatible audio. Gaps between cues display no subtitle. Missing English is explicitly shown as `[Translation unavailable]` in private drafts rather than silently dropping the cue. SRT retains canonical quoted Arabic and source captions even before confirmation, without changing review flags; the JSON sources list still includes only eligible citations. SRT has no font or appearance settings.

The frontend displays the server's warning array before export and alongside a prepared download, including incomplete processing and partial-quotation warnings. Review counters and filters also include missing English, unresolved candidates, unconfirmed citations, and unresolved partial alignment. JSON sources require an actual boolean `reviewed: true`, no outstanding review/candidate, a nonempty translation, and completed excerpt alignment; source metadata cannot overwrite the segment's exported start/end times. Style sizes must be integer values; invalid sizes and non-object JSON requests return `400`.

MP4 subtitle-image timestamps use a millisecond time base, preventing short cues from disappearing through the image demuxer's default 25-fps rounding. Video retains its source frame rate; the image time base does not make it a 1000-fps video. Display dimensions account for sample aspect ratio and 90-degree rotation, and normalize to an even square-pixel canvas for H.264. Interrupted manifest/metadata files are rebuilt. Browser images use a bounded cache and a guarded retry; editing an existing project does not reload its video or reset playback position.

Processing blocks transcript edits, manual replacement, source linking, and deletion. Style and title updates remain available. Missing keys, unresolved review for public sharing, and incompatible states return `409`; invalid input returns `400`; invalid editor access returns `403`; missing records return `404`. Upload and processing limits can return `429`.

## Verification limits

Tests exercise local processing and HTTP flows with mocked external responses. `scripts/check_sources.py` separately checks real public source responses; `source-check.json` records sample connectivity and field availability for Quranpedia, HadeethEnc, Dorar Hadith, Dorar tafsir, and Al-Jamhara. It does not verify the whole corpus. The October 5 six-video audit exercised actual providers and exported media; independent listening, expert meaning review and public deployment verification remain necessary. See verification-2026-10-05.md. This contract documents the current backend; separate upload and processing screens are deferred.

When matched speech terms exist, the server makes a second OpenAI call with the source definitions. Its response must contain every target ID exactly once. The original transcript, timestamps, quotation candidates, and word partitions remain fixed. A failed refinement does not commit that batch's draft translations; completed earlier batches remain available for retry.

## Processing details

OpenAI uses the `v1/responses` API with strict JSON schemas, `store: false`, and the configured model. Translation runs in batches of four original segments, with bounded surrounding transcript context and checkpoints after validated batches. One corrective request may repair invalid output; the original Arabic words and timestamps are preserved. Explicit transient HTTP failures receive at most three attempts. Authentication errors, long quota waits, and uncertain timeouts do not trigger another request or model.

Ordinary-speech parts with indexed words must contain at most 180 English characters. Parts with more than 12 Arabic words must last at most 8 seconds; word-end offsets are supplied for boundary selection. These limits trigger the same bounded repair request as invalid word coverage. They do not apply to scripture matching. Retrying a ready project also accepts oversized unreviewed ordinary speech. Reflow runs on a copy and retains the saved translations if the provider fails; reviewed text and unresolved scripture candidates are excluded.

If a Quran candidate names a surah but omits its verse number, only a unique literal match in that surah's authoritative text can resolve the location. Ambiguous excerpts and explicitly wrong locations remain unresolved. Quran translation HTML is converted to text; verse-number prefixes and documented footnote markers are omitted from subtitles, while source footnotes are retained in optional `translation_notes`. No translation wording is generated by this cleanup.

## Translation provider health

`GET /api/health` reports `translation_provider` (`openai`), `translation` (OpenAI key present), `openai`, `elevenlabs`, and `ffmpeg`. Key-presence booleans do not validate credentials, billing, or model access. Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` (default `gpt-6-luna`). Public project JSON and edit endpoints are unchanged.

### Citation retrieval failures

Unresolved Quran/Hadith candidates retain `candidate`, set `needs_review: true` and `reviewed: false`, and expose `citation_lookup` with `status`, `provider`, and a safe editor-facing `message`. Status values distinguish `not_matched`, `unavailable`, and `invalid_response`; HTTP failures also include `http_status`. The editor displays the message beside the segment. Successful or manually linked references clear this diagnostic. Retrying processing reuses the saved transcription and completed translations.

Hadith literal no-match results trigger up to three HadeethEnc anchor searches and at most three complete-record lookups. Only a unique, complete, literal match without lookup failures attaches automatically. Looser lexical matches produce `citation_lookup.status: suggested` and `citation_suggestions`: an array with `id`, `title`, `arabic`, `english`, `url`, `narrator`, `grade`, `attribution`, and `quotation_mode`. These are comparison choices, not confirmed citations. `citation_suggestion_status` distinguishes `suggested`, `not_found`, and `unavailable`. The editor selects a suggestion through the existing Hadith endpoint, explicitly using `paraphrase: true` for abbreviated wording. Attaching/rejecting a source or changing Arabic clears stale suggestions; no automatic review approval occurs.

Hadith matching ranks the spoken passage inside a full source report. Passage matching uses the existing 0.86 similarity threshold; a one-word difference in token counts additionally requires compatible beginning/end boundaries and at least 0.98 similarity without spaces. This tolerates a near-identical ASR boundary error without absorbing an introduction. The original transcript stays unchanged and human review remains required. A transcription error in a complete quotation does not make it a partial quotation. Longer source reports remain partial and require the correct sourced subtitle excerpt. Failed long queries may use up to two shorter normalized anchors; every result must still pass passage matching and metadata checks. This is source retrieval and validation, not an embedding/vector RAG pipeline.

## Citation destinations

`source.url` identifies the cited record. Dorar references additionally report `link_status` (`direct` or `search_only`), `search_url`, and, when published, `record_id` and `origins_url`. The same fields can appear in a HadeethEnc record's separate `verification` object. A direct Dorar record requires an exact full-text and narrator/scholar/reference/grade match against a published website result; similar words alone cannot select a different scholarly record. Unavailable or ambiguous link lookup retains the citation and an explicitly labelled search fallback.

`explanation_url` points to a retrieved explanation only when `explanation_status` is `available`. `explanation_index_url` is a broader surah index and must be labelled as browsing. Source, translation, verification, origins and explanation destinations are rendered separately. Legacy search URLs are recognised even without `link_status`. A missing narrator marker is displayed as unspecified, never replaced with a guessed narrator.

For existing projects, run `python scripts/refresh_source_links.py` to preview repairs and add `--apply` to save them. This uses public-source requests only. It preserves texts, translations, grading and review flags, skips active processing, and refuses stale writes after concurrent edits.


## October 5 quality and connected quotation checks

Every segment with `reviewed !== true` is pending, including ordinary speech.
Private draft SRT/MP4 remains exportable. A successful AI check is never human
approval. `quality_review` has `status: checked|unavailable` and an `issues` array
of `boundary`, `meaning`, `transcript`, `duplicate` or `not_checked`.
`quality_input_hash` caches checks for unchanged Arabic/English.
`quality_previous_english` retains the first machine draft when a correction is
applied. `translation_origin: human` protects saved text edits from automated
meaning repair. Ambiguous ASR is flagged without silently reconstructing it.
The original Arabic, word timestamps, IDs and canonical source text are preserved.
Editable project JSON exposes boolean `retryable`, computed from the same
eligibility check as the processing endpoint. It shows the retry button on ready
projects with pending automatic work; public JSON sets it to false. Reviewed
text, human translations and custom captions do not qualify for automatic retry.

Meaning checks use batches of at most 12 draft speech cues with neighboring
Arabic as context. IDs, nonempty English, boolean confidence and issue codes
must validate for the entire batch before corrections commit. An unavailable
provider keeps translations and flags `not_checked`; retry does not retranscribe.

`readability` reports `characters_per_second`, `duration_seconds`, and `issues`:
`reading_speed` above the local 25 English characters/second heuristic and
`short_display` below one second. `review_issues` contains safe code/message pairs
for the UI. These checks do not retime words or shorten sourced scripture.
Human confirmation acknowledges warnings; metrics remain available.

Connected unreviewed Hadith candidates, at most eight with no gap over two
seconds, are retrieved as one quotation. Every child must match the same source
before a grouped update commits. `citation_group` identifies its timed parts.
Reviewed/manual/custom-caption/paraphrase segments form boundaries. Source
translations use their own record metadata; a related narration is never
presented as a verified English translation of a different Dorar record.
Competing complete translation records are exposed as comparison suggestions.
Search anchors are evidence for retrieval only; a failed candidate cannot make
another result uniquely verified. Narrator extraction preserves explicit
published attributions, including records containing more than one report.

`POST /api/projects/{id}/hadith/{segment_id}` additionally accepts boolean
`apply_to_group`. With true, the selected record applies transactionally to the
connected group; reviewed/manual/custom-caption parts block a bulk overwrite.
Literal linking requires a match for every child. Explicit `paraphrase: true`
preserves each child's spoken Arabic/English and labels the relationship.
Neither operation confirms human review. Invalid booleans return 400.

`POST /api/projects/{id}/export/sources-draft` is editor-only and returns the
usual expiring download ticket. Its JSON has `status: draft`, `notice`, and
`citations` with `segment_id`, timing, `citation_group`, `reviewed`,
`review_pending`, `source`, `candidate`, `lookup`, and `suggestions`.
The existing `sources` export is unchanged: it contains confirmed citations only.
Draft inventories do not appear on a public unauthenticated export route.

Automatic Quran captions include ترجمة معاني القرآن الكريم and the translator.
Unsourced Hadith English and unreviewed paraphrase subtitles carry an English
machine-draft label. Explicit custom/hidden source captions remain supported.
`shared-png-v4` invalidates earlier images/MP4 caches, fitting long subtitles
approximately into the lower half of the frame. New uploads default to size
24 for portrait, 22 for square and 18 for landscape; saved styles are preserved.
