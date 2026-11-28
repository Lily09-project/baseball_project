"""Offline syntax and current-document link checks. Historical records stay historical."""
import argparse
import ast
import json
from pathlib import Path
import re
import subprocess
import unicodedata
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CURRENT_DOCS = ['README.md', '協作指南.md', '資料來源.md', 'docs/技術細節.md', 'docs/qa/README.md',
    'docs/training-v5.md', 'docs/ci-validation.md',
    'docs/qa/release-foundation-20261106/README.md',
    'docs/qa/replay-20261112/README.md', 'docs/qa/model-horizons-20261113/README.md',
    'docs/qa/data-2026-20261114/README.md', 'docs/qa/website-roadmap-20261115/README.md',
    'docs/project-closeout-20261116.md', 'docs/qa/replay-evidence-20261116/README.md',
    'docs/qa/visual-refresh-20261121/README.md']


def prose(text):
    return re.sub(r'```.*?```', '', text, flags=re.S)


def anchors(path):
    used, result = {}, set()
    for text in re.findall(r'^#{1,6}\s+(.+)$', prose(Path(path).read_text(encoding='utf-8-sig')), re.M):
        text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
        text = re.sub('<[^>]+>', '', text).replace('`', '').lower()
        slug = ''.join(c for c in text if c.isspace() or c in '-_' or unicodedata.category(c)[0] in ('L', 'N', 'M')).replace(' ', '-')
        number = used.get(slug, 0); used[slug] = number + 1
        result.add(slug if not number else slug + '-' + str(number))
    return result


def check_links(root, names):
    root = Path(root).resolve(); errors = []; count = 0
    for name in names:
        path = root / name
        if not path.is_file():
            errors.append({'file': name, 'issue': 'missing current document'}); continue
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', prose(path.read_text(encoding='utf-8-sig'))):
            parts = urlsplit(target.split(' "')[0].strip('<>'))
            if parts.scheme or parts.netloc: continue
            count += 1
            dest = (path.parent / unquote(parts.path)).resolve() if parts.path else path.resolve()
            if not dest.is_relative_to(root) or not dest.exists():
                errors.append({'file': name, 'target': target, 'issue': 'missing or out-of-repository target'})
            elif parts.fragment and dest.suffix == '.md' and unquote(parts.fragment) not in anchors(dest):
                errors.append({'file': name, 'target': target, 'issue': 'missing heading'})
    return {'local_links': count, 'documents': len(names), 'errors': errors}


PUBLISHED_FORBIDDEN_SUFFIXES = {'.pkl', '.csv', '.pem', '.key', '.env', '.pptx', '.ppt', '.zip', '.xlsx'}
PUBLISHED_MAX_BYTES = 5_000_000
FORBIDDEN_TEXT = ('Da-Xiong-Chen', 'C:' + chr(92) + 'Users' + chr(92), 'C:/Users/', '/Users/')
TEXT_SUFFIXES = {'.md', '.py', '.js', '.cjs', '.html', '.css', '.yml', '.yaml', '.txt', '.bat', '.json'}
NOT_SCANNED = {'scripts/check_repository.py', 'tests/test_repository_checks.py'}
LOCAL_ONLY_DIRECTORIES = ('多餘資料/', 'data/rebas/', 'data/rebas-fielding/', 'data/ldkrsi/', 'output/')
LOCAL_DIRECTORY_EXCEPTIONS = {'多餘資料/README.md', 'data/ldkrsi/LICENSE', 'output/qa/baseline/engine.js'}


def check_tracked_files(root):
    """已追蹤的檔案：Pages 會公開整個 docs/，不能放原始資料、模型、簡報或過大的檔案；
    也不能出現舊專案名稱或本機絕對路徑，受限制的守位資料不得在任何位置被追蹤。"""
    root = Path(root)
    if not (root / '.git').exists(): return {'tracked_files': None, 'errors': []}
    listing = subprocess.run(['git', '-c', 'core.quotepath=off', 'ls-files', '-z'], cwd=root, check=True, capture_output=True).stdout
    names = [n for n in listing.decode('utf-8').split(chr(0)) if n]
    errors = []
    for name in names:
        path = root / name
        if name.startswith(LOCAL_ONLY_DIRECTORIES) and name not in LOCAL_DIRECTORY_EXCEPTIONS:
            errors.append({'file': name, 'issue': 'local data, archive or generated output must not be tracked'})
        if not path.is_file(): continue
        if Path(name).name.casefold() == 'positions_2025.csv':
            errors.append({'file': name, 'issue': 'restricted fielding data must not be tracked'})
        if name.startswith('docs/'):
            if path.suffix.lower() in PUBLISHED_FORBIDDEN_SUFFIXES:
                errors.append({'file': name, 'issue': 'file type must not be published through GitHub Pages'})
            elif path.stat().st_size > PUBLISHED_MAX_BYTES:
                errors.append({'file': name, 'issue': 'published file exceeds the size limit'})
        if name in NOT_SCANNED or name.startswith(('docs/data/', 'output/')) or path.suffix.lower() not in TEXT_SUFFIXES: continue
        text = path.read_text(encoding='utf-8-sig', errors='replace')
        for token in FORBIDDEN_TEXT:
            if token in text: errors.append({'file': name, 'issue': f'contains forbidden text {token!r}'})
    return {'tracked_files': len(names), 'errors': errors}


def check(root=ROOT, node='node'):
    root = Path(root); python_files = list(root.glob('*.py'))
    for directory in ('src', 'scripts', 'tests'): python_files.extend((root / directory).glob('*.py'))
    for path in python_files: ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    javascript = list((root / 'docs').glob('*.js'))
    for path in javascript: subprocess.run([node, '--check', str(path)], check=True, capture_output=True)
    links = check_links(root, CURRENT_DOCS)
    if links['errors']: raise ValueError(json.dumps(links, ensure_ascii=False))
    tracked = check_tracked_files(root)
    if tracked['errors']: raise ValueError(json.dumps(tracked, ensure_ascii=False))
    return {'python_syntax': len(python_files), 'javascript_syntax': len(javascript), **links, 'tracked_files': tracked['tracked_files']}


if __name__ == '__main__':
    import os
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--node', default=os.environ.get('NODE_BINARY', 'node'))
    args = parser.parse_args()
    print(json.dumps(check(node=args.node), ensure_ascii=True, indent=2))
