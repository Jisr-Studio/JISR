# Sources, tools, and components working register

> October 6 release update: the actual translation provider is OpenAI GPT-6 Luna, transcription is ElevenLabs Scribe v2, and Quranpedia/HadeethEnc use the seven verified language mappings in [language/source coverage](../languages.md). The ten bundled subtitle fonts have adjacent SIL OFL notices and exact source links in [the font manifest](../../dist/fonts/README.md). The current release checks are in [final delivery](../final-delivery-check-2026-10-06.md). License/permission decisions left blank below have not been invented by this technical audit.

Anas completes AI/reference entries. Turki completes code, media, fonts, and hosting. This is a working register; license verification is not complete. Fill dates and exact applicable terms before releasing or packaging material.

## Content sources

| Source | How Jisr uses it | Evidence / attribution | Remaining action |
|---|---|---|---|
| [Quranpedia](https://quranpedia.net/api-docs) | Hafs text matching; English translation identified as Saheeh International, book 1947 | Source URL, verse identity, translator; explicitly named on supplied package page 3 | Verify terms; resolve page 11's approved-translation emphasis with mentor and record selected provider/translation |
| [Dorar](https://dorar.net/) | Hadith candidates and reported grading/attribution; retrieved tafsir | Keep original provider metadata and tafsir section scope | Record terms and attribution for each use; do not infer redistribution permission from connectivity |
| [HadeethEnc](https://github.com/islamhouse-dev/hadith-api) | Hadith English translation/explanation where a matching record exists | Preserve record ID, translation URL, and separate Dorar verification; explicitly listed on supplied package page 9 | Verify API/content terms and record attribution; listing does not guarantee every automatic match |
| [Al-Jamhara](https://islamic-content.com/dictionary) | Retrieved terminology definitions and available English equivalents | Keep exact entry links and missing-match status | Verify terms and explain that definitions guide a machine draft |
| [Supplied scientific package](../hackathon/scientific-sources-package.pdf) | Content boundaries, named sources, and terminology guidance | 15 pages; core sources pages 3–4, output standards page 5, glossary page 7, expanded sources pages 8–15 | Retain the received version and distinguish it from the earlier package's page numbering |
| QuranEnc / TerminologyEnc / ICADB, listed in supplied package | Candidate approved translations/terminology resources | QuranEnc page 9; TerminologyEnc and central database page 10 | Assess only the specific gap needed for Jisr; no integration or live connectivity is claimed |

The existing docs/source-check.json contains sample connectivity results. Source reachability does not establish content accuracy or permission to redistribute a corpus. Jisr's register should describe actual use rather than claim approval of all records.

## Runtime, models, and external services

| Component | Current role | What to document for release |
|---|---|---|
| Python standard library | HTTP, storage, processing orchestration | Release Python version, runtime license/reference, setup instructions |
| SQLite | Server project persistence | Runtime version where relevant, bundled-use attribution, storage behavior |
| FFmpeg / libass / codecs | Video probing and burned-in subtitles | Exact host build/version, license/build configuration, enabled codecs/fonts, operating requirements |
| ElevenLabs Scribe v2 | Speech transcription with word timestamps | Exact model/API, dated service terms, uploaded-media handling, measured charge |
| Selected translation provider | Translation/classification, terminology refinement, quote-excerpt selection | Provider/model/version, official API docs, applicable terms, data handling, cost, quotas, configuration keys |
| OpenAI, current implementation | Translation, classification, terminology review, and source-excerpt alignment | Document the configured model and retain separate source translations; Gemini is historical only |
| Caddy / container images | Optional hosted HTTPS/deployment | Shipped image versions, applicable licenses, infrastructure cost |
| IBM Plex Sans Arabic / Amiri | Frontend typography; rendering fonts may differ | Actual font source and license, attribution/bundling requirements; verify exported Arabic rendering |
| Google Fonts | Browser font delivery in dist/index.html | External dependency and actual font-use terms; record whether fonts are fetched or bundled |

Do not copy values from .env into this register. Configuration examples contain blank keys only.

## Team code and media

- Project source: Turki/Anas confirm authorship, any reused components, and the license they choose for team-owned code. No tracked project LICENSE was found on October 3; do not assign a license without team agreement.
- Existing silent demo and illustrative segments: record origin and permitted use. Label them as interface examples; they are not evaluated live-provider output.
- Evaluation and presentation clips: record creator/source, permission or applicable license, dates, allowed display/release scope, and whether they meet the organizer's data requirements. Public availability alone does not establish reusable rights.
- Screenshots/recordings: use the team's app and permitted clips. Record any third-party material visible in them.
- Logo/identity assets: distinguish team-created Jisr assets from organizer marks; follow the supplied identity guidance.

## One record to fill per component

```text
Component / content:
Owner or provider:
Version / model / record ID:
Used for:
Official documentation URL:
Applicable license/terms URL:
Terms checked on:
Attribution required / where displayed:
Stored locally / displayed / bundled / redistributed:
Media or data permission evidence, where applicable:
Release decision / unresolved issue:
Responsible team member:
```

Keep this register with the release documentation. Maintain private permission evidence privately when it contains personal details; the public record can summarize the permission without exposing them.
