# Data contract (frontend ⇄ backend)

`POST /api/process` (upload) and `GET /api/projects/{id}` both return this shape.
The reference example is `frontend/mock/project.json`. **If you change the shape, change the mock too.**

```jsonc
{
  "video_id": "abc123",
  "title": "…",
  "source_lang": "ar",
  "target_lang": "en",
  "duration": 184.2,          // seconds
  "video_url": "…",
  "segments": [
    {
      "id": 1,
      "start": 12.4,           // seconds
      "end": 17.9,
      "type": "speech",        // "speech" | "quran" | "review" (low confidence, needs a human)
      "ar": "…",               // transcript
      "en": "…",               // translation
      "ref": "…",              // short label shown in the UI (optional)
      "citation": {            // only when type == "quran"
        "surah": 94,
        "ayah": 6,             // TODO decide: ayah_start/ayah_end for multi-verse quotes
        "surah_name_ar": "الشرح",
        "surah_name_en": "Ash-Sharh",
        "partial": false,      // quote is part of the verse
        "official_text": "…",  // from the Quran DB, never from speech-to-text
        "translation": "…",    // approved translation, never machine-translated
        "translation_source": "…",
        "confidence": 0.94,    // 0..1 match score
        "status": "pending"    // "pending" | "confirmed" | "rejected" (set by the reviewer)
      }
    }
  ]
}
```

## Rules (from the challenge's scientific reference)
- Quran text and translation come **only** from approved sources, never generated.
- Low confidence → `type: "review"`. Never guess.
- Distinguish Quranic text from generated translation in the UI.
