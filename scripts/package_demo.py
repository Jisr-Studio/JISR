"""Build a runtime-only ZIP for a fresh deployment repository, without secrets."""

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "submission" / "deployment" / "jisr-hackathon-deploy.zip"


def main():
    files = [ROOT / name for name in (
        "Dockerfile", ".dockerignore", "docker-entrypoint.py", "server.py", "subtitle_png.py", "render.yaml",
        "docs/deployment.md", "scripts/check_deployment.py",
    )]
    files += sorted(path for path in (ROOT / "dist").rglob("*") if path.is_file())
    payloads = {}
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise SystemExit(f"Refusing linked file: {path.relative_to(ROOT)}")
        payloads[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    payloads[".gitignore"] = (ROOT / ".gitignore").read_bytes()
    payloads["README.md"] = (
        "# JISR hackathon application\n\n"
        "Full Python/Docker application with the Arabic landing page and editor.\n\n"
        "Deploy using [the hosting guide](docs/deployment.md) and `render.yaml`.\n"
        "API keys must be entered in hosting secret fields. This package contains\n"
        "no local projects, credentials or Git history.\n"
    ).encode()
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payloads.items())}
    payloads["release-manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payloads.items()):
            archive.writestr(name, data)
    print(f"Created {OUTPUT} ({len(payloads)} files, {OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
