# Jisr presentation draft

> Current local validation after integration: 90 Python tests passed, including real MP4 export, plus JavaScript citation checks. Earlier test counts below record the starting baseline; use current measured results in the final submission.

Prepared content for Turki to turn into the team's final presentation. The order below is our proposed structure. Replace bracketed evidence slots only after checking the output. Use the accepted project name and organizer identity assets.

## Official template now available

Use [the unchanged organizer template](../hackathon/presentation-template.pptx) as the design source. It contains 31 slides: slides 1–7 explain its use; the rest are optional layouts. Work in a new copy. The following mapping keeps the existing eight-part content draft concise:

| Jisr draft section | Original template slide | Why it fits |
|---|---|---|
| 1. Project introduction | 8 | Cover with name and short description |
| 2. Creator's task | 12 | Problem explanation and supporting observation |
| 3. Review workspace | 26 | Actual interface screenshots with short captions |
| 4. AI and sources | 24 | Input, processing, output, and benefit workflow |
| 5. Concrete review example | 13 | Source/editor screenshot beside its explanation |
| 6. Results | 17 | Comparison table with sample/method note |
| 7. Operation and continuation | 20 | Readable summary of dependencies, cost, and limits |
| 8. Delivered work and links | 31 | Closing links; summarize development evidence verbally and in notes |

If the final deck needs a separate team slide, layout 19 is available; remove the two unused member slots. This is a choice, not a mandatory ninth slide. Retain details that prove new work in the results/operating sections if they do not fit the closing slide.

Template design guidance: Readex Pro; main title 45 pt, body 24 pt, caption 18 pt; bold titles and regular body text. Colors are navy #12183F, purple #6150EA, turquoise #2EF2C2, and pale blue-white #F2F4FF. Preserve image proportions and identity assets. Check that the font is available when editing/rendering.

Delete guide slides, unused samples, bracketed instructions, and example data before submission. The sample charts contain illustrative values; none are Jisr results. These are template-use instructions, not claims about required content or compulsory slide count.

## Slide 1 — Jisr / جسر

**Arabic Islamic video. English subtitles. Traceable references.**

Jisr helps content creators translate Arabic Islamic videos, review Quran and Hadith quotations against sources, and export a publishable video.

Turki — product experience, frontend, integration and delivery.
Anas — AI engineering, translation and source processing.

Visual: one clear screenshot of the working editor with a real reviewed clip. The existing docs/previews images are design references; capture fresh evidence for the release.

Speaker note: “We built Jisr for the editor preparing Arabic Islamic content for English-speaking viewers.”

## Slide 2 — The creator's task

**One video requires several connected jobs.**

Transcribe speech → time subtitles → translate meaning → verify quotations → review → export.

When these steps are disconnected, the creator must reconcile text, timing, terminology, and sources manually.

Primary operator: Arabic-speaking Islamic content creator/editor.
End beneficiary: English-speaking viewer.

Evidence slot: [one observed creator difficulty, participant count, date, and how you learned it]. Until that exists, describe this as the problem being tested rather than a proven widespread finding.

Speaker note: Explain one concrete segment with a religious term or quotation; avoid unsupported market-size claims.

## Slide 3 — One review workspace

**Upload → process → review → export.**

- A timed Arabic transcript and English draft.
- Quotations linked to retrieved references.
- Review tools for text, timing, uncertainty, and subtitle appearance.
- MP4, SRT, and reference-list output after required checks.

Visual: four screenshots from the same project, each showing a meaningful step.

Speaker note: “The creator keeps control of the final wording. Completing processing and approving publication are separate steps.”

## Slide 4 — How the AI and sources work

Audio → ElevenLabs transcription and word timestamps.

Transcript → [chosen translation provider/model] → speech translation, quotation candidates, detected terminology.

Candidates → Quranpedia / Dorar / HadeethEnc → source text and available published translations.

Terms → Al-Jamhara → definitions and available English equivalents for translation review.

Editor review → FFmpeg and subtitle/reference exports.

Source matching and human confirmation remain separate. A partial quotation uses its corresponding reference excerpt. Uncertain alignment remains unresolved until reviewed.

Visual: a simple flow diagram, with generated speech translation and sourced quotation translation labeled distinctly.

Evidence slot: [provider decision, model, sample processing receipt, source record screenshot].

Speaker note: Anas explains where AI operates and what the server validates. Do not describe lexical source matching as a model's religious judgment.

## Slide 5 — A concrete review example

**Follow one quotation from audio to exported subtitles.**

Show the original spoken excerpt, its source reference, corresponding English excerpt, and the editor's final confirmation.

Show what happens if the text is changed or the excerpt cannot be resolved: it needs another review before publication.

Evidence slot: [real source-backed segment screenshot + exported result]. The previous Maryam example is historical evidence only until recovered and reviewed.

Speaker note: Use one checked example. Do not use the silent illustrative frontend demo as proof of processing accuracy.

## Slide 6 — Results we can reproduce

| Measurement | Manual comparison | Jisr | Evidence |
|---|---|---|---|
| Human working time for equivalent reviewed output | [minutes] | [minutes] | [record] |
| Machine waiting time | N/A or [minutes] | [minutes] | [record] |
| Meaning/terminology corrections | [count] | [count] | [review sheet] |
| Correct quote source/excerpt checks | [passed/total] | [passed/total] | [review sheet] |
| Completed upload-to-export attempts | N/A | [passed/total] | [run log] |

State clip durations, sample size, reviewers, and limitations below the table. A small team pilot is preliminary evidence.

Today’s verified baseline: 74 local tests passed; three media-dependent checks skipped. Replace this with the release test result and retain the difference. Mocked-provider tests verify integration behavior, not live translation quality.

Speaker note: Present measured results only. If something was not measured, remove its improvement claim.

## Slide 7 — Operation and continuation

The product needs a Python host, media processing, provider credentials, source-service access, persistent storage, and an editor who reviews the output.

- Measured provider cost for test clip: [amount and currency].
- Human review effort: [minutes per tested clip].
- Hosting estimate: [amount/time period, source and date].
- Dependencies and failure handling: [chosen provider, quota behavior, retained checkpoints].
- Current limits: [supported input conditions, translation quality boundaries, storage/deletion behavior].

Next steps after submission: expand evaluated clips; improve the observed failure points; pilot with creators; confirm source permissions and operational cost at larger scale.

Speaker note: State what is required to keep Jisr usable. No revenue or adoption claim is needed without evidence.

## Slide 8 — What we delivered during development days

| Starting baseline | October 4–6 additions | Evidence |
|---|---|---|
| Partial translation and provider interruption | [completed integration and runs] | [commits/receipts] |
| Local editor and deployment configuration | [verified product journey/live host] | [run/link] |
| Local reference tests | [real reviewed examples/evaluation] | [review sheet] |

Live application: [public URL].
Reviewed example: [public viewer URL].
Code and run instructions: [public repository URL].

Closing line: “Jisr helps creators make Islamic video content accessible in English while keeping the translation and its references reviewable.”

## Speaker rehearsal

Turki leads the user problem, editor journey, and delivery. Anas explains the processing and evaluation. Keep technical detail behind the concrete demonstration. Agree answers for: source selection, uncertain quotations, cost, provider outages, measured benefit, and work completed during the challenge.

Before export: replace/remove every bracketed slot, inspect all slides, check current screenshots, and make sure each claim has evidence. Keep a source/evidence note with the presentation working files.
