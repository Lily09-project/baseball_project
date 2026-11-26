"""Broken latest-document targets must block the PR gate."""
from pathlib import Path
import contextlib
import io
import json
import subprocess
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_repository import check_links, check_tracked_files
import run_ci


class RepositoryCheckTests(unittest.TestCase):
    def test_encoded_paths_duplicate_anchors_and_external_links(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'說明.md').write_text('# 最新工作稿\n## A.B\n## A.B\n', encoding='utf8')
            (root/'README.md').write_text('[最新](%E8%AA%AA%E6%98%8E.md#最新工作稿)\n[second](說明.md#ab-1)\n[外部](https://example.org)', encoding='utf8')
            result = check_links(root, ['README.md'])
            self.assertEqual(result['errors'], []); self.assertEqual(result['local_links'], 2)

    def test_missing_file_heading_escape_and_document_are_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'target.md').write_text('# Current', encoding='utf8')
            (root/'README.md').write_text('[a](missing.md)\n[b](target.md#old)\n[c](../outside)', encoding='utf8')
            self.assertEqual(len(check_links(root, ['README.md', 'absent.md'])['errors']), 4)

    def test_examples_in_fenced_code_do_not_become_release_links(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'README.md').write_text('```md\n[sample](not-created.md)\n```\n# Current\n[ok](#current)', encoding='utf8')
            result = check_links(root, ['README.md'])
            self.assertFalse(result['errors']); self.assertEqual(result['local_links'], 1)

    def test_failed_check_blocks_ci_and_restores_existing_fixture(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/'tests/fixtures').mkdir(parents=True)
            fixture=root/'tests/fixtures/qa_scenarios.json'; fixture.write_bytes(b'original developer fixture')
            def failure(*args, **kwargs):
                fixture.write_bytes(b'generated test content')
                return SimpleNamespace(returncode=7, stdout=b'failure details must remain visible')
            with patch.object(run_ci,'ROOT',root), patch.object(sys,'argv',['run_ci']), \
                    patch.object(run_ci.subprocess,'run',side_effect=failure) as command, contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(run_ci.main(),7)
            self.assertEqual(command.call_count,1)
            self.assertEqual(fixture.read_bytes(),b'original developer fixture')
            self.assertIn('failure details',output.getvalue())
            report=json.loads(next((root/'output/ci-validation').glob('*/summary.json')).read_text())
            self.assertNotIn('passed',report)
            self.assertEqual(report['steps'][0]['exit_code'],7)


    def tracked(self, root, files):
        subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
        for name, data in files.items():
            path = Path(root, name); path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data if isinstance(data, bytes) else data.encode('utf8'))
        subprocess.run(['git', 'add', '-A'], cwd=root, check=True)
        return check_tracked_files(root)

    def test_tracked_files_reject_published_models_data_and_restricted_fielding_copies(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.tracked(folder, {'docs/ok.md': 'fine', 'docs/data/m.json': '{}', 'docs/leak.csv': 'a,b',
                'docs/model.pkl': b'x', 'docs/big.json': b'0' * 5_000_001,
                'data/cpbl/positions_2025.csv': 'ID', 'models/2026/weights.pkl': b'x'})
            flagged = sorted(e['file'] for e in result['errors'])
            self.assertEqual(flagged, ['data/cpbl/positions_2025.csv', 'docs/big.json', 'docs/leak.csv', 'docs/model.pkl'])

    def test_tracked_files_reject_old_project_names_and_local_paths(self):
        bad_path = 'C:' + chr(92) + 'Users' + chr(92) + 'someone'
        with tempfile.TemporaryDirectory() as folder:
            result = self.tracked(folder, {'README.md': 'see github.com/Da-Xiong-Chen/x', 'docs/a.md': 'file at ' + bad_path,
                'src/ok.py': 'print(1)', 'docs/data/skipped.json': '{"p": "/Users/x"}'})
            self.assertEqual(sorted(e['file'] for e in result['errors']), ['README.md', 'docs/a.md'])

    def test_clean_repository_passes_and_non_git_folders_are_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(self.tracked(folder, {'README.md': 'hello', 'docs/index.html': '<p>hi</p>'})['errors'], [])
        with tempfile.TemporaryDirectory() as folder:
            self.assertIsNone(check_tracked_files(folder)['tracked_files'])


if __name__ == '__main__': unittest.main()
