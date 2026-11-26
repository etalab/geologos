"""URL, format, size and hash of Commons files."""

import json
import os
import time

from .config import URL_CACHE_FILE
from .http import commons_api


def get_image_info(session, file_titles, cache_path=URL_CACHE_FILE, refresh=False):
    """Resolve File: titles to url/mime/size/sha1, using a persistent cache."""
    results = {}
    if not refresh and os.path.exists(cache_path):
        with open(cache_path, encoding='utf-8') as f:
            # Older caches stored only the URL: resolve those entries again.
            results = {t: v for t, v in json.load(f).items()
                       if isinstance(v, dict)}

    missing = sorted(t for t in file_titles if t not in results)
    total_batches = (len(missing) + 49) // 50
    for idx in range(0, len(missing), 50):
        batch = missing[idx:idx + 50]
        print(f'Résolution des URLs : lot {idx // 50 + 1}/{total_batches}')
        query = commons_api(session, {
            'action': 'query',
            'titles': '|'.join(batch),
            'prop': 'imageinfo',
            'iiprop': 'url|mime|size|sha1',
            'redirects': 1,
        }).get('query', {})

        # Titles may be normalized or redirected (renamed files).
        aliases = {}
        for key in ('normalized', 'redirects'):
            for item in query.get(key, []):
                aliases.setdefault(item['to'], []).append(item['from'])

        for page in query.get('pages', []):
            info = (page.get('imageinfo') or [None])[0]
            if page.get('missing') or not info:
                continue
            entry = {key: info[key] for key in ('url', 'mime', 'size', 'sha1')}
            entry['title'] = page['title']
            pending = [page['title']]
            while pending:
                title = pending.pop()
                results[title] = entry
                pending.extend(aliases.get(title, []))

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        time.sleep(0.3)

    return {t: results[t] for t in file_titles if t in results}
