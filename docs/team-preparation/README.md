# Jisr team preparation

> The plan below is historical. The current release implements seven target languages at the user's request; the old English-only scope and language-expansion restriction below no longer apply. See the [final delivery check](../final-delivery-check-2026-10-06.md) for current code and remaining submission artifacts.

> Update after GitHub integration: OpenAI translation and the Hadith paraphrase fix are now in the shared code. FFmpeg is installed locally; the combined suite passes 90 tests, including MP4 export. The starting-state table and baseline.json below are historical snapshots from 17:23 on October 3, not current app status.

Prepared October 3, 2026. All dates and times below use Riyadh time.

**Start with the task board. Turki owns the product journey and delivery materials; Anas owns AI processing and its evaluation. Both review the final output.** Your immediate goal is one complete, reviewed, reproducible video workflow, followed by broader evidence and a working hosted version.

## Your working files

| File | Use it for |
|---|---|
| [Task board](task-board.md) | Assign work, follow dependencies, and check when a task is actually complete |
| [Presentation draft](presentation-draft.md) | Copy-ready slide content, speaker notes, and evidence slots |
| [Video script](video-script.md) | A 115-second recording plan and narration |
| [Evaluation and release checklist](evaluation-and-release.md) | Human review, comparison measurements, hosting checks, and submission checks |
| [Sources and components register](sources-and-components.md) | Finish source, tool, media, and license documentation |
| [Starting baseline](baseline.json) | File hashes and the state observed before development days |
| [Review of supplied organizer files](official-documents-review.md) | What the three supplied files mean for Jisr, including template layouts and source-policy updates |

These are preparation documents. The presentation draft still needs conversion to a final deck, and the video script still needs recording. Blank measurements are deliberately left blank.

## 1. Agreed project definition

**One sentence:** Jisr helps Islamic content creators turn Arabic videos into English-subtitled videos, with traceable Quran and Hadith references and an editor review step before publication.

**Problem:** A creator currently has to move between transcription, translation, subtitle timing, and reference checking. A generic translation can miss a quotation or render a religious term without its intended meaning. Combining these tasks creates a focused editing workflow worth testing.

**Primary user:** An Arabic-speaking editor or content creator preparing short Islamic educational videos for English-speaking viewers.

**Beneficiary:** An English-speaking viewer who needs clear subtitles that preserve the speaker's meaning. The creator operates the editor; the viewer receives the video.

**First use case:** Upload a short Arabic video, generate a timed draft, inspect quotations and terminology, correct and confirm the output, then export an MP4, SRT, and source list. Keep Arabic-to-English as the submission scope.

**Distinctive value to demonstrate:** The creator can see where a quotation came from, distinguish source text from machine-translated speech, and resolve uncertainty before publishing. Show this with an actual reviewed output rather than a design screenshot.

**Track fit:** The multilingual content/localization track appears to fit Jisr's core purpose. Keep the team's already accepted track; verify it in the portal rather than attempting a registration change.

## 2. Official requirements located

Source: [official website](https://islamicaich.org/) and the [supplied participant guide](../hackathon/participant-guide.pdf), checked October 3. The supplied guide confirms the delivery and final judging requirements previously found online.

- Submit by **October 6, 11:59 p.m.** through the portal and retain confirmation.
- Deliver a functioning complete use case, a live demo link, a public GitHub repository, operating documentation, a sources/tools/licenses register, a PDF or PowerPoint presentation, and a video of at most two minutes.
- The guide permits Arabic or English and a compliant custom presentation layout. The team now has the [official editable template](../hackathon/presentation-template.pptx); its 31 slides include instructions and optional layouts, not a required slide count.
- Record the existing project's baseline; the website says evaluated new work is October 4–6.
- Final-stage weights: technical/AI quality **25%**, scientific reliability **15%**, innovation **15%**, user experience/accessibility **10%**, track benefit **20%**, operational feasibility **10%**, presentation/verifiability **5%**. The final session allocates **5 minutes presenting + 3 minutes questions**.

Check portal fields and any later organizer instructions before final upload. The proposed schedule below is our team's plan, not an organizer timetable.

## 3. Actual starting state

Observed from code, saved project metadata, documentation, and checks on October 3:

| Area | Evidence | What it means for your work |
|---|---|---|
| Frontend | Start screen, upload entry, editing, source dialogs, review filters, styling, and export controls exist | Exercise these using the real project; avoid rebuilding the interface |
| Backend | Processing, checkpoints, source matching, review gates, storage, SRT/JSON/MP4 paths exist | Preserve the working contract while changing providers |
| Current saved project | Error status; 241 segments; 30 contain nonempty English; 0 linked citations; 10 unresolved review flags; stored duration is 0 | Diagnose this project before choosing it as the demonstration. Nonempty English is not evidence of reviewed accuracy |
| Earlier documented example | October 2 receipt reports a 53.9-second transcription, five translated segments, and a Maryam 19:96 reference | Historical evidence only. Its relationship to the current saved project is unconfirmed |
| Live translation | Documentation records quota/service failures and a team pause while choosing a Gemini alternative | Provider selection is the first AI dependency; preparation does not resume requests |
| FFmpeg | Neither ffmpeg nor ffprobe was found on the current shell PATH; tests skipped their dependent checks | Confirm binaries, video probing, and Arabic subtitle rendering on the machine used for release |
| Tests | 77 discovered; 74 passed, 3 skipped after allowing local test-server access | Good local evidence, but the real MP4 integration path and live providers remain unverified here |
| JavaScript | Syntax checks passed for app.js, studio.js, and splash.js | Syntax is verified; a fresh browser acceptance session is still needed |
| Hosting | Docker/Compose/Caddy configuration exists | A public URL and host behavior have not been verified in this review |
| Licenses | No project LICENSE file was found among tracked files | Agree project licensing and complete the component register before publishing |

Existing uncommitted changes in studio.js and studio.css were present before this preparation. Their hashes are in the baseline. No application source was changed by this preparation. Documentation was subsequently updated against the three organizer files supplied by the user; the starting code baseline remains unchanged.

## 4. Ownership and how to work together

**Turki:** User journey, frontend, FFmpeg/export integration, hosting coordination, presentation, video recording, portal submission.

**Anas:** Translation provider decision/integration, word/timing preservation, terminology and quotation processing, live processing evidence, quality/cost measurements, AI/source documentation.

**Together:** Select permitted test media, listen to the original audio, review the English, confirm reference excerpts, test release behavior, agree public claims, and check the final submission.

Anas should primarily change server.py and relevant tests; Turki should primarily change dist/ and deployment files. Agree before editing each other's area. Anas sends a short handoff when a backend change affects a provider label, health field, configuration key, API response, or review state. Turki returns the browser result and any blocking error.

For each completed task, record: task ID, changed files/commit, what was tested, evidence location, and remaining issue. Do not mark a task complete because its code was written.

## 5. Proposed milestones

| Date | Turki | Anas | Shared completion target |
|---|---|---|---|
| Sat Oct 3: preparation | Read this pack, establish submission folders, collect guide/portal details, outline presentation | Diagnose saved project, compare provider requirements, identify permitted test clips | Baseline saved; ownership agreed; mentor questions ready; no new feature commitments |
| Sun Oct 4: complete the core flow | Confirm FFmpeg/probing; exercise real editor and exports; identify host | Integrate chosen provider; complete transcription/translation/source path | One real clip fully reviewed and exported; working preview of deployed backend |
| Mon Oct 5: prove quality | Observe a creator using the editor; measure task friction; finish live URL; assemble slide evidence | Run varied clips and controlled failures; compare results; measure cost and processing time | Evaluation records, hosted workflow, first deck draft, first recorded demo |
| Tue Oct 6: finish delivery | Finalize deck/video; test every link; upload and retain receipt | Confirm release configuration; re-run affected checks; finish source/provider notes | Feature freeze at noon; package review by 4 p.m.; first submission target 8 p.m. |

The noon/4 p.m./8 p.m. targets are proposed buffers. If the main workflow is still blocked on October 4, ask a technical mentor immediately, move presentation polishing behind the blocker, and narrow optional scope. A manually completed example can support a recording if clearly labeled, but does not prove automatic processing works.

## 6. Mentor questions, ready to use

Bring the failed stage or concrete example with each question. Keep credentials and private editing links out of the channel.

1. **Source/content mentor:** “The supplied package lists Quranpedia on page 3 and QuranEnc/HadeethEnc on page 9; page 11 emphasizes the association's approved translations. Should our Quran translation come from QuranEnc, or is our current Quranpedia/Saheeh International record acceptable? What attribution and review evidence should we display?”
2. **Content/translation mentor:** “Can you help review this specific subtitle against its Arabic audio, especially the terminology and the partial quotation? What would you consider a meaning-changing error?”
3. **Technical mentor:** “Our processing has saved partial results after provider failures. We need an alternative that supports structured word partitions, terminology refinement, and reference excerpt selection. Which integration risks should we address first?”
4. **Product mentor:** “Our operator is the creator and our beneficiary is the English-speaking viewer. Does our timed comparison and short comprehension check demonstrate the right benefit?”
5. **Delivery mentor:** “Does the judge need to run a fresh upload themselves on the live link? Are there additional portal fields, identity assets, or an editable presentation template beyond the public guide?”
6. **Program mentor:** “Jisr existed before October 4. We documented code hashes and current limitations. Is this sufficient baseline evidence, and how should we present October 4–6 improvements?”

Record answers with date, mentor, decision, and the affected task ID. Both owners should see the decision before implementing it.

## 7. First working session

1. Read task IDs T01–T05 together and assign a target time for each.
2. Turki checks the release machine and starts the presentation from the supplied draft.
3. Anas diagnoses the saved project and prepares the provider decision against the listed contract.
4. Agree the demonstration clip and review standard.
5. End the session by recording blockers and the next shared checkpoint.

Do not expand into accounts, additional languages, long-video processing, or new effects until the core flow, evidence, and submission materials are complete.
