# Source policy

Reference: the [AI Challenge scientific package](https://islamicaich.org/files/HackathonFile/BI5ZrlfRZqpzIVd6z1zaYSiNBC06uRtZ6PovwtQO.pdf), pages 3, 4, 5, and 8. This document maps the current implementation to the package; it does not certify every source record or translation.

| Content | Current implementation | Boundary |
|---|---|---|
| Quran text and English translation | Quranpedia Hafs text and Saheeh International, book 1947 | Matched against fetched text. Full sources remain in the citation record; subtitles use a corresponding source excerpt for partial quotations. Human confirmation is required. |
| Quran commentary | Dorar tafsir, named in the package | Fetch the actual section indexed for the verse. Preserve references and disclose adjacent-verse scope. Retrieval failure yields a source link with unavailable status, never generated commentary. |
| Hadith attribution and grading | Dorar search results, including narrator, scholar, grade, and attribution | A lexical match is a candidate pending human confirmation. Report the source's grade literally; do not turn it into an AI confidence percentage or claim every match is authentic. |
| Hadith translation and explanation | Automatically search HadeethEnc after a Dorar match; attach a unique complete matching record, or allow editor selection/manual linking | Auxiliary provider, not a source explicitly named in the package. Automatic matching retains separate Dorar verification metadata. Ambiguous, unavailable, or incomplete results retain the machine draft and require review; the model never generates commentary. |
| Sensitive terminology | Gemini detects terms from the original transcript; exact Al-Jamhara records supply definitions and published English terms when available. Page 8's ten-term sample glossary provides baseline guidance. | Retrieval is on demand, not a local corpus. Missing or ambiguous matches flag the affected speech for review. Arabic-only definitions do not become approved English equivalents. Source-guided sentence translation remains a machine draft. |
| Ordinary speech | Gemini translation using the original transcript | Preserve context and uncertainty; do not add rulings, answers, or claims. The transcript is input data, not instructions. |

Source texts, English translations, commentary, and generated speech translations remain distinct in the API. Editing a citation's Arabic or English removes its reference and requires another review. Export and public sharing remain blocked until unresolved segments are addressed and every linked citation is confirmed.

Partial quotation alignment selects an exact contiguous source-English substring and a canonical Arabic excerpt. The model does not generate the scripture translation. A failed or uncertain alignment leaves the existing draft visible with `alignment_status: needs_selection`; confirmation and publication remain blocked until the editor selects a source excerpt. The local tests cover both automatic selection with mocked Gemini and the manual API flow. Live Gemini alignment quality remains unverified until API keys and real recordings are supplied.

The saved `source-check.json` is a timestamped check of seven public-service samples, including two dictionary terms and one automatic Hadith translation match. It stores response fields and content hashes rather than a scraped corpus. It does not establish global matching accuracy, translation quality, redistribution rights, or live paid-provider compatibility. Complete a real-video review with API keys before public launch.
