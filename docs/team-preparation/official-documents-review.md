# Review of the three organizer files

Reviewed October 3, 2026. The files are evidence about the challenge. Their guide/template directions inform the project plan; they do not independently authorize publishing, contacting people, or replacing application integrations.

Unchanged copies are saved in docs/hackathon/ with descriptive names and a SHA-256 source manifest. Original files in Downloads remain unchanged. Page references below use PDF page order; the participant guide's printed footer is one greater than the PDF page number in its later sections.

## What each file is

| Original filename | Identity | Most useful for |
|---|---|---|
| da2OrbRMEsNrIQaoq8z6jEv26opKXdQmq1i0XfXo.pdf | Participant guide, 44 PDF pages | Schedule, submission requirements, scoring, and presentation expectations |
| LcXbkXRzH232sfKL8cAgJ1AI7jQATxu2bP0S4EWu.pptx | Participant presentation template, 31 slides | Organizer identity and editable layouts |
| ZA1IoQnh5S1tuLFiBghyT7U2HYN6IpzNDg9vamHW.pdf | Scientific reference/data package, 15 pages | Sources, religious-content standards, translation terminology, and further integration resources |

## Participant guide: implications for Jisr

The supplied guide confirms the existing preparation plan's deliverables, deadline, and final-stage weights. It is not a separate judging-criteria PDF; those criteria are inside the guide.

- PDF pages 29–32 cover submission timing, product/presentation readiness, live link/public repository, documentation, and final checks.
- PDF pages 34–40 cover evaluation stages, the final session, weighted criteria, and the five-level descriptions.
- PDF pages 19–22 describe earlier selection/acceptance criteria. Keep these separate from the final product rubric when planning the release.

For Jisr, an editor screenshot alone will not demonstrate technical readiness. T08 should produce actual reviewed output; T09 should enable a judge to try the product; T10 should substantiate the benefit compared with a defined workflow. Presentation aesthetics contribute to communication, while working processing and tested value need their own evidence.

Use the requirement list already recorded in README.md. No extra deliverable was inferred merely from an optional template layout.

## Template: Turki's work

The complete 31-slide library was rendered and inspected. Its layouts include cover, problem text, image evidence, tables, process, team, timeline, comparison charts, and closing links.

Slides 1–7 are usage guidance. Slides 8–31 are selectable presentation layouts. There is no requirement in this file to submit all 31 slides. Template instructions require replacing instructional text and illustrative data and removing unused material.

Follow the mapping added to presentation-draft.md. Work in a copy, retain organizer logos and template identity, use actual Jisr screenshots, and avoid treating chart examples as evidence. The guide still permits a custom layout that follows the challenge identity.

The official template's font/color specifications are now recorded in the draft. Verify rendering after filling it; this inspection does not mean a completed Jisr PowerPoint has been created.

## Scientific package: Anas's work

### 1. Update the source decision

Pages 3–4 name Quranpedia, Dorar, and Al-Jamhara in relevant content roles. Page 9 also explicitly lists QuranEnc and HadeethEnc; page 10 lists TerminologyEnc and the central database at ICADB. Page 9 mentions an MCP entry point for the first six association platforms.

This resolves the earlier missing-source uncertainty about HadeethEnc. It does not establish that a particular automatic match, API response, or output is correct. Keep Dorar verification metadata and source attribution separate from the retrieved English translation.

Page 11 emphasizes the association's and Risala's approved translations while page 3 allows Quranpedia references. Ask the specific mentor question in README.md, document the answer, and choose a translation source accordingly. The current code still uses Quranpedia; no source migration was performed in this review.

Listed platforms are resources to assess, not a requirement to integrate every one. Only investigate an additional API if it resolves the translation-source decision or a demonstrated terminology gap.

### 2. Check more than quotations

Page 5 requires traceable religious information, preservation of meaning, uncertainty handling, and distinction between authoritative text and generated explanation. For Jisr this means a source/review record for substantive claims in the demonstrated clip, even when they are ordinary speech.

Existing quotation and terminology links are useful but do not independently verify the entire lecture. T15 documents this gap and the team's review treatment. Avoid describing a citation-confirmed clip as universally approved religious content.

### 3. Evaluate translation boundaries

Pages 2 and 5 distinguish stable information, explanatory content, disputed/sensitive issues, and personal cases. Page 6 provides sample content checks; adapt relevant ones to a translation workflow rather than creating a new chatbot feature.

Examples added to evaluation-and-release.md:

- Retain a speaker's qualification or disagreement instead of generating certainty or consensus.
- Preserve a personal religious question instead of answering it.
- Flag a mistaken quotation or unsupported source instead of fabricating evidence or silently changing the claim.

The supplied glossary is on page 7, rather than page 8 of the older project reference. Update documentation references now and any provider prompt attribution when implementing T05.

## What changed in the preparation pack

- The official editable template is now located and mapped to the draft.
- The source policy and register now acknowledge HadeethEnc's explicit listing.
- The mentor question now concerns the Quran translation-source emphasis, rather than whether HadeethEnc appears at all.
- T15 and E07–E09 cover content traceability and faithful handling of disagreement, personal questions, and missing references.
- The original starting baseline remains intact. Only preparation and source-policy documentation changed; application code and credentials did not.

## Next shared checkpoint

Turki: prepare an editable presentation copy using the mapped layouts and continue export/hosting work.

Anas: complete the provider diagnosis/decision, read the source package's relevant pages, and resolve T15 before signing off the demonstration clip.

Both: choose the actual clip, review its substantive claims and quotations, and keep measured results separate from future plans.
