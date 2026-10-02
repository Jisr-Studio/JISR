# Live example receipt — October 2, 2026

**Paused by the user:** choose an alternative translation API before continuing integration. The implementation and saved results are retained; no further automatic translation attempts are running.

The user supplied **I1.mp4** and authorized processing with their configured ElevenLabs and Gemini keys. Keys, the private edit link, the uploaded video, and project data are excluded from the source archive and Git.

| Check | Observed result |
|---|---|
| Upload | Local project created; video duration 53.9 seconds |
| ElevenLabs Scribe v2 | Successful real transcription with 113 word timestamps; reused on subsequent attempts |
| Gemini | First structured translation batch saved; 5 translated segments out of 13 after splitting the quotation |
| Remaining translation | Stopped with HTTP 429 after earlier service-unavailability/timeouts; the project retains completed work |
| Quota diagnostic | One Gemini 3.8 request at 12:35:57 UTC returned HTTP 429 with `Retry-After: 41040` seconds; no automatic retry was made |
| Alternative model | At the user's supplied usage screenshot, the running server was temporarily switched to Gemini 3.7 Flash; its bounded pending-batch attempt ended in HTTP 503 at 12:39 UTC without altering saved results |
| Quran source | Maryam 19:96 matched to Quranpedia Hafs text and Saheeh International translation; linked through the editor API without human confirmation |
| Explanation | Dorar commentary retrieved with its original section scope, verses 96–98 |
| Source formatting | Quranpedia returned HTML and translator footnotes; subtitle text is cleaned without rewriting its wording, and footnotes remain in source metadata |
| Review hints | Unfinished words and one unusually long word timing flagged; no guessed transcript corrections applied |
| Hadith | No Hadith citation established in this example; this clip does not validate the live Hadith path |
| Export/share | Blocked while translation and human review remain incomplete |

The local suite passes **77 tests**, including actual FFmpeg rendering with controlled external API responses. This does not substitute for completing and reviewing the real example. The local editor's **متابعة المعالجة** button resumes pending batches after Gemini becomes available; it does not repeat the saved transcription or completed translation.

The active local server uses Gemini 3.7 through process environment overrides. The user's `.env` keys and source defaults were not changed; a normal restart returns to the configured model or the default Gemini 3.8. A lower displayed historical peak for another model does not prove current remaining quota or service availability.
