# Evaluation and release checks

> Current local validation after integration: 90 Python tests passed, including real MP4 export, plus JavaScript citation checks. Earlier test counts below record the starting baseline; use current measured results in the final submission.

Use this to produce evidence for Jisr, not just a list of features. Anas owns processing measurements; Turki owns user-journey and host checks; both review content.

## A. Test cases

Use a small, clearly labeled pilot. Start with short clips so you can review every spoken segment. The durations below are suggestions, not measured inputs.

| ID | Suggested case | Required observation |
|---|---|---|
| E01 | Ordinary Arabic speech, 20–40 seconds | Transcript and English preserve meaning; timings follow speech; MP4 has readable subtitles |
| E02 | Religious terminology in context, 20–40 seconds | Retrieved definition/English term helps review; missing dictionary match is disclosed |
| E03 | Partial Quran quotation, 20–40 seconds | Correct location, authoritative source text, exact corresponding English excerpt, human confirmation |
| E04 | Hadith quotation, 20–40 seconds | Narrator/grade/attribution reported from their providers; translation source distinguished from machine draft; ambiguity not silently accepted |
| E05 | Unclear speech or source ambiguity | Review remains required until corrected/resolved; uncertainty is visible |
| E06 | Controlled provider interruption or invalid response | Saved work remains; errors explain the next action; retry preserves transcript, timing, and completed batches |
| E07 | Speaker discusses a disputed issue with a qualification | Translation retains the qualification/disagreement and creates no unsupported consensus or ruling |
| E08 | Speaker asks a personal religious question | Translate the question faithfully; the model does not answer it or issue a personal ruling |
| E09 | Misquoted scripture, unsupported attribution, or missing reference | Flag the issue for review; avoid fabricated sources, silent substitution, or an unverified publication claim |

One clip may cover multiple cases. Repeat one successful core case to check consistency. Use mocks to exercise quota/timeout paths without deliberately exhausting a paid quota, and label such evidence as simulated. At least one full successful run must use the selected live providers for a live-processing claim.

## B. Review rules

For every segment, listen to the audio and compare the transcript, English, and timing.

- **Meaning:** Are a negation, subject, condition, attribution, or theological meaning changed? Such a change is a critical error.
- **Terminology:** Does the English express the term in this speaker's context? A dictionary definition alone does not approve the sentence.
- **Quotations:** Does the source identify the actual spoken quotation? For an excerpt, do subtitles include only the corresponding reference text? A wrong verse/Hadith or invented canonical translation is critical.
- **Timing/readability:** Can a viewer read the subtitle while the words are spoken? Record overlap, clipping, excessive line length, and missed words.
- **Uncertainty:** Are unresolved candidates, unclear words, and source failures surfaced? Do not dismiss a real problem just to enable export.

Anas reviews first; Turki cross-checks the audio and editor behavior. Seek a qualified content/translation reviewer for material beyond your ability to assess. Record reviewer qualifications accurately; a team review is not scholarly certification.

Our release target: zero unresolved critical errors in the demonstrated outputs and every displayed quotation checked against its source. Report draft errors and corrections as well as the final result.

The supplied scientific package also requires traceability of substantive religious information, not only quotations. For each demonstration claim, record its accepted supporting reference and review outcome. Code currently links quotations and terminology; it does not establish every religious statement's truth. Agree the resulting source/review treatment in T15 and disclose that boundary in the product and presentation.

## C. Fill one record per run

```text
Case / run:
Date (Riyadh):
Code commit or file baseline:
Clip duration and media permission record:
Provider / model / relevant configuration:
Live external processing or controlled fixture:
Reference author / reviewers:
Machine processing time:
Human review/editing time:
Transcript errors before correction / spoken words checked:
Meaning-changing translation errors before correction:
Terminology errors before correction / terms checked:
Correct quotation locations / quotations checked:
Correct source excerpts / excerpts checked:
Unresolved issues after review:
SRT / source JSON / MP4 locations:
Viewer and full workflow result:
Provider charge evidence or dated estimate:
Limitations / next action:
```

Avoid private edit tokens, keys, or identifiable participant information in public evidence. Use permitted clips and aggregated observations.

## D. Demonstrate benefit without inventing metrics

Choose a defined baseline: the creator uses their ordinary transcription/translation/subtitle tools and checks the same sources manually. Both outputs must meet the same review standard. Record the baseline tools and human steps.

Measure human active work separately from machine waiting and total elapsed time. If the same person does both workflows, record the order and note that familiarity with the clip can favor the second attempt. An unfamiliar second clip or a second operator can reduce that effect, but small samples remain a pilot.

Time saving (%) = 100 × (manual active minutes − Jisr active minutes) / manual active minutes. Calculate only if the manual value is positive and comparable; retain negative results too.

Report quotation accuracy as correct checked items / all checked items. Keep sourced translation, machine-draft translation, and manual correction distinguishable. Do not call a test-suite pass rate translation accuracy.

For viewer clarity, have a willing English-speaking reviewer watch a permitted output and answer a few questions based on the speaker's message. Record the questions and aggregate outcome. If unavailable, leave this result unmeasured.

Cost per minute = total recorded processing charges / processed media minutes. Separate transcription, translation/refinement/excerpt calls, hosting, and human review. Label estimates with their assumptions and date. Include failed attempts in the operating-cost discussion.

## E. Browser and output acceptance

- [ ] Fresh upload works; unsupported/corrupt input is rejected appropriately on the release machine.
- [ ] Processing shows useful state and preserves progress after an error.
- [ ] Ready-for-review is distinguishable from approved-for-publication.
- [ ] Editing text/timing saves correctly and does not misrepresent an old citation.
- [ ] Unresolved quotes/excerpts block publication until resolved; source details remain readable.
- [ ] Review filters, segment seeking, keyboard access, narrow layout, and subtitle settings work.
- [ ] Actual exported MP4 has audio, correct duration, readable Arabic shaping and English, and correct subtitle position.
- [ ] SRT opens in a subtitle player; source JSON matches the demonstrated quotations.
- [ ] Public viewer opens independently and exposes no editing capability.
- [ ] Private editing access can be recovered by its holder; unauthorized edits fail.

## F. Host and reproducibility acceptance

- [ ] Runtime is Python with FFmpeg/FFprobe support and suitable fonts; static-only hosting is insufficient.
- [ ] HTTPS application URL loads in a fresh browser.
- [ ] Live credentials work on the host without exposing their values to browsers or public files.
- [ ] Public citation services can be reached from the host.
- [ ] Uploaded projects and exports remain available after restart, with correct private/viewer behavior.
- [ ] A new permitted upload can complete review/export on the deployed app.
- [ ] Health endpoint is treated as configuration evidence, followed by an actual workflow test.
- [ ] The intended deletion operation is checked using a separate disposable project.
- [ ] Another person follows release README instructions successfully on the chosen runtime.
- [ ] Limits, storage/deletion behavior, provider dependencies, and approximate operating cost are documented.

## G. Final submission review

Use the official requirement list in this folder's README as the source checklist.

- [ ] All required outputs and URLs are present and open from an independent browser.
- [ ] The code release includes only material the team can publish; secrets and private project data are excluded, including from prior history when relevant.
- [ ] Sources/component/media register is completed; unresolved publication permissions are addressed.
- [ ] Presentation and recording match the actual release and distinguish existing work from new development.
- [ ] Video has been timed and watched fully; presentation has been inspected page by page.
- [ ] Baseline and development log retained; evidence supports each reported achievement.
- [ ] Portal entries checked by both members; confirmation saved with timestamp.

## Verification already performed October 3

`python3 -m unittest discover -s tests -v`: 77 discovered, 74 passed, 3 skipped. The first sandboxed run could not bind local HTTP test servers; rerunning with local server access succeeded. Skips: full FFmpeg integration, HTTP upload/process path requiring video probing, and video-probe validation.

`node --check` succeeded for dist/js/app.js, dist/js/studio.js, and dist/js/splash.js. These checks made no paid-provider calls and do not verify live translation or a public deployment. Re-run affected tests after implementation; re-run the full media-enabled suite before release.
