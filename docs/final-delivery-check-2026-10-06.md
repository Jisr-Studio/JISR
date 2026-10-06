# Final delivery check — October 6, 2026

## Decision

The current **source files are ready for the team's final push**. This does not mean every organizer submission artifact or the current public deployment is complete. Use the clean source package, then deploy and verify the latest commit before submitting the live link.

## Verified local release

- Active backend: `server.py`, `pipeline_quality.py`, `subtitle_png.py`, `languages.py`; the archived FastAPI prototype is not the running app.
- Seven languages: en/es/ur/hi/id/zh-Hans/tr; upload selection, saved language, explicit retranslation without ASR, neutral fields, legacy migration, source-language availability and exact excerpt selection.
- Arabic editor, Urdu RTL, bundled script fonts and OFL notices; shared subtitle PNG rendering for preview/MP4; language-aware artifacts, SRT, sources and sharing.
- Final Python discovery: **210 tests, 209 passed and one Unix-only module skipped on Windows**. Four JavaScript suites and active JavaScript syntax checks passed. Provider transports are mocked; actual local FFmpeg export/decode is exercised.
- The local read-only deployment checker passed health, configured-key presence, JavaScript/catalog, all four target fonts (including CJK OTF), and demo video.
- Read-only inspection of the three current user projects found 46 nonempty translated segments, no project/source language mismatches, and preserved reference metadata. This is a data consistency check, not human approval of their meanings. No user project was changed or auto-confirmed in this final audit.
- No paid AI requests were made during this final audit. Earlier real English checks and the current multilingual mock/browser checks are documented separately in the dated verification reports.

## Push contents and private files

`python scripts/package_source.py` creates **submission/deployment/jisr-final-source.zip**, containing the source, tests, documentation, blank `.env.example`, fonts/licenses and a SHA-256 manifest. Extract its contents into the repository; do not upload only the ZIP as a substitute for a browsable source repository.

The source/package scan found no configured API-key values or current private editor tokens in candidate source files. Private projects/uploads, `.env`, logs, work folders, virtual environments, Python caches, Git metadata and generated ZIPs are excluded. The only packaged videos are the existing silent illustration in `dist/` and its archived prototype demonstration. No source candidate exceeds 50 MiB.

`python scripts/package_demo.py` rebuilds the smaller runtime-only deployment ZIP. Docker includes the language module/catalog/fonts; dependency/context regression tests passed. Docker itself is unavailable on this Windows machine, so the image build remains a hosting check.

This folder has **no project `.git` directory**. Its actual remote, staged files, commit or Git history cannot be validated here. Do not force-add ignored private files. The GitHub API confirmed [turki125/JISR](https://github.com/turki125/JISR) is public with `main` as its default branch; this does not prove the local final files have already been pushed.

The current public `main` tree was also checked: 131 tracked files, no `.env` or private `data/`/SQLite paths found. `languages.py` and `dist/languages.json` are absent there, so the new language feature still needs this final push. This path check is not a full historical-secret scan or a check of a future staging area.

## Public deployment

Read-only checks against [the existing Render host](https://jisr-3ue4.onrender.com/) returned:

| Check | Observed result |
|---|---|
| `/api/health` | 200; FFmpeg and both provider keys configured |
| `/languages.json` | 404; current multilingual files are absent from this deployment |

The checked host is older than this release. `render.yaml` uses `plan: free`, no disk and `autoDeployTrigger: "off"`. After pushing, choose **Manual Deploy → Deploy latest commit**, verify the build/revision and rerun `scripts/check_deployment.py` against the HTTPS root URL. A Git push by itself does not update this configuration.

Complete a fresh hosted upload/review/MP4/SRT/source/share workflow before giving judges the updated link. This paid-provider exercise requires the team's authorization and was not run in this audit. Free storage is temporary: a saved viewer link cannot be promised to survive sleep/restart/redeployment. See [deployment instructions](deployment.md).

## Submission materials still absent here

The [organizer requirements recorded from the supplied guide](team-preparation/README.md) include the working live link, public source repository, operating/source documentation, final PDF/PPTX presentation and a demonstration video of at most two minutes.

This workspace contains drafts, a recording script and the organizer's empty presentation template. **No completed Jisr presentation or final two-minute demonstration recording was found in this folder.** If prepared elsewhere, attach those actual final files in the submission portal. Also record the pushed/deployed revision and portal confirmation in `submission/README.md`; neither can be invented before those actions occur.

The font notices and language/source register are present. The team has not supplied a project `LICENSE`; do not claim the team code is MIT/OFL merely because a dependency uses that license. The component register distinguishes font licenses, provider/content terms and team-owned material.

## Content limits to present honestly

Published translation availability is per reference, not guaranteed by a provider's language catalog. Chinese providers use generic `zh`; the checked samples are simplified, without a separate whole-corpus `zh-Hans` certification. HadeethEnc does not expose an individual translator. Missing translations and machine/editor alternatives remain distinct. Neither automatic matching nor a configured key replaces human religious/translation review. See [language/source coverage](languages.md) and [multilingual verification](verification-multilingual-2026-10-06.md).
