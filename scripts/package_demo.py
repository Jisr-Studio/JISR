"""Build a guarded runtime ZIP; use package_source.py for committee source delivery."""
import hashlib
import json
import zipfile
from pathlib import Path
from package_source import source_payloads

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'submission/deployment/jisr-hackathon-deploy.zip'


def main():
    payloads = {name: data for name, data in source_payloads(ROOT).items()
                if not name.startswith(('tests/', 'submission/', '.vscode/'))}
    manifest = {name: hashlib.sha256(data).hexdigest() for name,data in sorted(payloads.items())}
    payloads['release-manifest.json'] = (json.dumps(manifest,indent=2)+'\n').encode()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(OUTPUT,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(payloads.items()): archive.writestr(name,data)
    print(f'Created {OUTPUT} ({len(payloads)} files, {OUTPUT.stat().st_size:,} bytes)')


if __name__ == '__main__': main()
