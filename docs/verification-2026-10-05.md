# October 5 — six-video quality repairs

Verified locally on Windows with real FFmpeg, ElevenLabs Scribe v2 and OpenAI.
This is a technical audit; no qualified religious review or independent
word-by-word listening accuracy measurement was performed.
The repair run reused saved word timestamps from the six fresh live
transcriptions in the initial audit, avoiding another transcription charge.
Meaning checks and source retrieval were exercised with the actual services.

## Regression results

- **I2 introduction:** the English for `ولا تنسى أن` now contains the introduction
  only, without borrowing or repeating the next Hadith. The false Hadith
  candidate on this introduction is removed.
- **I2 connected Hadith:** all three timed parts now share one Dorar record,
  `https://dorar.net/h/lS2wNsu7`, instead of changing source/grade within the quote.
- **I3 connected Hadith:** all three parts share `https://dorar.net/h/mv8Jxe26`.
  HadeethEnc alternatives are retrieved with published Arabic/English and
  metadata. Different wording appears for comparison, not automatic approval.
  Browser selection of record 6461 as an explicit paraphrase updated all three
  parts, preserved their spoken text/timing, remained unreviewed, and persisted
  after reload. A separate literal audit snapshot retains the original match.
- **Saved-project retry:** a ready audit project displayed the new retry button
  and opened the processing dialog. Backend eligibility and UI visibility use
  the same flag; protected human edits do not qualify for automatic repair.
- **I4 meaning:** the misleading physical-protection translation of `تحفظه`
  was corrected to observing God's commands. Three inconsistent ASR passages,
  including the attribution/honorific example, are flagged for listening instead
  of silently reconstructing their Arabic.
- **I6 retrieval:** the related HadeethEnc 3608 record now appears as a comparison
  suggestion. Its published record contains two reports; both explicit narrators
  are retained. It is not silently substituted for a differently worded quote.
- **I1/I5 Quran:** the earlier canonical source and boundary behavior survives.
  Automatic captions now identify a translation of Quranic meanings and its
  translator. Original audio is retained.

All unreviewed ordinary speech is now pending alongside scripture. Meaning
checks preserve source text, timestamps and human edits; provider failures keep
drafts with explicit warnings. Fast/short displays are flagged without moving
ASR timings or shortening source translations. They still require an editor's
decision, especially for fast recitations.

## Export and UI verification

- Final `shared-png-v4` MP4 and SRT exports succeeded for **all six videos**, plus
  the I3 source-selection case and an I3 size-42 export.
- All eight MP4 files decode completely. Original dimensions and durations are
  preserved. AAC packet hashes equal the respective originals.
- **34 sampled cue images** match the exact PNG bytes used by export, including
  six samples at size 42. Long cues fit approximately into the lower half of the
  frame; their effective font size can be below the requested size.
- The browser showed review warnings, allowed private export, disabled public
  sharing, compared complete source records and applied a group selection.
- **Draft sources JSON** was prepared and downloaded from the actual UI. It
  carries pending review states. The existing confirmed-source JSON stays empty
  until citations are confirmed. No human review was auto-approved in this audit.
- Changes were exercised on isolated audit projects; existing editor projects
  were not rewritten or auto-confirmed.

## Automated checks and package

**163 Python tests passed; one Unix-only deployment module was skipped.**
All three JavaScript suites passed. The eight rendering regression tests were
also rerun after the cache-version update. Tests cover transactionality,
attribution extraction, independent meaning checks, draft export permissions,
protected group updates, scripture boundaries and preview/export equality.
Automated provider transports are mocked; the six-video audit uses real services.

The local deployment smoke check passed. The runtime ZIP includes the new
`pipeline_quality.py` dependency in both its payload and Docker build context;
manifest hashes and exclusion of actual API keys/project data were verified.
No public hosting deployment was performed.

Detailed local evidence, videos, SRT files, source inventories and sampled
frames are stored outside the repository in `work/six-video-repairs/` under the
workspace root. Its private editor-state file must not be shared or committed.

## Remaining acceptance work

Select and review competing Hadith narrations and their English excerpts;
listen to flagged transcription, adjust fast displays, and have a qualified
reviewer check religious meaning before publication. An AI quality check does
not establish correctness. Deploy and verify the same flow from an open HTTPS
URL for the judges.
