# جسر · Jisr

**Smart studio for translating Arabic Islamic videos into English, with documented Quranic and Hadith citations.**  
منصة ذكية لترجمة الفيديو الإسلامي وتوثيق الآيات القرآنية والأحاديث النبوية.

> Built for the [AI Challenge for Serving Islamic Content](https://islamicaich.org/), October 2026.  
> Jisr is an AI-assisted tool. Every matched Quranic or Hadith citation requires human confirmation before export or sharing. Unresolved segments block publication.

**Current status:** The local application integrates **ElevenLabs Scribe v2** for transcription and **OpenAI GPT-6 Luna** for translation, quotation detection, terminology review, and source-excerpt alignment. The latest local verification passed **89 Python tests**, including actual FFmpeg video export, plus the JavaScript citation-link checks. Live-provider testing and deployment verification remain necessary before public launch.

![Jisr translation studio — desktop preview](docs/previews/studio-desktop.png)

## The problem

Islamic organizations produce valuable Arabic videos, but reaching English-speaking viewers requires transcription, subtitle timing, translation, and manual verification of every quoted verse or Hadith. Transcription errors can slip through, quotations can be translated as ordinary speech, and viewers may receive no traceable sources.

## How it works

1. **Upload** an Arabic video, or open the interactive example.
2. **Transcribe** with Scribe v2 word timestamps. Suspected audio gaps and uncertain speech are flagged for correction.
3. **Translate** ordinary speech with GPT-6 Luna. Sentence context helps keep connected phrases together; the server validates that subtitle parts preserve every original word and its timing. Al-Jamhara definitions guide translation of detected Islamic terms.
4. **Verify Quran quotations** against Quranpedia's Hafs text and attach sourced Saheeh International English. The model does not generate canonical verse translations.
5. **Verify Hadith quotations** against Dorar and search HadeethEnc for a matching translation and explanation. A unique complete match can be attached automatically; ambiguous or unavailable records require editor selection or manual linking. Unverified English remains a labelled machine draft.
6. **Review** Arabic and English text, timing, narrator, grading, attribution, sources, and subtitle appearance. Editing a verified quotation invalidates its source verification and requires another review.
7. **Export** a subtitled MP4, an SRT file, or a JSON citations list, or publish a read-only video link after all review requirements are resolved.

For partial quotations, citation details retain the full source while subtitles use the corresponding Arabic and English excerpt. The model can select an exact English substring from the sourced translation; it cannot invent a canonical translation. Uncertain alignment requires manual selection before confirmation and export.

Source, translation, explanation, and search links are displayed separately. A Dorar direct link is used only when the published record matches the full text and attribution metadata. If no unique record can be resolved, the interface explicitly labels the search fallback.

## Project structure

```text
server.py               Standard-library Python HTTP API, AI pipeline, storage, and exports
dist/                   Active RTL frontend; no build step
  index.html            App shell
  js/                   Editor, studio, splash, and citation-link helpers
  css/                  Editor and responsive styles
  demo.mp4              Silent illustrative demo video
tests/                  Python tests and JavaScript citation-link checks
scripts/                Public-source checks and saved citation-link repairs
docs/                   API contract, source policy, implementation notes, and previews
.vscode/                Run, debug, and test configuration
.env.example            Configuration template; contains no credentials
Dockerfile              Linux image with FFmpeg
compose.yaml            App, Caddy HTTPS proxy, and persistent data volume
Caddyfile               Reverse-proxy configuration
data/                   Generated media and SQLite database; Git-ignored
archive/prototype/      Preserved early frontend and FastAPI prototype
```

The active backend is `server.py`; the archived FastAPI prototype is not the running application. See the [code map](docs/code-map.md) and [API/data contract](docs/data-contract.md).

## Run locally

Requirements: **Python 3.11+** and **FFmpeg** for video inspection, audio-gap detection, and MP4 export. No Python package installation or frontend build is needed.

Copy the configuration template:

```bash
# macOS / Linux
cp .env.example .env
```

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

Add your keys to `.env`:

```dotenv
ELEVENLABS_API_KEY=your_elevenlabs_key
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-6-luna
```

The ElevenLabs key must have **Speech to Text** access. If FFmpeg is not in `PATH`, set `FFMPEG_PATH` to its executable in `.env`.

```bash
python server.py
```

Open [http://127.0.0.1:8766](http://127.0.0.1:8766). On systems where Python is named `python3`, use that command instead. Restart the server after changing `.env`.

The interactive demo and manual transcript workflow can be used without AI keys. Automatic processing requires both keys and access to the source services. `/api/health` reports configuration availability; it does not verify credentials, billing, or model access.

In VS Code, select a Python interpreter and use **Run and Debug → JISR: Debug app**. The supplied run/test tasks use `python3`; the terminal commands above also work on Windows with `python`.

## Sources and services

| Content or task | Source or service |
|---|---|
| Speech and word timestamps | [ElevenLabs Scribe v2](https://elevenlabs.io/docs/api-reference/speech-to-text/convert) |
| Ordinary-speech translation and quotation detection | [OpenAI GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) through the Responses API |
| Quran text | [Quranpedia API](https://quranpedia.net/api-docs), Hafs text |
| English Quran translation | Saheeh International, Quranpedia book ID `1947` |
| Quran explanation, when available | [Dorar tafsir](https://dorar.net/tafseer), preserving section scope and references |
| Hadith attribution and grading candidates | [Dorar](https://dorar.net/hadith) |
| Matched Hadith translation and explanation | [HadeethEnc API](https://github.com/islamhouse-dev/hadith-api) |
| Islamic terminology | [Al-Jamhara dictionary](https://islamic-content.com/dictionary), retrieved for detected terms |
| Subtitle rendering and MP4 export | FFmpeg |

Religious explanations are retrieved from their sources, not generated by the model. Dorar and HadeethEnc metadata remain distinguishable when both are attached. A source's Hadith grade is not an AI confidence score.

See the [source policy](docs/source-policy.md) for the mapping to the challenge's scientific package and remaining source-integration limits, including QuranEnc prioritisation. Third-party services and content have their own licenses and terms. This repository does not bundle religious datasets, model weights, or API credentials; the demo content is illustrative.

## Verification and maintenance

Run the local tests:

```bash
python -m unittest discover -s tests -v
# Optional JavaScript check; requires Node.js
node tests/test_citation_links.js
```

The latest run passed **89 Python tests with no skips**, with FFmpeg available. External AI and source-service responses are mocked in the suite; no paid API requests are made by these tests. The integration test uploads a video with audio, processes word timestamps and mixed quotations, enforces review, renders an actual MP4, and checks subtitle/source exports, sharing permissions, retries, and deletion. These checks establish local integration rather than live model accuracy.

Optional checks against public citation services:

```bash
python scripts/check_sources.py --output docs/source-check.json
```

This command makes network requests to public sources without sending user videos or invoking paid AI services. The [saved sample report](docs/source-check.json) records successful checks on October 2, 2026; it does not establish corpus-wide matching accuracy.

To repair source links in saved projects:

```bash
python scripts/refresh_source_links.py          # Preview only
python scripts/refresh_source_links.py --apply  # Save resolved links
```

Link repairs preserve transcript text, translations, grades, and review decisions, and do not retranscribe or retranslate videos.

## Privacy and storage

There are **no accounts and no backup system**. Uploaded videos, projects, edits, and exports remain on the server until the editor deletes the project; there is no automatic expiry. Sharing uses a read-only link, while editing requires a separate private link.

Automatic processing sends uploaded media to ElevenLabs and transcript/translation context to OpenAI. OpenAI Responses requests use `store: false`; each provider's own data policies still apply. Public source lookups send relevant quotation or term queries to their services.

Keep API keys and editor links private. `.env`, `data/`, generated logs, and Python caches are excluded by `.gitignore`; only `.env.example` belongs in the repository. Do not force-add private project files when pushing.

## Deployment and remaining work

For a Linux host with a configured domain, set `JISR_DOMAIN` and the API keys in `.env`, then run:

```bash
docker compose up -d --build
```

Docker, persistent storage, and Caddy HTTPS configuration are supplied. Public deployment has not yet been verified end to end.

Live OpenAI testing translated all nine cues from the saved 53.9-second example using its original 113 word timestamps; Maryam 19:96 received a sourced translation. Three cues still required human review at the time of that check. A separate ElevenLabs test reported missing `speech_to_text` permission; verify the key's access and a fresh upload before relying on automatic transcription. See the [live example receipt](docs/live-example.md).

Before public launch, complete human review of representative Arabic videos, verify live transcription and translation together, and check HTTPS, access links, persistent storage, source retrieval, export, and deletion on the intended host. Citation matching, uncertain speech detection, and machine translation still require editor judgment. The [implementation audit](docs/implementation-status.md) records the outstanding launch checks.

## Team

- **Turki:** frontend, UI/UX, integration, and export.
- **Anas:** AI engineering, translation, and API integration.
