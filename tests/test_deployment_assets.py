"""Cross-platform checks for the restricted Docker context's runtime dependencies."""
import ast
import fnmatch
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def included_in_context(path):
    included = True
    for line in (ROOT/'.dockerignore').read_text().splitlines():
        rule = line.strip()
        if not rule or rule.startswith('#'):
            continue
        negated = rule.startswith('!')
        rule = rule.lstrip('!')
        matches = path.startswith(rule) if rule.endswith('/') else fnmatch.fnmatchcase(path,rule)
        if matches:
            included = negated
    return included


class DeploymentAssetsTests(unittest.TestCase):
    def test_local_python_imports_are_copied_and_included_in_docker_context(self):
        copied = {line.split()[1] for line in (ROOT/'Dockerfile').read_text().splitlines()
                  if line.startswith('COPY ')}
        for module in ('server.py','pipeline_quality.py','subtitle_png.py','languages.py'):
            tree = ast.parse((ROOT/module).read_text(encoding='utf-8'))
            imported = {node.module.split('.')[0]+'.py' for node in ast.walk(tree)
                        if isinstance(node,ast.ImportFrom) and node.module}
            for dependency in {module} | {name for name in imported if (ROOT/name).is_file()}:
                with self.subTest(module=module,dependency=dependency):
                    self.assertIn(dependency,copied)
                    self.assertTrue(included_in_context(dependency))

    def test_all_language_runtime_assets_are_included_and_private_data_excluded(self):
        for path in ('dist/languages.json','dist/js/languages.js','dist/css/fonts.css',
                     'dist/fonts/noto-urdu.ttf','dist/fonts/noto-devanagari.ttf',
                     'dist/fonts/noto-cjk.otf','dist/fonts/noto-latin.ttf'):
            self.assertTrue((ROOT/path).is_file(),path)
            self.assertTrue(included_in_context(path),path)
        for path in ('.env','data/jisr.sqlite3','work/api.log','.git/config','tests/test_languages.py'):
            self.assertFalse(included_in_context(path),path)
