"""download_data.py：失敗時不得截斷或悄悄沿用舊資料。全部用假的 fetch，不連網。"""
import contextlib
import io
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import download_data  # noqa: E402


def zip_bytes(names):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name in names:
            archive.writestr(name, '{"game": 1}')
    return buffer.getvalue()


class DownloadTests(unittest.TestCase):
    def run_main(self, tmp, fetch):
        with patch.object(download_data, 'ROOT', str(tmp)), patch.object(download_data, 'fetch', fetch), \
                patch.object(download_data, 'export_fielding_2026', lambda: None),                 contextlib.redirect_stdout(io.StringIO()):
            download_data.main()

    def test_failed_download_keeps_existing_fielding_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp, 'data', 'ldkrsi', 'fieldings_2023.csv')
            existing.parent.mkdir(parents=True)
            existing.write_bytes(b'old-but-valid')

            def fetch(url, timeout=120):
                if url.endswith('/fieldings/2023.csv'):
                    raise OSError('network down')
                if url.endswith('.zip'):
                    return zip_bytes(['CPBL-2024-G001.json'])
                return b'x'

            with self.assertRaises(OSError):
                self.run_main(tmp, fetch)
            self.assertEqual(existing.read_bytes(), b'old-but-valid')
            self.assertFalse(list(Path(tmp).rglob('*.tmp')))

    def test_archive_without_game_files_aborts_instead_of_reusing_old_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp, 'data', 'rebas', '2024', 'CPBL-2024-G001.json')
            old.parent.mkdir(parents=True)
            old.write_bytes(b'old-game')
            with self.assertRaises(SystemExit) as caught:
                self.run_main(tmp, lambda url, timeout=120: zip_bytes(['README.txt', 'CPBL-2024-all.json']))
            self.assertIn('找不到逐場檔', str(caught.exception))
            self.assertEqual(old.read_bytes(), b'old-game')

    def test_success_writes_game_files_and_leaves_identical_license_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            license_file = Path(tmp, 'data', 'ldkrsi', 'LICENSE')
            license_file.parent.mkdir(parents=True)
            license_file.write_bytes(b'LICENSE-TEXT')
            before = license_file.stat().st_mtime_ns

            def fetch(url, timeout=120):
                if url.endswith('.zip'):
                    return zip_bytes(['x/CPBL-2024-G001.json', 'x/CPBL-2024-G002.json', 'x/CPBL-2024-all.json'])
                if url.endswith('LICENSE'):
                    return b'LICENSE-TEXT'
                return b'season,player\n'

            self.run_main(tmp, fetch)
            games = sorted(p.name for p in Path(tmp, 'data', 'rebas', '2024').iterdir())
            self.assertEqual(games, ['CPBL-2024-G001.json', 'CPBL-2024-G002.json'])
            self.assertEqual(license_file.stat().st_mtime_ns, before)
            self.assertEqual(Path(tmp, 'data', 'ldkrsi', 'fieldings_2024.csv').read_bytes(), b'season,player\n')


if __name__ == '__main__':
    unittest.main()
