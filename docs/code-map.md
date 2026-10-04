# JISR code map

## Active application

- `server.py`: Python HTTP API, persistence, processing, source matching, exports, and static file serving. This remains at the root to preserve the test imports and deployment entry point.
- `subtitle_png.py`: standard-library PNG decoder for alpha bounds; the shared subtitle renderer uses it to fit long cues without clipping.
- `dist/index.html`: HTML shell, video controls, transcript list, source panel, and dialogs.
- `dist/js/app.js`: API requests, project loading, editing, review, source details, and exports.
- `dist/js/subtitle-preview.js`: bounded image cache, next-cue preload, failed-load retry, and cancellation guards for the shared PNG preview.
- `dist/js/studio.js`: start screen, studio tabs, segment timeline, review controls, and processing status. It loads after `app.js` and uses its existing state.
- `dist/js/splash.js`: once-per-session intro; skips project/share links and reduced-motion users.
- `dist/css/style.css`: underlying editor layout.
- `dist/css/studio.css`: midnight/amber theme, responsive views, and motion.
- `dist/favicon.svg`: Mihrab logo.
- `tests/`: existing backend and integration tests.
- `scripts/check_sources.py`: opt-in checks against public citation services.
- `docs/`: data contract, source policy, implementation notes, and saved UI previews.
- `data/`: generated projects and database; excluded from Git.

`dist/` is the served frontend source, not a generated build. There is no frontend build step. Do not edit the archived prototype to change the live site.

## VS Code

Use **Terminal → Run Task → JISR: Run app** to start port 8766, **Run and Debug → JISR: Debug app** to debug, or **Tasks: Run Test Task** to run the suite. Python 3.11+ is required; no backend package installation is needed. Select your installed Python interpreter in VS Code. The test explorer uses unittest in `tests/`.

The source-check task makes external requests; run it explicitly when needed. MP4 exports and integration tests require FFmpeg.

## Historical prototype

`archive/prototype/` preserves the first frontend demo and unfinished FastAPI backend. Its files are excluded from workspace search by default. Current tasks and Docker use the active application.

## Deployment

`Dockerfile`, `compose.yaml`, and `Caddyfile` remain at the root. The Docker image copies the entire `dist/` directory, including its CSS and JS subdirectories.
