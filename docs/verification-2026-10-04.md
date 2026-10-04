# Local verification — October 4, 2026

The landing/onboarding, subtitle appearance controls and export changes were
verified locally before the GitHub push. Public hosting remains pending.

## Automated checks

- `python3 -m unittest discover -s tests -v`: **111 tests passed**.
  The suite uses isolated storage and mocked external providers. Its end-to-end
  case exercises actual HTTP upload, processing transport, review requirements,
  source linking, SRT/source export, real FFmpeg MP4 export/download, sharing and
  deletion. Export ticket authorization, expiration and changed-project rejection
  are covered by HTTP tests.
- `node tests/test_citation_links.js`: passed.
- `node tests/test_citation_text.js`: passed.
- Syntax checks for `app.js`, `studio.js`, `onboarding.js`, the Python server,
  container entrypoint and deployment scripts: passed.
- `git diff --check`: passed.

## Browser checks

Desktop (1280 px) and mobile (390 px) checks used the in-app browser.

- All five onboarding steps, source-confirmation example, motion pause and FAQ
  open/close worked; the studio link entered the demo editor.
- Mobile layouts had no horizontal overflow.
- Volume adjusted to 35%, mute set it to 0%, and unmute restored 35%.
- Seven font options, the 10 px minimum, synchronized size inputs, eight preset
  colors and a custom color worked. The preview selected the bundled Cairo face.
- The 720p label and subtitle-position setting were absent.
- A separate server with disposable storage accepted a real four-second MP4
  upload. Manual captions avoided paid processing calls and isolated the UI test
  from all existing user projects.
- Missing English and unresolved review disabled MP4/SRT/share; the export
  shortcut opened the unfinished segment.
- Completing the test translation/review and choosing Tajawal / 12 px / gold
  persisted after reload. MP4 preparation displayed the native download link.
- The downloaded MP4 was inspected with FFprobe: H.264 video, AAC audio,
  four-second duration. The shared viewer showed the reviewed subtitle and
  omitted edit/upload/export controls. No browser warnings/errors were recorded
  during this isolated flow.

## Remaining verification

These checks establish the changed local behavior, not public availability or
live AI service access. No paid API calls or cloud deployment were made during
this verification. The earlier ElevenLabs diagnostic reported missing
Speech-to-Text permission; that must be resolved and a fresh live processing
test completed before presenting automatic transcription to judges. Docker
image building and restart persistence on the chosen host remain pending.
