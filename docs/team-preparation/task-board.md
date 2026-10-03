# Jisr task board

Prepared October 3. Check a box only after its completion check passes. Suggested effort is active work, excluding service failures, reviews, workshops, and mentor availability.

## Preparation: both owners start here

- [ ] **T01 — Establish the baseline and release targets.** Owner: Turki; Anas confirms. Effort: 20–30 minutes. Before: none.
  - Read baseline.json and the state table in README.md. Include the existing dirty frontend files in any team snapshot.
  - Keep today's existing work separate from new development entries starting October 4. Record commits or changes per task.
  - Record accepted track, submission portal URL, and the machine/host intended for release.
  - **Done:** both agree the starting limitations and one release target; the baseline is retained. No secret or user project data is included in public evidence.

- [ ] **T02 — Select the demonstration and evaluation media.** Owner: both. Effort: 30–45 minutes. Before: T01.
  - Choose an audible, short Arabic clip you can use in the demonstration. Confirm rights/consent and the organizers' data requirements.
  - Use the current saved project only after diagnosing it. Prepare a separate permitted clip for Hadith if the main clip contains none.
  - Write a reference transcript/translation for evaluation, identifying source quotations and accepted terminology.
  - **Done:** main clip chosen, permissions recorded, reference reviewed, and additional case clips identified. Do not use synthetic test-fixture quotations as approved religious material.

- [ ] **T15 — Align scientific sources and content boundaries.** Owner: Anas; Turki implements any review messaging. Effort: 45–90 minutes plus mentor response. Before: T02; complete before T08.
  - Read scientific package pages 3–7 and 9–11, using official-documents-review.md. HadeethEnc is explicitly listed, so it no longer needs to be treated as absent from the supplied package.
  - Resolve the page 3 Quranpedia allowance and page 11 translation-source emphasis with the content mentor. Record the selected translation, provider, attribution, and source decision; do not replace a working integration just because another API is listed.
  - Check traceability of ordinary religious statements as well as quotations. For the demonstration, identify accepted references for substantive claims and have the reviewer check that translation preserves them. The current quotation matcher does not verify every religious statement automatically.
  - Test preservation of disagreement/hedging and personal questions. Jisr translates the speaker; it must not produce its own fatwa, answer a question inside the audio, or fabricate a reference when one is unavailable.
  - **Done:** source decision documented, E07–E09 results recorded, demonstration claims traceable, and interface/documentation accurately describe what was reviewed.

## Critical path: finish before presentation polish

- [ ] **T03 — Diagnose current saved processing.** Owner: Anas. Effort: 30–60 minutes. Before: T01.
  - Current metadata: error, 241 segments, 30 with English, no linked citations, duration 0. Determine the failing stage and whether the transcript matches the selected input.
  - Record which segments/batches are already complete. Establish whether the previous 53.9-second example is still available separately.
  - Determine why duration is 0; ensure final timing agrees with the actual media.
  - **Done:** a written diagnosis and safe resume/new-project decision. Retain completed work; no duplicate transcription merely to retry translation.

- [ ] **T04 — Choose the translation provider.** Owner: Anas; Turki confirms the product implications. Effort: 45–90 minutes. Before: T03.
  - Compare the team's realistic candidates using current official documentation. Record structured-output support, availability/quota, Arabic-to-English quality on your sample, data handling, request cost, and timeout behavior.
  - Confirm model identifiers and API fields against that provider's documentation before coding. Existing model labels do not prove current availability.
  - Produce a short decision with selected provider/model, reasons, expected request types, and fallback behavior.
  - **Done:** usable credentials/configuration and a justified selection; all three model-dependent paths below have a plan.

- [ ] **T05 — Integrate all model-dependent paths.** Owner: Anas. Suggested effort: 3–5 hours. Before: T04; development target Oct 4.
  - Main translation/classification: server.py translate_segments(), translation_request(), translation_parts(), validated_translation_parts(). Preserve IDs, exact word coverage, Arabic, timestamps, surrounding context, and completed-batch checkpoints.
  - Terminology refinement: ground_terminology(). Keep source definitions and published equivalents as guidance; retain uncertainty when dictionary matches are unavailable.
  - Partial quotations: prepare_quote_subtitles(). Select an exact substring from the existing source translation; keep manual selection and the export block when uncertain.
  - Update key/configuration checks, /process gating, /api/health, .env.example, and provider-specific error messages. Review tests for the new transport without weakening validation.
  - **Done:** relevant contract/retry tests pass; a bounded live trial succeeds; interrupted work resumes; a missing key/quota error is actionable; canonical quote translation is still sourced rather than generated.

- [ ] **T06 — Make media probing and MP4 export work.** Owner: Turki. Suggested effort: 1–2 hours. Before: T01; can run alongside T04/T05.
  - Locate or configure FFmpeg and FFprobe on the release machine. Ensure the FFmpeg build supports libass, libx264, and AAC, and has suitable Arabic fonts.
  - Check duration and stream detection with the chosen clip. Verify warnings for sound not covered by the transcript are exercised on that machine.
  - Run the existing test suite where the media binaries are available. Inspect an actual exported video, not just its HTTP success status.
  - **Done:** no media-dependent test is skipped for missing binaries; MP4 plays with audio, readable Arabic/English, correct timing, and the selected appearance.

- [ ] **T07 — Update the editor for the selected backend.** Owner: Turki. Suggested effort: 1–2 hours. Before: T05 contract handoff.
  - Replace old provider names in process/help dialogs. Check upload, processing, recoverable error, ready-for-review, unresolved source, and publishable states.
  - Review real segments, choose partial-source text, check source details, and ensure free edits invalidate citation links as intended.
  - Exercise review/source/appearance tabs, timeline selection, and private edit-link recovery in a fresh browser session. Check a narrow viewport and keyboard operation.
  - **Done:** all states tested on the real project, no misleading readiness labels, and an ordinary creator can find the next step. Syntax check all three active scripts.

- [ ] **T08 — Complete and review the main clip.** Owner: Anas processes; both review. Suggested effort: 1–2 hours. Before: T02, T05, T06, T07, T15.
  - Fill every spoken segment's English; review transcript/timing, terminology, quotation identity, source text, and excerpt alignment.
  - Resolve candidates and flagged gaps; confirm actual quotations only after checking them. Ask a content mentor when the team cannot establish meaning or source identity.
  - Export SRT, source JSON, and MP4. Open the public viewer and check it independently.
  - **Done:** evaluation sheet has zero unresolved critical errors; all necessary source/excerpt confirmations are complete; all outputs play/open correctly. Save dated evidence.

- [ ] **T09 — Verify the hosted product.** Owner: Turki; Anas supports provider/source access. Suggested effort: 2–4 hours. Before: T06; finish after T08.
  - Choose a host that runs Python, FFmpeg, persistent files/SQLite, and outbound provider requests. Hosting only dist/ will not run this application.
  - Use the existing Docker/Compose/Caddy configuration where appropriate; confirm domain/HTTPS, uploaded-file persistence after restart, source access, and MP4 rendering.
  - Provide a public app entry plus a reviewed sample viewer. The sample viewer alone does not exercise upload/edit/export.
  - **Done:** a fresh browser can complete the workflow, shared viewers cannot edit, edit links work only for their holders, uploads/exports survive normal operation, and the release URL remains usable during evaluation.

## Evidence and delivery

- [ ] **T10 — Evaluate varied cases and benefit.** Owner: Anas measures; Turki observes usability; both interpret. Effort: 2–3 hours. Before: T08.
  - Use evaluation-and-release.md. Include ordinary speech, terminology, a Quran excerpt, Hadith, and an uncertainty/failure case; cases can share clips.
  - Compare a defined manual workflow with Jisr for equivalent output and review quality. Label team-only pilot evidence clearly.
  - **Done:** raw measurements and corrections are saved; claims have a sample size and limitation; unresolved failures are listed.

- [ ] **T11 — Complete source, component, and operating documentation.** Owner: Anas covers AI/sources; Turki covers code/media/hosting. Effort: 1–2 hours. Before: T04 and T09.
  - Fill sources-and-components.md, including third-party terms and media permissions. Agree a license for code the team owns; do not assume third-party data inherits it.
  - Update README, .env.example, live-example receipt, and implementation status to the actual release. Include clean-machine setup and current limits.
  - **Done:** another person can configure/run the release without receiving personal keys; licenses and sources are documented, with unresolved publication rights addressed.

- [ ] **T12 — Produce the presentation.** Owner: Turki; Anas supplies technical/evaluation evidence. Effort: 2–3 hours. Before: start now; finish after T10/T11.
  - Use presentation-draft.md and its official-template map, actual screenshots, measured results, and baseline-to-release changes. Work from a copy of docs/hackathon/presentation-template.pptx. Keep achievements distinct from proposed work.
  - Remove template guide slides 1–7 and unused layouts; replace illustrative chart figures with measurements or remove the charts. Preserve organizer logos and the template's visual identity.
  - Export a final presentation and inspect every page. Use the approved identity assets obtained from the organizers.
  - **Done:** claims are supported, screenshots are current, evidence and limits are readable, and both can present the product without overclaiming.

- [ ] **T13 — Record the demo.** Owner: Turki; Anas verifies narration/output. Effort: 1–2 hours. Before: T08 and stable UI.
  - Use video-script.md. Show a real source-backed review and exported output. Label shortened waiting time and any preprocessed footage.
  - **Done:** recording stays within the submission limit, has clear narration and captions, exposes no private links/credentials, and matches the delivered product.

- [ ] **T14 — Publish permitted code and submit.** Owner: Turki; both do final review. Effort: 45–90 minutes. Before: T09–T13.
  - Check git status and the exact publication contents, including prior history where applicable. Agree which repository is the submitted public release.
  - Publish the code the team can release, verify the live URL, upload the finished materials, and retain portal confirmation.
  - **Done:** every submitted link opens independently, the repository is public, all materials agree on features/results, and receipt/time are recorded.

## Ready-to-send handoff to Anas

“Let's focus Jisr on a complete Arabic-to-English video workflow. I’ll own the editor, export setup, hosting, presentation, and recording. Please own T03–T05: diagnose the saved project, choose the translation provider, and integrate it across translation, terminology review, and partial-quotation alignment. Preserve the transcript/timestamps and checkpoint behavior. Then let's review a complete clip together for T08 and collect actual results for T10. Send me any changes to configuration, API responses, or provider labels before I update the interface.”
