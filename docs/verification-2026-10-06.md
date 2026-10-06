# October 6 — current product and output quality verification

The current `JISR_Pull_4` application was tested in an isolated local runtime
and through the existing public Render deployment. Existing editor projects
were not rewritten. No religious sample was automatically approved or publicly
shared. Tests establish observed functionality, not expert religious approval
or an independent word-by-word transcription accuracy score.

## Current-release results

- **169 Python tests passed; one Unix-only deployment module was skipped**
  (170 discovered), with real FFmpeg available. All three JavaScript suites
  passed, and the editor JavaScript passed its syntax check.
- I1 and I2 were uploaded and processed afresh with the actual ElevenLabs
  Scribe v2 and configured OpenAI services. I3–I6 used new isolated uploads and
  the previously verified live transcript/source snapshots for current-renderer
  regression checks; they were not transcribed again in this run.
- All six local cases exported MP4, SRT, confirmed sources and draft sources.
  Additional exports covered I1 at size 42 with Amiri and a custom source line,
  and I2 after the attribution repair: **eight local MP4 checks in total**.
- Every checked MP4 fully decoded, retained the original dimensions and
  duration, and had identical copied AAC audio packet hashes. No empty English
  cue or overlapping cue interval appeared in the six base cases.
- **107 cue preview images** across these eight exports matched the exact PNG
  bytes used by export. Actual video frames were extracted for every sampled
  cue; selected frames were also inspected visually. Preview equality alone
  does not establish linguistic correctness or reading comfort.
- MP4 and SRT were downloaded through the actual browser controls. The native
  size-42 MP4 download matched the server's exported file byte for byte.

## UI and permissions

The browser checks covered the landing page/file chooser, processing progress,
Quran details, full source Arabic and English, source-linked seeking/playback,
Quran/Hadith filters, edit dialogs, appearance settings, and draft exports.
Size, font and custom source caption survived a reload. Invalid timing was
rejected without removing the reference; an unsupported file was rejected
without replacing the current project. Mobile layout had no horizontal overflow
in the observed 375-pixel viewport; the temporary viewport override was reset.

A separate, non-religious manual fixture exercised review and sharing. Private
project access without the editing token returned 403; viewing before review
returned 409. After explicitly reviewing the synthetic test text, its viewer
loaded without an editor token or edit/upload/export controls. This fixture is
not evidence that any real religious sample was reviewed.

## Sources and repairs

All seven live public-source smoke checks passed: Quranpedia, HadeethEnc,
Dorar, Dorar tafsir, two Al-Jamhara terms, and automatic Dorar/HadeethEnc
translation matching. These checks used public services with AI calls disabled.

The four actual Quran references in the sample set (19:96, 18:30, 2:152,
33:56) were fetched again. Their full Arabic and Saheeh International English
texts matched the saved references exactly.

The live I2 check exposed an attribution defect: the string `-` was accepted as
a complete narrator value during automatic Dorar selection. Automatic matching
now requires meaningful narrator, grade and attribution values. Parsed source
records still preserve their original missing values, so existing records can
retain accurate links and metadata without invented names or changed grading.
Two regressions cover placeholders and choosing a complete matching record.

Live retrieval after the fix found a report with Abu Hurayrah rather than `-`.
Connected I2 quotation parts were then resolved together and retained one
complete source identity. This repair did not mark the English as a sourced
translation or approve the quotation.

The edit dialog now labels an unsourced Hadith translation as a machine draft
instead of calling it the full source translation. Playback's accessible label
also changes correctly between play and pause. Both changes were verified in
the browser.

The deployment smoke checker now requires the shared English caption-label
JSON asset, so an older or incomplete frontend cannot pass that check merely
because its homepage and AI configuration respond. The final local smoke check
passes; the existing public host lacks this asset and needs the new release.

## Existing public deployment

The existing https://jisr-3ue4.onrender.com/ deployment was tested with a new
I6 upload. Actual transcription, translation, reference retrieval and MP4/SRT
downloads succeeded. Draft-source JSON was downloaded and retained its pending
review status. The downloaded MP4 fully decoded, retained 576×1024 dimensions
and the 15.72-second duration, and preserved the original AAC packets. Its SRT
contained all six timed cues.

The host required a cold start, and source retrieval was still in progress at
the observed 03:38 processing counter before completing. Export was also slower
than local execution. This is an observed single run, not a performance benchmark.

**The public deployment is older than the local release.** Its output still has
the older diacritic backdrop and Arabic attribution caption. The new shared
caption-label asset returns 404 there. No deployment was performed during this
verification; local fixes and current rendering must be published before using
the hosted site to demonstrate the latest appearance.

## Remaining output-quality limits

- Some spoken passages and fast recitations exceed the local reading-speed
  heuristic or display for less than one second. They are flagged; preserving
  ASR timing and a complete reference does not make them comfortable to read.
  Review cue boundaries, concise speech wording and timing before publication.
- Several Hadith narrations have a verified Arabic record but no unique matching
  published English translation. They remain explicitly marked machine drafts;
  related HadeethEnc records require comparison rather than silent substitution.
  The brief phrase “الدال على الخير كفاعله” still has a search fallback, not a
  uniquely resolved direct-record link in this run. Do not call it a direct link.
- Transcription hesitations, possible extraction errors and difficult English
  terminology remain review tasks. An extracted continuous sentence can span
  multiple cues; editor review must assess its connected meaning as well as
  individual cue text.
- Neither the automated suite nor these integration runs replace listening to
  every word, target-audience reading checks or qualified religious review.

Detailed logs, private fixture state, actual outputs and screenshots are under
`work/full-quality-2026-10-06/` outside this repository. Never publish its private
state files or editing links. The deployment ZIP is rebuilt from runtime files
only and excludes real credentials and user projects.

## Follow-up: subtitle transition gaps

Renderer `shared-png-v7` derives subtitle display ends from the original timings:
gaps up to 0.5 seconds hold the previous cue until the next begins. Preview,
SRT and MP4 use the same derived interval; source records and stored spoken
timings remain intact. Longer silences and final cues clear normally. Empty
text containers are hidden, and warmed PNGs are decoded before a preview swap.

The local I3 regression exported a fresh MP4 and SRT without another paid AI
request. At 37.8 seconds, previously inside the 37.64–38.00 gap, the Quran cue
remains visible in both the browser and exported video. At 38.00 it switches
to the next speech cue; at 47.9 the longer pause has no subtitle or background
bars. All 15 preview PNGs match their exported images, the MP4 decodes fully,
and audio packets match the input. Proof and outputs use the `gap-fixed-*`
and `I3-gapfix-*` names in the private work directory above.

The updated Windows suite passes 171 Python tests with one Unix-only skip
(172 discovered), plus all three JavaScript suites. Added regressions cover
short/long gaps, exact transitions, no trailing leak, overlapping timings,
preservation of source/transcript timings, cache swaps and reset during PNG
decoding. The deployment ZIP includes the fix; the public Render deployment
has not been updated by this follow-up.

## Follow-up: narration wording and long Hadith cues

The current I7 project had one 11.92–24.16 Hadith cue, matched to a different
narration beginning with conditional wording instead of the speaker's words.
The exact Dorar record was previously filtered out because its narrator field
was `-`. Retrieval now ranks text before metadata completeness, keeps absent
narrators explicit, rejects changed pronouns/conditional wording for automatic
literal attachment, and never replaces a closer match with a worse translated
alternative. Short ASR split/merge errors remain supported. Grade and
attribution are still required, and every attachment remains unconfirmed.

The actual public Dorar API and website were read with no AI calls. They
returned the matching text and direct record
[mv8Jxe26](https://dorar.net/h/mv8Jxe26), grading `صحيح`, attribution
`مجموع الفتاوى · 10/212`, and narrator `-`. No narrator was inferred.

Subtitle length validation now also covers Hadith/Quran translation parts.
Older automatic Hadith paragraphs can reuse existing Arabic/English sentence
clauses locally when their counts agree, or defer to validated word-range
translation. Human edits/approval, custom captions and paraphrases are preserved.
These splits remain drafts and need contextual review; sentence-count agreement
does not certify translation accuracy.

The current local I7 project was repaired without paid service calls or content
uploads: all 20 original timed words were retained in three cues at
11.92–16.02, 16.36–20.20 and 20.60–24.16. Each uses the corresponding canonical
Arabic excerpt and its existing English clause; all share the matching direct
source. The full text remains in source details, with the active excerpt
highlighted and missing narrator disclosed. English remains `machine_draft`.

A real 1920×1080 MP4 and SRT were exported after the repair. All three Hadith
preview PNGs equal their exported images, full video decoding passed, and
audio packets equal the uploaded original. The Windows suite passes 177 Python
tests with one Unix-only skip (178 discovered), plus three JavaScript suites.
Artifacts use `I7-hadithfix-*`, `hadith-fixed-ui.png`,
`I7-hadith-repair-checks.json` and `hadith-live-source-check.json` under the
private work directory. Original project segments were saved there before
repair. The public deployment has not been changed.
