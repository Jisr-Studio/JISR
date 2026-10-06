# Final Pull_7 delivery audit — October 6, 2026

## Decision and scope

The audited code is runnable from an isolated source package. Complete committee delivery still needs the team to deploy this final revision, run the authorized real-provider workflow on that host, and review the demonstrated religious content and translations. This audit does not declare religious approval or a paid multilingual accuracy benchmark.

The final presentation and explanation video are submitted externally, as confirmed by the team; their absence from the code ZIP is intentional. Their finished contents were not inspected. No team-code license is added. No push, deployment, submission or paid AI request was performed.

## Requirements and evidence

**متحقق** means verified within the stated test scope. **جزئي** identifies an actual remaining condition. **غير متحقق** means no successful execution/evidence in this audit. Official requirements come from the participant guide, printed pages 31–33, and scientific package, pages 3–5, 7, 9 and 11. Product requirements also include the team's seven-language and draft-export decisions; they are not all organizer mandates.

| Requirement | Origin | Status | Evidence / limitation |
|---|---|---|---|
| Runnable complete code and startup instructions | Official | متحقق محليًا | Extracted ZIP; no-pip isolated Python 3.12.14 environment; blank `.env`; standalone installed FFmpeg; vanilla startup and fresh SQLite database. No application dependencies outside the extracted folder. |
| Python/FFmpeg/dependencies/fonts | Product / delivery | متحقق ضمن البيئة المختبرة | Standard library only; FFmpeg 7.1 GPL/version3, libx264/libass/Fribidi/HarfBuzz; ten bundled fonts/OFL notices. Declared Python minimum 3.11, tested 3.12.14 only. |
| Blank safe configuration | Official / product | متحقق | `.env.example` has empty provider keys; health reports availability only; automatic processing requires valid provider accounts. |
| Fresh DB and old-schema upgrade without lost edits | Product | متحقق | `test_database_upgrade.py`: language column created, all seven stored; legacy English edits, words/timing, tokens, style/title/review preserved; idempotent upgrade; interrupted job recovery. |
| Arabic upload, selected language persisted and reopened | Product | متحقق | Seven-language HTTP round trips, real HEVC upload for every language; browser upload and re-open; server allowlist validation. UI requires explicit choice; missing legacy/API language defaults to English. |
| Arabic Scribe v2 and word timing | Agreed / official AI role | جزئي | Mock transport verifies streaming `scribe_v2` request and exact timestamps. Historical real-provider reports retained; current account access/audio accuracy not retested using paid services. |
| Speaker translation, terminology, retries, meaning check in target language | Product | متحقق تقنيًا بالمحاكاة | Language policy tests cover target language across each stage, repair/retry, exact word partitioning and separate meaning review. Paid model output quality remains unverified. |
| Separate speech / Quran / Hadith | Scientific / product | متحقق تقنيًا بالمحاكاة | Full HTTP mixed-transcript integration and browser run produce separate cues and references without dropped words; uncertain speech gets visible review flags. Detection accuracy on arbitrary real audio is not certified. |
| Canonical Arabic source and corresponding translation excerpt | Scientific / product | متحقق تقنيًا | Exact source substring/alignment tests, Quran-boundary and Hadith-wording regressions, direct record evidence; source body is retrieved, never generated as scripture. |
| Published source vs machine/editor draft; unavailable translation | Scientific / product | متحقق | Tests cover failed/empty language source, retained Arabic identity, no English fallback, explicit labels/status/provenance. Partial selections are scoped to target language. |
| Sources actually accessible, seven mappings correct | Scientific / product | متحقق للعينة | `public-source-check-final.json`: seven public-service samples succeeded. `public-language-sources-final.json`: Quran 1:1 and Hadith 65004 sourced in all seven target languages. This is not whole-corpus coverage. |
| Approved source emphasis on association translations | Scientific page 11 | جزئي | HadeethEnc integrated; Quranpedia is named on page 3 and is the current Quran translation provider. QuranEnc prioritization is not implemented. Team must resolve preferred Quran translation policy and disclose the current provider. |
| Substantive religious claims and qualified content review | Scientific pages 3–5 | جزئي | Quotations/terminology traceable and review required; ordinary-speech claims are not independently source-checked. Native-language/religious review of the final demonstration remains necessary. |
| Literal vs paraphrase vs source wording | Product / scientific | متحقق تقنيًا | Strict conditional/pronoun matching; explicit related-reference/source-wording modes; canonical Arabic separated from preserved ASR; source suggestions never auto-confirmed as literal matches. |
| Edit Arabic/translation/time/source caption and save/reopen | Product | متحقق | Browser edited speech translation, end time and viewer source caption; reload retained changes. Source/timing APIs and stale-edit tests protect reference integrity. |
| Uncaptured speech/audio-gap correction or dismissal | Product | متحقق تقنيًا | Real synthetic tone triggers missing-transcript cue; editor now exposes non-speech dismissal with explicit confirmation; original audio preserved. Speech-detection accuracy is a heuristic. |
| Explicit language change without ASR, stale cache/approval isolation | Product | متحقق بالمحاكاة | `test_languages.py` forbids transcribe on retranslation, checks unchanged Arabic word timing, archived previous edits, approval/selection reset, invalid old downloads and stale writes. |
| Video preview, original preserved, black-screen regression | Product | متحقق | HEVC fixtures converted to H.264/yuv420p + AAC-LC; 206 range checked; original SHA-256 unchanged for each language; browser readyState 4, no media error, playback advanced. Five playback cache/failure tests. |
| Script direction/fonts/shaping/wrapping/no tofu | Product | متحقق للعينة | Urdu RTL DOM and SRT marker; glyph coverage of samples/labels; real ASS renders for all seven; visually inspected Urdu, Hindi and Simplified Chinese MP4 frames. Every possible input glyph is not guaranteed. |
| Preview/MP4 same font/size/cues | Product | متحقق | Shared RGBA preview-image bytes equal render-manifest image bytes in integration tests; browser size42/Amiri preview compared with downloaded MP4 frame; same fitted text/background. SRT player styling is outside its format. |
| MP4/SRT/source JSON and private draft policy | Product | متحقق | Actual browser downloads opened/read; all seven real synthetic audio/video MP4 files fully decoded; Unicode SRT checked; two-reference JSON opened. Private export warnings remain and draft export does not mark review complete. |
| Public viewer review gate and read-only access | Product / scientific | متحقق محليًا | Unreviewed sharing blocked in tests/disabled in browser; synthetic confirmation enabled viewer; separate browser tab opened without edit controls/token; source details retained. |
| No user data/secrets in source ZIP, safe Git exclusions | Official | متحقق للحزمة / جزئي لـGit الفعلي | Guard scans configured credentials plus SQLite edit/share capabilities; excludes .env/data/work/DB/cache/binaries/ZIPs/old prototype. No standalone project Git root here: the working folder resolves to an unrelated ancestor repository. A fresh scratch Git root verified that .env/data/work/venv are ignored and .env.example is publishable; the final team repository staging/history is not attested. |
| Delivery cleanup without deleting user originals | Agreed | متحقق | Archived prototype and duplicate submission screenshots excluded from ZIP, not deleted from workspace. Only `dist/demo.mp4` is allowed media. Required fonts, frontend assets and referenced README screenshots retained. |
| Documentation/component terms/source coverage | Official / agreed | متحقق مع حدود موثقة | README, contract, deployment/review guides, third-party register, font notices, source coverage and final receipts. General redistribution rights for Dorar/Al-Jamhara content were not established; no corpus is packaged. |
| Exact manifest/inventory | Delivery | متحقق | `package_source.py` writes identical root/ZIP manifest. `verify_release.py` verifies every entry/hash, forbids unsafe/private paths and checks required runtime files. Final package re-extracted for acceptance. |
| Linux/Docker image execution | Deployment | غير متحقق | Docker unavailable on this Windows host; static Docker import/context tests pass, Unix privilege module skipped. Hosting build and container execution still need observed success. |
| Open live demo and current final deployed revision | Official | جزئي | Existing HTTPS health/catalog returned200 and seven languages. Hosted app.js lacks this delivery's portable-preview fix. Final revision not pushed/deployed in this task; hosted paid pipeline not exercised. |
| Public source repository | Official | جزئي | GitHub API reports `turki125/JISR` public, main=`0ee83846f504a63f7a1b1cdb44aa21980abf8fb3` at inspection. Final audited package is not yet in that observed revision. |
| Final PDF/PPTX presentation and ≤2min explanation video | Official | جزئي / تسليم خارجي | User confirms separate submission outside code files. Actual final deck/video not inspected; no claim of completed content/length here. |
| Portal submission and confirmation | Official | غير متحقق في هذا العمل | Team action; explicitly not performed. Deadline in supplied guide: October6 23:59 Riyadh. |

## Repairs completed

1. Restored the missing portable playback implementation from Pull_6 without replacing Pull_7's appearance, onboarding and export changes. Original files stay unchanged; conversion cache is atomic, versioned and retryable. Frontend displays preparation/error/retry rather than a silent black frame. Preview encoding honors the configured FFmpeg thread limit.
2. Corrected a Quran translation link incorrectly labelled as Hadith translation.
3. Prevented draft export from completing the human-review workflow step.
4. Exposed the already-supported non-speech audio-gap dismissal in the editor with explicit confirmation.
5. Added fresh/legacy SQLite upgrade coverage, restored five playback tests and added packaging/editor workflow regressions. Fixed read-only packaging SQLite handles to close explicitly on Windows.
6. Source/runtime packagers share private-data guards; archived prototype/duplicate submission screenshots excluded; SQLite capabilities cannot appear in packaged docs; root/ZIP manifest synchronized; independent ZIP verifier added. No user project/media deletion.
7. Updated contradictory export/source policy, glossary page7, public-deployment observations, startup/contract/review instructions and external notices. Historical reports remain identified as historical.

## Test evidence

- Python: **221 discovered, 220 passed, one Unix-only module skipped**. Run once in the working source and again from the extracted candidate, then against the final ZIP extraction. Actual FFmpeg tests run; paid/source transports in automated suites are mocked.
- JavaScript: six suites (`citation_links`, `citation_text`, `subtitle_preview`, `languages`, `workflow`, `gap_editor`); syntax checked on all active scripts.
- Isolated environment: Windows, Python3.12.14, SQLite3.53.1, empty-key .env, virtualenv created with `--without-pip`, user packages disabled. FFmpeg supplied as an installed standalone dependency in PATH, outside the app; no old-project/application path used.
- Strict browser harness imports only the extracted package's application/tests. External API transport rejects unknown destinations. Synthetic timed mixed transcript: one ASR request, ordinary speech, partial verse, partial Hadith and an intentionally untranscribed tone. None of these fixtures is a real religious accuracy approval.
- Browser: upload/language selection, processing, reference dialog, translation/time/caption edits and reload, size42/Amiri, actual MP4/SRT/JSON download, gap dismissal, review and separate read-only viewer. Native-download waiting timed out once for JSON, but the actual file was present and successfully opened/validated; it was not a server export failure.
- Actual HEVC/audio acceptance: all seven uploads → H.264/AAC preview/range → manual Unicode caption → MP4/SRT. Original hashes retained, full audio/video decode succeeded; Urdu/Hindi/Chinese export frames visually inspected. No paid AI invoked.
- Free live reference checks: seven service samples plus published Quran1:1/Hadith65004 in all seven languages. A deliberately mismatched Hadith ID/text was rejected during sample preparation; the corrected matching record was then checked. This rejection is not treated as a source outage or matching failure.
- Read-only hosting/repository inspection only. Health initially timed out while Render woke, then succeeded. Configured keys do not prove quota/permissions or actual output quality.

Evidence logs, downloaded exports and test projects are retained outside the delivery ZIP under the review work folder. Current user projects and originals were not modified or auto-confirmed.

## Delivery contents and tried startup

Primary deliverable: `submission/deployment/jisr-final-source.zip`. It includes active Python modules, HTML/CSS/JS, demo and fonts/notices, tests, scripts, docs/organizer references, safe editor configs, deployment files, blank `.env.example` and the matching `release-manifest.json`. The runtime ZIP is optional; it omits tests/editor/submission working files. Use the full source ZIP for a browsable code repository, not a ZIP-only repository.

1. Extract into a new directory; install Python3.12 and FFmpeg with libass/libx264 in PATH. Run `ffmpeg -version` and verify those enabled components. Node is only needed for JavaScript tests.
2. `Copy-Item .env.example .env` (PowerShell) or `cp .env.example .env` (POSIX). Keep keys blank for demo/manual checks; add valid keys privately for automatic processing.
3. `python server.py`; open `http://127.0.0.1:8766`. Fresh DB is created automatically; legacy DB upgrade runs at startup. Alternate audit ports do not change defaults.
4. `python -m unittest discover -s tests -v`, then the six Node suites documented in README. `python scripts/verify_release.py submission/deployment/jisr-final-source.zip` verifies a rebuilt delivery package.

## Remaining conditions

- Deploy the audited package, observe its Docker build/revision, and run one authorized real-provider mixed-video/review/download/viewer trial on HTTPS before relying on the public judging link.
- Review demonstrated Arabic references, published excerpt selection, meaning, pronunciation/timing and target-language translation with appropriate human expertise. No all-seven-language paid-quality certification is claimed.
- Resolve page11's preferred Quran translation source policy; current Quranpedia and unavailable/per-record/generic-zh limitations are documented.
- Free Render storage is ephemeral: upload/project/viewer survival is not promised across restart/redeploy. There is no backup service.
- Team completes its external presentation/video and actual portal submission, records final public commit and deployed revision. Their absence from code is expected.
