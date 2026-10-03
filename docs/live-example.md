# Live example receipt — October 3, 2026

The user configured ElevenLabs and OpenAI keys and authorized a small live test. Credentials, the private editor link, uploaded media, and project data remain local and Git-ignored.

| Check | Observed result |
|---|---|
| OpenAI GPT-6 Luna | Successful live Responses request with strict JSON output; the full Arabic greeting stayed in one cue |
| I1.mp4 | 53.9-second video uploaded into the current JISR_Pull_1 application |
| Saved transcription | Reused all 113 original ElevenLabs word timestamps from the earlier example; no full-video retranscription charge |
| Full English translation | All 9 resulting segments translated; exact original word coverage validated |
| Quran source | Maryam 19:96 matched to Quranpedia Hafs text and sourced Saheeh International English |
| Review | 3 segments require review, including the verse and uncertain words; no automatic human confirmation |
| Export and sharing | Blocked until the editor resolves outstanding review |
| Current ElevenLabs key | A separate 12-second Scribe v2 test returned HTTP 401. A diagnostic request confirmed `missing_permissions` for `speech_to_text`; enable Speech to Text on the existing key before retrying new transcription |
| Hadith | No Hadith quotation established in I1; this video does not prove the live Hadith path |

The new example uses fresh grouping and OpenAI translation, with the original saved transcription reused.

84 local tests pass, including a complete OpenAI-shaped transport workflow with synthetic Quran/Hadith records, human review gates, actual FFmpeg MP4 export, subtitle/source export, sharing, and deletion. These checks establish local integration, not corpus-wide citation accuracy or public deployment readiness.

Sentence grouping now gathers context before the model proposes subtitle boundaries. Original words and timestamps stay authoritative. This reduces premature splitting, but translation and semantic boundaries still require review.
