"""Stage and verify original news images for the static GitHub Pages build."""
import base64
import hashlib
import json
import shutil
from pathlib import Path


def prepare_news(root: Path, out: Path):
    manifest = json.loads((root / 'news-manifest.json').read_text())
    out.mkdir(parents=True, exist_ok=True)
    for name in ('news.js', 'news-manifest.json'):
        shutil.copyfile(root / name, out / name)
    for item in manifest:
        name = item['src']
        assert Path(name).name == name, 'Invalid news image path'
        original = root / name
        encoded = root / 'news-assets' / (name + '.b64')
        raw = original.read_bytes() if original.exists() else base64.b64decode(encoded.read_text(), validate=True)
        assert hashlib.sha256(raw).hexdigest() == item['sha256'], f'News image hash differs: {name}'
        (out / name).write_bytes(raw)
    print(f'Verified and staged {len(manifest)} news clippings across {len({item["question_id"] for item in manifest})} questions.', flush=True)
