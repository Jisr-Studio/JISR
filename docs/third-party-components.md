# Third-party components and source terms

Release audit: October 6, 2026. These notices describe external components and content.

## Runtime and assets

| Component | Use | License / evidence |
|---|---|---|
| Python standard library | HTTP, SQLite, JSON, networking, orchestration | [PSF license and bundled third-party notices](https://docs.python.org/3/license.html). Tested interpreter: Python 3.12.14. No pip runtime dependencies. |
| SQLite | Private local project storage | [Public domain](https://sqlite.org/copyright.html). Tested SQLite: 3.53.1, supplied by the test interpreter; installed distributions can differ. |
| FFmpeg | Probe, audio analysis, compatible preview, subtitle images and MP4 | [LGPL 2.1+ with GPL components when enabled](https://ffmpeg.org/legal.html). This application requires libx264 and libass; check the installed build's `ffmpeg -version` configuration/license. Acceptance build: FFmpeg 7.1 essentials, GPL/version3, libass, libx264, libfribidi and libharfbuzz enabled. The source ZIP does not redistribute an FFmpeg executable. Docker installs the distribution's FFmpeg package. |
| libx264 | H.264 encoding | [GPL or separately available commercial licensing](https://www.videolan.org/developers/x264.html). Invoked through the separately installed FFmpeg executable. |
| libass | ASS rendering/shaping | [ISC](https://github.com/libass/libass/blob/master/COPYING). Shaping support depends on the FFmpeg/libass build; verified with the local acceptance build. |
| Caddy (optional deployment) | HTTPS reverse proxy | [Apache 2.0](https://github.com/caddyserver/caddy/blob/master/LICENSE); executable not included in source ZIP. |
| Ten bundled font families | Arabic/Urdu/Hindi/Chinese/Latin glyph coverage | SIL OFL 1.1. Exact source links, families and adjacent license files: [font inventory](../dist/fonts/README.md). Keep these notices with the fonts. |
| Illustrative demo and UI scenes | Demonstration of editor tools | Silent illustrative asset, not a recording of the religious sample text. No uploaded user recordings are packaged. Demo captions are examples and must not be presented as a processed/approved religious video. |

## Remote services and religious content

| Service / source | Applicable reference | Use and limits |
|---|---|---|
| ElevenLabs | [Speech-to-text API](https://elevenlabs.io/docs/api-reference/speech-to-text/convert), [service terms](https://elevenlabs.io/terms-of-use) | `scribe_v2`, Arabic word timestamps. Uploaded media leaves this server; account permissions/billing and provider terms apply. No key or model is redistributed. |
| OpenAI | [API business terms](https://openai.com/policies/business-terms/), [API data controls](https://platform.openai.com/docs/guides/your-data) | Configurable Responses model; `store:false`. Transcript/context is sent to the provider. Presence of a key does not establish model access, quota or content accuracy. |
| Quranpedia | [Published API usage policy](https://quranpedia.net/api-docs#usage-policy) | Live integration is permitted by the published policy; it disallows bulk scraping/republishing and requires attribution for downloadable data publications. Jisr retains verse/book/translator links in the per-video citation list; it does not bundle or mirror a Quran corpus. Follow provider limits and record-level translation terms. |
| HadeethEnc | [Official API documentation](https://github.com/islamhouse-dev/hadith-api) | Retrieved Arabic report and per-language published translation, with record link. Individual translator metadata is unavailable. API availability is not a blanket dataset redistribution license; no corpus is bundled. |
| Dorar | [Hadith encyclopedia](https://dorar.net/hadith), [tafsir](https://dorar.net/tafseer) | Candidate Arabic wording/grade/attribution and retrieved explanation. Source metadata and direct-record evidence remain separate from HadeethEnc. A general redistribution license has not been established in this audit; keep attribution and do not bulk-package source material. |
| Al-Jamhara | [Dictionary](https://islamic-content.com/dictionary) | Per-term definitions/context and available English equivalents. No dictionary corpus is bundled; retrieved definitions do not establish approved translations in other languages. A general redistribution license has not been established here. |
| Organizer documents | [Participant guide](hackathon/participant-guide.pdf), [scientific package](hackathon/scientific-sources-package.pdf) | Supplied reference copies, retained with [their source manifest](hackathon/source-manifest.json). They are organizer materials, not team-authored deliverables. |

The Quranpedia source is named in the supplied scientific package, page 3. Page 11's preference for the association's approved translation platforms needs to be resolved by the team; QuranEnc is not integrated in this release. [Coverage](languages.md) records actual mappings, unavailable publications and generic Chinese `zh` limitations. No automated test certifies religious correctness or broad rights in publishers' material.
