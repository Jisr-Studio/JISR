# Translation languages and source coverage

The editor remains Arabic. Each project has exactly one target language. New uploads require an explicit language choice in the interface. Legacy projects without a language migrate to English.

| Project code | Language | Direction | Quranpedia language ID / code | Translation book | HadeethEnc code |
|---|---|---|---|---|---|
| en | English | LTR | 2 / en | 1947 — Saheeh International | en |
| es | Spanish | LTR | 4 / es | 1950 — Muhammad Isa García | es |
| ur | Urdu | RTL | 12 / ur | 1966 — Muhammad Ibrahim Junagarhi | ur |
| hi | Hindi | LTR | 28 / hi | 1986 — Azizul Haq Umari | hi |
| id | Indonesian | LTR | 9 / id | 1961 — Indonesian Ministry committee, King Fahd Complex edition | id |
| zh-Hans | Simplified Chinese | LTR | 19 / zh | 1974 — Muhammad Ma Jian | zh |
| tr | Turkish | LTR | 8 / tr | 1959 — King Fahd Complex edition | tr |

These are translations of Quranic **meanings**, not translated tafsir substituted for verse translation. Quranpedia's catalog describes corrections to some editions; the live published entry and its notes are retained. Names/edition attribution come from the [Quranpedia catalog and API documentation](https://api.quranpedia.net/).

On October 6, 2026, a free public-source check verified Quran 1:1 in all seven selected books, and Hadith 3636 in all seven HadeethEnc languages. The Chinese samples use simplified characters. Both providers advertise generic Chinese `zh`, not a separate `zh-Hans` API language. This mapping does not certify the script of every record; imported text is kept verbatim, without an AI script conversion attributed to the source.

The [HadeethEnc API](https://github.com/islamhouse-dev/hadith-api) advertises all seven codes. Its per-record `translations` list is checked when present. A catalog entry does **not** imply every hadith has a published translation. The API does not supply an individual translator name: `translator: "HadeethEnc"`, `translator_status: "not_specified"` records that limitation rather than inventing an author. Arabic narrator, grading and attribution remain from the Arabic record; viewer grading/attribution use the requested-language record when supplied.

Dorar supplies Arabic hadith verification and direct record links; it does not supply these seven translations. Al-Jamhara grounds terminology with Arabic definitions; its English equivalents are additional English data, not approved equivalents for other target languages. Other languages use the model to express the grounded meaning.

## Missing or unavailable published translations

A failed/empty translation response never erases a valid Arabic reference or substitutes English. The source keeps `translation: ""`, `translation_language`, `translation_status: "unavailable"`, no translator/translation URL, and the notice **لا تتوفر ترجمة موثقة بهذه اللغة**. A network outage is treated as unavailable for the current request; `translation_fetch_error` distinguishes an unsuccessful fetch from a successful empty response. Retry can check the same preserved reference again.

The segment may retain a target-language machine translation of the speaker's words. Its origin is `machine`, and viewer captions identify the alternative as a draft, separately from published source translations. Human review does not change the source's publication status. An editor-written alternative is labelled as an editor translation. Partial **published** translations require an exact contiguous selection in that language; English selections are never reused. Selecting source wording is unavailable until a published translation is retrieved, but an existing source-wording mode can be turned off to restore the new-language speech draft.

## Language changes

The project dropdown does not change existing translations. The editor must click **إعادة الترجمة**, then confirm. The backend archives the previous segment JSON privately in `data/PROJECT/translation-history/`, clears approval, translated fields, translation selections and custom viewer captions, and starts translation using saved Arabic words/timestamps. It preserves Arabic reference identity and quotation/paraphrase/source-wording choices. A changed language cannot invoke transcription; retries reuse completed stages.

Arabic word partitions remain complete and ordered. Chinese has a 70-character cue limit and a 12-character/second review heuristic, not a whitespace word quota. Other script-specific limits are in `dist/languages.json`. Reading limits are heuristics: source quotations are never shortened by dropping words. Long captions can still need a person's rewording, segmentation or timing review; shared rendering fits them without clipping.

## Fonts and export

Arabic: existing bundled Plex/Amiri/Cairo/Tajawal/Noto Arabic options. Urdu: **Noto Nastaliq Urdu**; Hindi: **Noto Sans Devanagari**; Simplified Chinese: **Noto Sans CJK SC**; Latin targets: **Noto Sans**. Latin/Plex fallbacks cover punctuation and mixed-script metadata. Every font ships with its SIL Open Font License notice in `dist/fonts/`; see [the font manifest](../dist/fonts/README.md).

The Arabic font picker controls Arabic quotation text; the target font is selected automatically for script coverage. FFmpeg/libass shapes and wraps these fonts. Preview and MP4 share exact RGBA subtitle images and fitted sizes, at the same video dimensions and derived display times. Cache identities, render files, download filenames and translation checks include language. Chinese line breaks are explicit for libass builds without Unicode line breaking. SRT preserves Unicode and timing but cannot enforce player font, size, direction handling or appearance; use MP4 for embedded styling.

The interface, fonts and mocked translation flow were tested locally. This feature has **not** been evaluated with paid multilingual AI requests or by native-language religious reviewers. Published translation availability and model accuracy remain distinct checks.
