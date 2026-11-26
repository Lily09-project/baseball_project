"""server.py 的本機請求防護與模型快取。api() 用假的取代，不載入資料也不訓練。"""
import http.client
import json
import sys
import threading
import unittest
from collections import OrderedDict
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import server  # noqa: E402


class RunningServer:
    def __enter__(self):
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
        finally:
            conn.close()


JSON = {'Content-Type': 'application/json'}


class HandlerTests(unittest.TestCase):
    def test_requests_for_other_hosts_or_other_sites_are_refused(self):
        with RunningServer() as s, patch.object(server, 'api', return_value={'ok': 1}):
            self.assertEqual(s.request('GET', '/api/meta')[0], 200)
            self.assertEqual(s.request('GET', '/api/meta', headers={'Host': 'evil.example'})[0], 421)
            self.assertEqual(s.request('GET', '/api/meta', headers={'Sec-Fetch-Site': 'cross-site'})[0], 403)
            self.assertEqual(s.request('GET', '/api/meta', headers={'Sec-Fetch-Site': 'same-origin'})[0], 200)
            host = f'127.0.0.1:{s.port}'
            self.assertEqual(s.request('POST', '/api/evaluate', '{}', {**JSON, 'Origin': f'http://{host}'})[0], 200)
            self.assertEqual(s.request('POST', '/api/evaluate', '{}', {**JSON, 'Origin': 'https://evil.example'})[0], 403)

    def test_post_needs_json_and_survives_absurdly_nested_input(self):
        with RunningServer() as s, patch.object(server, 'api', return_value={'ok': 1}):
            self.assertEqual(s.request('POST', '/api/evaluate', '{}', {'Content-Type': 'text/plain'})[0], 400)
            status, data = s.request('POST', '/api/evaluate', '[' * 100000 + ']' * 100000, JSON)
            self.assertEqual(status, 400)
            self.assertIn('error', data)
            self.assertEqual(s.request('POST', '/api/evaluate', '{}', JSON)[0], 200)  # 伺服器仍正常

    def test_errors_do_not_leak_paths_or_python_internals(self):
        secret = r'C:\Users\someone\private\models\x.pkl'
        with RunningServer() as s:
            with patch.object(server, 'api', side_effect=FileNotFoundError(secret)):
                status, data = s.request('POST', '/api/evaluate', '{}', JSON)
                self.assertEqual(status, 503)
                self.assertNotIn('someone', json.dumps(data, ensure_ascii=False))
            with patch.object(server, 'api', side_effect=KeyError('team')):
                status, data = s.request('GET', '/api/team')
                self.assertEqual(status, 400)
                self.assertNotIn('KeyError', json.dumps(data))
            with patch.object(server, 'api', side_effect=ValueError('局別無效')):
                status, data = s.request('POST', '/api/evaluate', '{}', JSON)
                self.assertEqual((status, data['error']), (400, '局別無效'))


class ModelCacheTests(unittest.TestCase):
    def test_cache_is_bounded_keeps_the_current_model_and_fits_each_date_once(self):
        calls = []
        lock = threading.Lock()

        def fake_fit(date, season=None):
            with lock:
                calls.append(date)
            return object()

        with patch.object(server, '_models', OrderedDict()), patch.object(server, '_fit_gates', {}), \
                patch.object(server, 'fit', fake_fit):
            current = server.model_for(server.FULL)
            for day in range(1, 29):
                server.model_for(f'2026-04-{day:02d}')
            self.assertLessEqual(len(server._models), server.MAX_MODELS)
            self.assertIn(server.FULL, server._models)
            self.assertIs(server.model_for(server.FULL), current)
            calls.clear()
            threads = [threading.Thread(target=server.model_for, args=('2026-09-09',)) for _ in range(6)]
            [t.start() for t in threads]
            [t.join() for t in threads]
            self.assertEqual(calls.count('2026-09-09'), 1)

    def test_detail_refuses_dates_without_a_published_model(self):
        with patch.object(server, 'ensure_available', lambda: None), patch.object(server, 'load', lambda: (None, None, None)):
            with self.assertRaisesRegex(ValueError, '不支援的模型日期'):
                server.api('/api/detail', {'date': ['2031-01-01'], 'batter': ['x'], 'pitcher': ['y']}, None)


if __name__ == '__main__':
    unittest.main()
