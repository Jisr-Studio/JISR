# Subtitle readability and abbreviated Hadith retrieval — 2026-10-05

The reported I4 video displayed entire 13–17-second speech passages at once. Word coverage was validated, but the model's subtitle boundaries had no enforced readability limit. Translation now targets short connected clauses; the server rejects ordinary speech over 180 English characters or over 8 seconds with more than 12 Arabic words. One corrective response is allowed. Glossary refinement cannot expand those cues back into paragraphs. Quran/Hadith matching keeps its own rules, and connected short greetings remain intact.

Saved unreviewed speech can be repartitioned from its existing word timestamps. Reflow runs on a copy, preserves saved translations on failure, and skips reviewed text and unresolved scripture. No English word-ratio split or fabricated timing is used. A prompt instruction also requires each English clause to correspond only to its exact Arabic word range. This instruction does not establish model accuracy; editors still review meaning and timing.

The reported Hadith transcript contains `سفرا` where the source has `صفرا`, and compresses several words from the published narration. Its literal-match rejection was therefore appropriate, but retrieval stopped without offering a relevant source. A bounded HadeethEnc fallback now searches short anchors, filters unrelated results, and checks complete Arabic/English records. Only a unique literal match can attach automatically. Other plausible records are comparison suggestions with source text, narrator, grade, attribution, and an explicit paraphrase-link action. Linking never confirms review.

## Live verification

- I4 (`e549da9fc5524685be61ba02b8d5cb86`): 8 → 15 cues; its opening 13.54-second paragraph became five cues. Original STT words and timestamps were preserved.
- I1 (`d2516fb34e53426db409e2e8de05531c`): 7 → 12 cues; its already-reviewed Quran citation was unchanged. Two revised English clauses were manually aligned to their correct Arabic ranges after browser inspection.
- HadeethEnc returned [record 5499](https://hadeethenc.com/ar/browse/hadith/5499). The actual comparison and linking workflow was exercised in the browser. I4 now links the abbreviated wording as a paraphrase, with source Arabic, English, narrator, grade, explanation, and direct source links; review remains pending.
- A real I4 MP4 was rendered after the changes: 15 cues, 8,673,244 bytes. Its draft warning still reports unresolved review. A decoded frame confirms the opening translation appears as a short cue instead of the original paragraph.
- Python regression coverage includes readability repair, complete word/timing coverage, preservation on provider failure, greetings, reviewed-source preservation, glossary expansion, unrelated Hadith results, full-record rechecking, and explicit source suggestions. Existing rendering/export and browser-helper tests also pass. The Windows run skips the Unix-only deployment module.

Scope: this fixes oversized ordinary-speech cues and provides recoverable retrieval for abbreviated Hadith wording. It does not certify all machine translations or turn a paraphrase into a literal source quotation.

## Quran boundaries across adjacent cues

I5 exposed another failure: punctuation split Quran 33:56, the model retained `عباد الله` with its first half, and per-cue verification rejected that mixed segment while accepting the second half. The pipeline now checks normalized, contiguous source-text matches across up to two adjacent cues on each side of a known Quran candidate or verified source. Original word timestamps determine the new boundaries; only residual speech receives machine translation. The complete recited verse receives its source Arabic and English.

Recovery requires an unambiguous exact source span and aligned source English. It cannot cross a gap over two seconds, a conflicting citation, reviewed text, an explicit source-caption override, or Arabic edits that no longer match the saved words. Partial recitations remain partial; unrelated speaker words are never appended to the canonical verse. Source failures leave existing cues intact, and residual-translation failure commits no boundary changes. This conservative pass does not solve every transcription error or discover scripture without any Quran location candidate.

The reported I5 project was repaired from its saved word timings without repeating transcription: `عباد الله` at 0.34–0.94 seconds, then the complete recited Quran 33:56 at 1.24–7.06 seconds. The other five cues were preserved exactly. The verse uses its existing source translation and still requires human review. Its generated bilingual SRT contains the complete verse and source caption.
