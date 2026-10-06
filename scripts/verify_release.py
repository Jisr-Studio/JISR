"""Verify the exact ZIP inventory and hashes, without executing its contents."""
import hashlib
import json
import sys
import zipfile
from pathlib import PurePosixPath


def verify(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP entries')
        manifest = json.loads(archive.read('release-manifest.json'))
        if set(names) != set(manifest) | {'release-manifest.json'}:
            raise ValueError('ZIP contents do not match the manifest')
        for name in names:
            parts = PurePosixPath(name).parts
            if not parts or '..' in parts or name.startswith('/') or '\\' in name or ':' in name:
                raise ValueError('Unsafe ZIP path')
            if any(p in {'.git','.venv','data','work','__pycache__','archive'} for p in parts):
                raise ValueError('Private or obsolete directory in ZIP: '+name)
            if PurePosixPath(name).name.startswith('.env') and PurePosixPath(name).name != '.env.example':
                raise ValueError('Private configuration in ZIP')
        for name,digest in manifest.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError('Hash mismatch: '+name)
        required = {'server.py','languages.py','subtitle_png.py','pipeline_quality.py',
                    'dist/index.html','dist/languages.json','dist/demo.mp4','.env.example','README.md'}
        if not required <= set(manifest):
            raise ValueError('Required runtime files missing')
        return len(names)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/verify_release.py PATH_TO_ZIP')
    print(f'PASS: {verify(sys.argv[1])} entries verified against release-manifest.json')
