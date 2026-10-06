# Multilingual verification — October 6, 2026

## Scope and result

The current application supports one target language per project: English (`en`, default), Spanish (`es`), Urdu (`ur`), Hindi (`hi`), Indonesian (`id`), Simplified Chinese (`zh-Hans`) and Turkish (`tr`). The editor remains Arabic. No paid transcription or translation requests were made for this verification.

The final Python run completed **206 tests: 205 passed and one platform-specific test skipped on Windows**. The four JavaScript suites passed: canonical citation/edit saving, citation links, subtitle preview cache/retry/races/gaps, and the seven-language presentation policy.

## Automated checks

- Upload language validation, persistence, reopening, default English and lossless/idempotent migration of old English fields, including editor text, approvals, source selections and word timestamps.
- Language propagation through translation, a failed partition followed by retry, grounded terminology, meaning review and exact source excerpt alignment, using mocked API responses.
- All seven Quranpedia book/language mappings and HadeethEnc codes, missing published translations, per-record availability, preserved Arabic reference identity, and rejection of English excerpt selections in another language.
- Explicit confirmed retranslation without calling transcription; cleared approval, translated selections and captions; retained Arabic words/times and source identity; private history; stale revision and download-ticket rejection.
- Actual local HTTP upload, edit/review, reopen, share, SRT download, subtitle PNG generation, MP4 rendering and MP4 download/decode for each language. These use a synthetic two-second video and mocked service data. The exported subtitle cue image is byte-identical to the preview image for the same cue/style.
- Unicode SRT, Urdu bidi markers, script-specific font selection and bundled glyph coverage, SIL OFL notices, Arabic diacritics, visible subtitle content without clipping, CJK line wrapping and reading heuristics, and separate language/artifact cache identities.
- Existing citation, source-wording, export, upload, access control and subtitle rendering regressions.
- Docker build-context checks ensure local Python dependencies, the language catalog and script fonts are included while secrets/private data are excluded. Docker is unavailable on this Windows host, so no container image was built here.

Run locally with Python and FFmpeg available:

```bash
python -m unittest discover -s tests
node tests/test_citation_text.js
node tests/test_citation_links.js
node tests/test_subtitle_preview.js
node tests/test_languages.js
```

## Browser checks

A separate disposable local server used only synthetic video and mocked AI/source responses. Browser checks covered:

- Reopening an Urdu project, with its selected language retained, RTL translation text and the Nastaliq font in the studio and editing dialog.
- Explicit confirmation before switching to Chinese; the completed project showed Chinese text with LTR direction and the CJK font.
- Selecting Hindi before uploading a video through the actual file chooser; upload persisted Hindi and processing displayed Hindi subtitles.
- Export warnings for an unreviewed project, enabled SRT/MP4 draft export, and disabled public sharing until review.
- Downloading the Hindi SRT and MP4 through the application's export controls; decoding that downloaded MP4 with FFmpeg without errors.

The user's existing local project was compared with its private pre-migration SQLite backup: all 15 segments retained their Arabic, edited translation, word timestamps, review status and project style/access tokens. The migration was idempotent.

The rebuilt deployment ZIP passed an entry/hash audit and a scan against the locally configured credential values without printing them. It includes the catalog, language module, fonts/licenses and updated contracts/reports; it excludes local projects, private uploaded videos and credentials. The existing silent `dist/demo.mp4` remains as a public demonstration asset.

After restarting the current app on port 8766, the read-only deployment smoke check passed for health, configured-key presence, the language module/catalog and all four script fonts, including the CJK OTF MIME type. Key presence does not establish live provider permission or model quality.

## Published-source checks

Free public API checks on this date retrieved Quran 1:1 from all seven selected Quranpedia translation books and Hadith 3636 in all seven HadeethEnc languages. The provider catalogs and API documentation were checked against the configured IDs. This verifies these records and mappings, not complete corpus coverage.

See [languages and source coverage](languages.md) for the exact mapping, translator attribution, official documentation links, font licenses and missing-translation behavior.

## Limits of this verification

- Multilingual model accuracy has not been assessed with paid requests or native-language religious reviewers. Mocked prompts/flow and local rendering are verified; religious approval is still a human responsibility.
- A language in a provider catalog does not mean every reference has a published translation. Unavailable/failed fetches are marked explicitly; alternative machine/editor text is labelled separately and never promoted to published source text by approval.
- The Chinese providers expose generic `zh`. The checked samples use simplified characters; there is no separate provider `zh-Hans` endpoint or whole-corpus script certification. Source text is not converted by AI under source attribution.
- HadeethEnc does not expose the individual translator's name. That absence is stored explicitly instead of inventing an attribution.
- Reading limits are review heuristics. Long quotations may still need a person's segmentation/timing review; the system does not discard words to shorten them.
- SRT cannot enforce a viewer's font/size or bidi support. MP4 embeds the same rendered subtitle images as the preview and retains the original audio.
