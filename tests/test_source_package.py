"""Release packaging must not disclose configuration or private projects."""
import importlib.util
import tempfile
import sqlite3
import hashlib
import json
import zipfile
from unittest.mock import patch
from contextlib import closing
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('jisr_source_package',Path(__file__).resolve().parents[1]/'scripts/package_source.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class SourcePackageTests(unittest.TestCase):
    def fixture(self,root,name,content):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)

    def test_private_and_generated_artifacts_are_excluded_but_runtime_tests_and_licenses_kept(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ('.env','data/project/original.mp4','data/jisr.sqlite3','data/jisr.sqlite3-wal',
                         'work/run.log','.venv/private.txt','__pycache__/server.pyc','.git/config',
                         'submission/deployment/old.zip','ffmpeg.exe'):
                self.fixture(root,name,b'private')
            (root/'data/jisr.sqlite3').unlink()
            with closing(sqlite3.connect(root/'data/jisr.sqlite3')) as con:
                con.execute('CREATE TABLE projects (edit_token TEXT,share_token TEXT)')
                con.commit()
            public=('.env.example','server.py','languages.py','tests/test_languages.py','docs/data-contract.md',
                    'dist/languages.json','dist/fonts/noto-cjk.otf','dist/fonts/noto-cjk-OFL.txt','dist/demo.mp4')
            for name in public: self.fixture(root,name,b'OPENAI_API_KEY=\n' if name=='.env.example' else b'public')
            self.assertEqual(set(package.source_payloads(root)),set(public))

    def test_configured_key_leak_is_rejected_without_printing_its_value(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);secret=b'private-example-credential'
            self.fixture(root,'.env',b'OPENAI_API_KEY='+secret)
            self.fixture(root,'oops.md',b'do not ship '+secret)
            with self.assertRaises(ValueError) as error: package.source_payloads(root)
            self.assertIn('oops.md',str(error.exception));self.assertNotIn(secret.decode(),str(error.exception))

    def test_template_keys_must_be_blank(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root,'.env.example',b'OPENAI_API_KEY=filled')
            with self.assertRaisesRegex(ValueError,'must be blank'): package.source_payloads(root)

    def test_unreviewed_media_outside_private_storage_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root,'my-video.mp4',b'private footage')
            with self.assertRaisesRegex(ValueError,'Unreviewed media'): package.source_payloads(root)

    def test_archived_prototype_and_duplicate_submission_images_are_not_shipped(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ('archive/prototype/old.py','archive/prototype/frontend/assets/demo.mp4',
                         'submission/screenshots/duplicate.png','old.db','old.sqlite'):
                self.fixture(root,name,b'old')
            self.fixture(root,'dist/demo.mp4',b'demo')
            self.assertEqual(set(package.source_payloads(root)),{'dist/demo.mp4'})

    def test_private_project_links_in_docs_are_rejected_without_disclosing_token(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir()
            secret='private-capability-for-test'
            with closing(sqlite3.connect(root/'data/jisr.sqlite3')) as con:
                con.execute('CREATE TABLE projects (edit_token TEXT,share_token TEXT)')
                con.execute('INSERT INTO projects VALUES (?,?)',(secret,'share-capability-test'))
                con.commit()
            self.fixture(root,'bad.md',('edit='+secret).encode())
            with self.assertRaises(ValueError) as error: package.source_payloads(root)
            self.assertNotIn(secret,str(error.exception))

    def test_root_manifest_matches_zip_and_every_payload_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root,'server.py',b'public source')
            output=root/'submission/deployment/final.zip'
            with patch.object(package,'ROOT',root),patch.object(package,'OUTPUT',output): package.main()
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.read('release-manifest.json'),(root/'release-manifest.json').read_bytes())
                manifest=json.loads(archive.read('release-manifest.json'))
                self.assertEqual(set(archive.namelist()),set(manifest)|{'release-manifest.json'})
                for name,digest in manifest.items(): self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(),digest)
