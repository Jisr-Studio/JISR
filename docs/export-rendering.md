# Subtitle preview and draft export verification

Verified locally on Windows on October 4, 2026, with the saved I3 project and FFmpeg. No transcription or translation API was called for these checks.

## Rendering change

The old browser preview used CSS text while MP4 used a separate ASS canvas at 1280×720, with different font scaling and disabled wrapping. Real projects now use a shared RGBA subtitle image produced by FFmpeg/libass, at native video resolution. The server uses a 480-pixel logical width, fits long cues, caches images by content and appearance, and uses those exact images in both views. A renderer version in the MP4 manifest invalidates previous cached exports.

The preview preserves the uploaded video's colour and opacity; the demo's grayscale/dimming styling no longer applies to real projects. Timing gaps clear the subtitle, and late image loads cannot restore a previous cue.

## Actual I3 export

- Requested appearance: Amiri, size 42, white, bilingual, background enabled.
- Source and output: 1024×576, 30 fps, approximately 59.23 seconds.
- Video encode: H.264 CRF 18, medium preset, original dimensions.
- Audio: original HE-AACv2 stream copied. SHA-256 of the encoded audio payload matched the source.
- Output size: 8,330,190 bytes.
- The Quran cue's preview endpoint returned byte-for-byte the same PNG used by the exported video. Its effective logical font size was 42.
- The long bilingual Hadith cue fitted at 35.7 in both views; it was not clipped. A selected maximum size is reduced only when the cue does not fit.
- Exported frames at 15 and 35 seconds were visually inspected for Arabic shaping, English wrapping, and source-caption readability.
- Browser inspection confirmed the native PNG dimensions and size 42, with original video opacity and colour. The screenshot was taken at a narrow viewport; scaling preserved the same subtitle layout.

Low-detail source footage stays low-detail; the higher-quality encode reduces additional compression loss rather than reconstructing missing detail. SRT stores text/timing and does not carry the MP4's appearance.

## Draft export policy

Private SRT/MP4 exports require completed or failed processing with nonempty segments, plus editor access. They no longer require every cue to be confirmed. The export dialog shows a review warning and leaves the review state unchanged. Empty/processing projects remain unavailable for export. Public viewing links still require completed human review.

The I1 project retained six pending cues while the browser successfully prepared both SRT and MP4 drafts and displayed their download links alongside the warning. HTTP tests cover draft MP4 preparation, ticket downloads, editor permissions, unchanged review flags, and rejection of downloads after a concurrent edit. Unresolved partial quotations keep the spoken excerpt rather than inserting a full reference; missing English displays `[Translation unavailable]` instead of dropping the cue.

## Automated verification

With `FFMPEG_PATH` configured, the October 5 gap audit ran 120 test entries: 119 passed and one Unix-only container deployment module was skipped on Windows. The real-video integration test ran, including shared-image equality, MP4 encoding, and cache invalidation. PNG tests exercise all five filters and fitting long bilingual text. JavaScript syntax, citation-link/text, and preview lifecycle checks passed. These tests do not establish live translation accuracy or deployment readiness.

## October 5 gaps closed

- A 10-ms cue at 0.111–0.121 seconds disappeared completely in a 60-fps export because image timestamps were rounded to a 25-fps time base. It now appears on frame 7 (approximately 0.1167 seconds) and is absent from frames 6 and 8; all 24 frames of the 0.4-second test video are preserved.
- A 321×181 video failed to encode. Display geometry now normalizes to an even square-pixel canvas; the export succeeds at 322×182. A real rotated, anamorphic fixture also exports at the expected 180×428 display size.
- A failed preview request no longer leaves the cue permanently hidden. One retry handles temporary failures; preloading and a bounded object-URL cache reduce repeated loads. Tests cover stale responses, gaps, access denial, project resets, eviction, and cleanup.
- Saving the I3 Quran cue unchanged retained its original transcript and source, and the browser remained at 34.36 seconds with the PNG visible. Same-project updates no longer reload the video; style saves are serialized.
- The export dialog now displays all server warnings, including failed processing and unresolved partial quotations. Missing/whitespace English uses the same placeholder in SRT and MP4.
- Confirmed-source JSON excludes unconfirmed, unaligned, untranslated, or still-flagged records; review counters use the same criteria as the publication check.
- Interrupted manifest and PNG metadata files are repaired on demand. Invalid style sizes and non-object JSON return client errors rather than truncating input or failing unexpectedly.
- Static fonts/scripts use explicit MIME types rather than Windows registry associations. Video/download ranges clamp a valid end offset to the file length and return a proper 416 response for invalid/empty ranges.

The final I3 export was regenerated with `shared-png-v3` at 1024×576 (8,343,354 bytes). The Quran preview still equaled the image used by MP4, and the encoded audio payload still matched the original. The local deployment smoke check passed, and the runtime ZIP was rebuilt with the new preview helper. No paid AI calls were made for this audit.


## Multilingual renderer

`shared-png-v10-multilingual` includes language and the shared language/caption policy in PNG/MP4 cache identities. Bundled target fonts are Noto Sans (Latin), Noto Nastaliq Urdu, Noto Sans Devanagari and Noto Sans CJK SC, with Latin/Plex fallbacks. Arabic and target translations have separate font runs but use one shared RGBA image for preview and MP4. Urdu lines get an explicit RTL marker, including source lines beginning with Latin publisher names. Chinese wraps by characters, including viewer captions. MP4 and manifests use language-specific paths; old download tickets are invalidated by project revisions. SRT contains Unicode and timing, with RTL markers for Urdu; it cannot enforce font or size in another player. See [language coverage](languages.md).
