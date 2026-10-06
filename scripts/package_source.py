"""Package the source repository without local secrets, projects or build artifacts."""
import hashlib
import json
import os
import sqlite3
import zipfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'submission/deployment/jisr-final-source.zip'
PRIVATE_DIRS = {'.git','.venv','venv','__pycache__','data','work','.openai','.pytest_cache','node_modules','archive','__MACOSX'}
PUBLIC_DEMOS = {'dist/demo.mp4'}


def source_payloads(root):
    root = root.resolve()
    credentials = []
    database = root/'data/jisr.sqlite3'
    if database.is_file():
        # Read only: existing private capability links must not leak into docs.
        with closing(sqlite3.connect(database.as_uri()+'?mode=ro', uri=True)) as con:
            for row in con.execute('SELECT edit_token,share_token FROM projects'):
                credentials.extend(str(value).encode() for value in row if value)
    if (root/'.env').is_file():
        for line in (root/'.env').read_text(encoding='utf-8-sig').splitlines():
            if line.lstrip().startswith('#') or '=' not in line:
                continue
            key,value = line.split('=',1)
            value = value.strip().strip('"').strip("'")
            if ('KEY' in key or 'TOKEN' in key) and len(value)>=12:
                credentials.append(value.encode())
    payloads = {}
    for folder, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in PRIVATE_DIRS and not name.startswith('tmp')
                         and not (Path(folder)/name).is_symlink())
        for name in sorted(files):
            path = Path(folder)/name
            relative = path.relative_to(root).as_posix()
            if relative.startswith('submission/screenshots/'):
                continue
            if (name == '.env' or name.startswith('.env.') and name != '.env.example'
                    or path.suffix.lower() in {'.pyc','.log','.zip','.sqlite3','.sqlite','.db','.exe'}
                    or '.sqlite3-' in name or relative == 'release-manifest.json'):
                continue
            if path.suffix.lower() in {'.mp4','.mov','.webm','.mkv','.wav','.mp3'} and relative not in PUBLIC_DEMOS:
                raise ValueError('Unreviewed media cannot be packaged: '+relative)
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError('Linked file cannot be packaged: '+relative)
            content = path.read_bytes()
            if any(secret in content for secret in credentials):
                raise ValueError('Configured credential found in: '+relative)
            if name == '.env.example':
                for line in content.decode('utf-8-sig').splitlines():
                    if line.lstrip().startswith('#') or '=' not in line: continue
                    key,value=line.split('=',1)
                    if ('KEY' in key or 'TOKEN' in key) and value.strip():
                        raise ValueError('Configuration template keys must be blank')
            if len(content)>=100*1024*1024:
                raise ValueError('File exceeds GitHub source size limit: '+relative)
            payloads[relative] = content
    return payloads


def main():
    payloads = source_payloads(ROOT)
    manifest = {name:hashlib.sha256(data).hexdigest() for name,data in sorted(payloads.items())}
    payloads['release-manifest.json'] = (json.dumps(manifest,indent=2)+'\n').encode()
    (ROOT/'release-manifest.json').write_bytes(payloads['release-manifest.json'])
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(OUTPUT,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,content in sorted(payloads.items()): archive.writestr(name,content)
    print(f'Created {OUTPUT} ({len(payloads)} files, {OUTPUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
