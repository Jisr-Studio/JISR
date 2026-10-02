# جسر · Jisr

**Smart studio for translating Arabic Islamic videos into English, with documented Quranic and Hadith citations.**  
منصة ذكية لترجمة الفيديو الإسلامي وتوثيق الآيات القرآنية والأحاديث النبوية.

> Built for the [AI Challenge for Serving Islamic Content](https://islamicaich.org/), October 2026.  
> Jisr assists the editor. Every matched Quranic or Hadith citation must be confirmed by a human reviewer before export or sharing. Unresolved segments block export.

**Current status:** Translation integration work is paused at the team's request while selecting an alternative to Gemini. The existing backend and editor are preserved. The supplied real example has a complete transcript, a sourced Quran citation, and partial English translation; full translation, human review, and public deployment remain unfinished. See [the live example receipt](docs/live-example.md).

## UI and workspace

- New midnight blue, soft white, and amber theme with the Mihrab logo.
- A start screen explains the product and offers upload or an interactive example.
- The studio groups tools into **Review**, **Sources**, and **Appearance** tabs, with keyboard navigation.
- A clickable segment timeline connects the video preview to transcript selection.
- Processing/error status and review reminders explain what needs attention before export.
- A skippable 1.1-second splash appears once per tab session. Reduced-motion users and direct project/demo/share links bypass it.
- Responsive layouts and reduced-motion support are included.
- Active scripts and styles are organized in `dist/js/` and `dist/css/`. The old prototype is preserved under `archive/prototype/`.
- VS Code tasks, debugging, and unittest discovery now target the working Python application rather than the old FastAPI skeleton.

This update changes the interface and workspace organization. Completing live translation, human review of the real example, and public deployment still remains necessary.

![JISR translation studio — desktop preview](docs/previews/studio-desktop.png)

### Working in VS Code

Open the repository folder and select your installed Python interpreter. Use **Terminal → Run Task → JISR: Run app** to start the application, **Run and Debug → JISR: Debug app** to debug it, and **Tasks: Run Test Task** to run the existing suite. Recommended formatter extensions are listed in `.vscode/extensions.json`; they are optional for running the app.

Verification for this update: JavaScript syntax checks and browser checks of the start screen, demo entry, studio tabs, source dialogs, timeline selection, review filtering, splash dismissal, and responsive layouts. The backend suite ran **77 tests: 74 passed, 3 skipped** in the current environment. This run does not verify the skipped FFmpeg-dependent tests or a complete live-provider workflow.

## The problem

Islamic organizations produce valuable Arabic video content, but preparing it for English-speaking viewers takes time: transcribing speech, timing subtitles, translating, and checking every quoted verse or hadith. A quotation can be mistaken for ordinary speech, transcribed incorrectly, or published without a clear source.

## How it works

1. **Upload** an Arabic video.
2. **Transcribe** speech with word-level timestamps using ElevenLabs Scribe v2. Suspected gaps and low-confidence segments are flagged.
3. **Translate** ordinary speech into English using Gemini. Detected technical terms are looked up in Al-Jamhara; a second translation review uses the matched definitions and available English terms. Quranic and Hadith quotations follow separate verification paths.
4. **Match Quranic quotations** against Quranpedia's Hafs text. A matched verse receives a sourced English translation, never an AI-generated verse translation.
5. **Check Hadith quotations** against Dorar. Search HadeethEnc automatically and attach a sourced translation and explanation only when a unique complete record matches both the transcript and Dorar text. Multiple plausible reports remain a machine draft with selectable records for the editor; manual linking remains available.
6. **Review and edit** the transcript, timing, English text, citation details, and subtitle appearance. Editing a verified quotation's Arabic text removes its source link until it is checked again.
7. **Export** an MP4 with subtitles, an SRT file, and a JSON citations list, or share a read-only video page. Export is blocked while segments are unresolved; the editor remains responsible for checking citations before publication.

For a partial verse or Hadith quotation, the full source text remains in the citation details. Subtitles use only its corresponding Arabic and English excerpt. Gemini may select a verbatim English substring from the reference; it cannot write a new canonical translation. If alignment is uncertain or keys are missing, the editor selects the matching text from the source. Partial quotations cannot be confirmed or exported until this selection is resolved.

## Project structure

New automated transcripts retain word timestamps. Mixed segments are split into ordinary speech and individual quotations before source matching. The server derives the Arabic text and timing from the original transcript, rejects incomplete or overlapping model ranges, and preserves the translation of surrounding speech.

```text
server.py           Python standard-library HTTP API, processing, storage, and export
dist/               Active RTL web app served by server.py
  css/              Base editor styles and current theme
  js/               Editor/API logic, studio journey, and splash screen
  index.html        App shell
  favicon.svg       Mihrab logo
  demo.mp4          Silent demo video
archive/prototype/  Preserved original frontend and FastAPI skeleton
.vscode/            Run/debug/test configuration
docs/previews/      Saved UI screenshots
tests/              Backend tests
docs/               Frontend/backend API and data contract
scripts/            Opt-in checks of public citation services
.env.example        Environment variable template
Dockerfile          Linux image with FFmpeg
compose.yaml        App, Caddy HTTPS proxy, and persistent data volume
Caddyfile           Reverse-proxy configuration
data/               Generated project files and SQLite database (Git-ignored)
```

See [the code map](docs/code-map.md) for file responsibilities and VS Code shortcuts.

## Run locally

Requirements: **Python 3.11+**. No Python packages need to be installed. **FFmpeg** is required for MP4 export.

```bash
cp .env.example .env       # PowerShell: Copy-Item .env.example .env
# Add ELEVENLABS_API_KEY and GEMINI_API_KEY to .env for automatic processing.
python server.py
```

Open [http://127.0.0.1:8766](http://127.0.0.1:8766). Restart the server after changing `.env`. The manual transcript workflow works without API keys; automated processing requires both keys. On a machine without FFmpeg in `PATH`, set `FFMPEG_PATH` in `.env`.

For a Linux server with a configured domain, set `JISR_DOMAIN` and the API keys in `.env`, then run `docker compose up -d --build`. The container deployment has not yet been verified with live API keys and a real video; complete that end-to-end check before opening it to the public.

## Sources and services

The integration contract is documented in [docs/data-contract.md](docs/data-contract.md).

| Content or task | Source or service |
|---|---|
| Arabic Quran text (Hafs) | [Quranpedia API](https://quranpedia.net/api-docs) |
| English Quran translation | Saheeh International, Quranpedia book ID `1947` |
| Quranic explanation, when available | [Dorar tafsir](https://dorar.net/tafseer), with the original section scope and references |
| Hadith search and grading candidates | Dorar |
| Linked Hadith text, English translation, grading, and explanation | [HadeethEnc API](https://github.com/islamhouse-dev/hadith-api) |
| Speech-to-text | [ElevenLabs Scribe v2](https://elevenlabs.io/docs/api-reference/speech-to-text/convert) |
| Translation of ordinary speech and quotation detection | [Gemini](https://ai.google.dev/gemini-api/docs/structured-output) |
| Terminology guidance | [Al-Jamhara dictionary](https://islamic-content.com/dictionary), fetched for detected terms; page 8's sample glossary provides baseline guidance |
| Subtitle rendering and video export | FFmpeg |

Third-party data and services have their own licenses and terms. The repository does not include Quran or Hadith datasets, model weights, or bundled API keys. The demo video and its sample data are illustrative.

Source selection and remaining integration limits are documented in [docs/source-policy.md](docs/source-policy.md). Commentary is retrieved from its source and kept separate from the verse text; it is never generated by the model.

## Verification

```bash
python -m unittest discover -s tests -v
python scripts/check_sources.py --output docs/source-check.json
```

The second command makes public-source requests without paid API keys or user media. The [saved report](docs/source-check.json) records successful sample checks of Quranpedia, HadeethEnc, Dorar Hadith, Dorar tafsir, two Al-Jamhara terms, and automatic Hadith translation matching on October 2, 2026. It proves connectivity and expected fields for those samples, not corpus-wide accuracy or permission to redistribute every source. Both paid keys are now configured locally. ElevenLabs successfully transcribed the supplied 53.9-second Arabic example with 113 word timestamps. Gemini translated the first batch (five resulting segments), then subsequent processing stopped with HTTP 429. The saved results can be resumed without retranscribing. Full live translation and human review are still pending; see the [example receipt](docs/live-example.md).

The local suite currently passes 77 tests. Its full integration test uploads an actual video with audio, exercises streaming Scribe requests and Gemini translation/dictionary/excerpt requests through fake external transports, matches Quran/Hadith source fixtures, flags an untranscribed audio interval, requires review, and exports a real MP4 using FFmpeg. It also checks SRT, source JSON, read-only sharing, editor access, and deletion. Reference fixtures are synthetic; this test proves local integration, not live model accuracy. See the [implementation audit](docs/implementation-status.md) for remaining launch checks.

## Privacy and current limits

There are **no accounts**. Projects, uploaded videos, edits, and exports remain on the server until the editor deletes the project; there is no automatic expiry or backup system. Anyone with a share link can view its published project, while editing requires a separate private link. Keep the edit link and API keys private. `.env` and `data/` are excluded from Git.

The supplied real video has been partially processed with live keys; completing translation, human review, and deployment verification remain necessary before public launch. Human review is especially important for partial verse quotations, hadith attribution and grading, low-confidence speech, and translation in context.

Dictionary integration retrieves only detected terms and temporarily caches up to 256 records in memory. Search results must match the full headword; related or ambiguous results are not accepted. Not all entries have English translations, and the site's search can omit records. Missing dictionary matches flag affected segments for review. Source-guided speech translation is still machine translation, not an approved translation of the whole sentence. It adds one Gemini call per batch containing matched terms, plus public-source requests.

## Team

- **Turki:** frontend, UI/UX, integration, export.
- **Anas** AI Engineering, translation, API integration.
