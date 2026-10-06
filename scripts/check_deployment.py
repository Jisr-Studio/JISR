"""Read-only public smoke check; does not upload videos or call paid AI APIs."""

import json
import sys
import urllib.parse
import urllib.request


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/check_deployment.py https://YOUR-ACTUAL-HOST")
    base = sys.argv[1].rstrip("/")
    parsed = urllib.parse.urlsplit(base)
    local = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if (not parsed.hostname or parsed.username or parsed.password or parsed.path
            or parsed.query or parsed.fragment or (parsed.scheme != "https" and not (local and parsed.scheme == "http"))):
        raise SystemExit("Use the HTTPS root URL without credentials, project links or query parameters")
    checks = (
        ("/", b"JISR", "text/html"),
        ("/js/app.js", b"function", "javascript"),
        ("/js/subtitle-preview.js", b"JisrSubtitlePreview", "javascript"),
        ("/js/languages.js", b"JisrLanguages", "javascript"),
        ("/languages.json", b'"zh-Hans"', "application/json"),
        ("/source-caption-labels.json", b'"surahs"', "application/json"),
        ("/css/onboarding.css", b"{", "text/css"),
        ("/fonts/plex.ttf", None, "font"),
        ("/fonts/noto-latin.ttf", None, "font"),
        ("/fonts/noto-urdu.ttf", None, "font"),
        ("/fonts/noto-devanagari.ttf", None, "font"),
        ("/fonts/noto-cjk.otf", None, "font"),
        ("/demo.mp4", b"ftyp", "video/mp4"),
    )
    with urllib.request.urlopen(base + "/api/health", timeout=30) as response:
        health = json.load(response)
    if not health.get("ok") or not health.get("ffmpeg"):
        raise SystemExit("FAIL: backend health or FFmpeg configuration")
    print("PASS: backend and FFmpeg configured")
    if not health.get("openai") or not health.get("elevenlabs"):
        raise SystemExit("FAIL: configure both AI keys before judges test automatic processing")
    print("PASS: AI keys configured (live permission/model checks still required)")
    for path, marker, content_type in checks:
        with urllib.request.urlopen(base + path, timeout=30) as response:
            data = response.read(262144)
            if response.status != 200 or not data or content_type not in response.headers.get("Content-Type", ""):
                raise SystemExit("FAIL: asset " + path)
            if marker and marker not in data:
                raise SystemExit("FAIL: unexpected asset content " + path)
        print("PASS: " + path)
    print("Complete a fresh-session upload, live processing, review, export and restart-persistence check before submission.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit(f"FAIL: {type(error).__name__}: {error}")
