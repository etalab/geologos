#!/usr/bin/env python3
"""Download French towns' logos straight from a Wikimedia Commons category.

Unlike `geologos.py`, this script does not need a GeoZones MongoDB database.
"""
import argparse
import os
import time

import requests

COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
DEFAULT_CATEGORY = 'Category:Logos of communes of France'
DEFAULT_OUTPUT_DIR = 'logos_commons_cat'
USER_AGENT = 'GeoLogos/1.0 (https://github.com/etalab/geologos)'
RETRY_STATUSES = {429, 500, 502, 503, 504}


def api_get(session, params, retries=3):
    """Query the Commons API, retrying on throttling and server errors."""
    params = dict(params, format='json', maxlag=5)
    for attempt in range(retries + 1):
        resp = session.get(COMMONS_API, params=params, timeout=30)
        retry_after = resp.headers.get('Retry-After')
        if resp.status_code in RETRY_STATUSES or retry_after:
            if attempt == retries:
                resp.raise_for_status()
            wait = float(retry_after) if retry_after else 2 ** attempt
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError('unreachable')


def get_category_files(session, category_title, depth=2, visited=None):
    """Retrieve file titles inside a Commons category (recursively up to depth)."""
    if visited is None:
        visited = set()
    if category_title in visited:
        return []
    visited.add(category_title)

    files = []
    subcats = []
    params = {
        'action': 'query',
        'list': 'categorymembers',
        'cmtitle': category_title,
        'cmtype': 'file|subcat',
        'cmlimit': 'max',
    }
    while True:
        data = api_get(session, params)
        for member in data['query']['categorymembers']:
            if member['ns'] == 6:  # File:
                files.append(member['title'])
            elif member['ns'] == 14 and depth > 0:  # Category:
                subcats.append(member['title'])

        cont = data.get('continue')
        if not cont:
            break
        params.update(cont)
        time.sleep(0.2)

    for subcat in subcats:
        files.extend(get_category_files(session, subcat, depth - 1, visited))
        time.sleep(0.2)

    return files


def get_image_urls(session, file_titles):
    """Resolve Commons File: titles to direct download URLs in batches of 50."""
    results = {}
    for i in range(0, len(file_titles), 50):
        batch = file_titles[i:i + 50]
        data = api_get(session, {
            'action': 'query',
            'titles': '|'.join(batch),
            'prop': 'imageinfo',
            'iiprop': 'url',
        })
        for page in data['query']['pages'].values():
            title = page.get('title')
            imageinfo = page.get('imageinfo')
            if title and imageinfo:
                results[title] = imageinfo[0]['url']
        time.sleep(0.3)

    return results


def local_filename(title):
    """Turn a `File:Foo bar.svg` title into a safe local file name."""
    name = title.split(':', 1)[1] if title.startswith('File:') else title
    return name.replace('/', '_')


def download_all(session, url_map, output_dir, delay=0.4):
    """Download every URL of `url_map`. Return (fetched, skipped, failed)."""
    os.makedirs(output_dir, exist_ok=True)
    fetched = skipped = failed = 0
    for title, url in sorted(url_map.items()):
        clean_name = local_filename(title)
        dest = os.path.join(output_dir, clean_name)
        if os.path.exists(dest):
            skipped += 1
            continue

        tmp = dest + '.part'
        try:
            with session.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(tmp, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            os.replace(tmp, dest)
            fetched += 1
            print(f'Téléchargé : {clean_name}')
        except requests.RequestException as exc:
            failed += 1
            if os.path.exists(tmp):
                os.remove(tmp)
            print(f'Échec sur {clean_name} : {exc}')
        time.sleep(delay)
    return fetched, skipped, failed


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--category', default=DEFAULT_CATEGORY,
                        help='Commons category to crawl (default: %(default)s)')
    parser.add_argument('--depth', type=int, default=2,
                        help='sub-categories recursion depth (default: %(default)s)')
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR,
                        help='where to store logos (default: %(default)s)')
    parser.add_argument('--delay', type=float, default=0.4,
                        help='seconds between downloads (default: %(default)s)')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    with requests.Session() as session:
        session.headers['User-Agent'] = USER_AGENT
        titles = get_category_files(session, args.category, depth=args.depth)
        unique_titles = sorted(set(titles))
        print(f'{len(unique_titles)} fichiers trouvés dans la catégorie '
              f'et ses sous-catégories')
        url_map = get_image_urls(session, unique_titles)
        fetched, skipped, failed = download_all(
            session, url_map, args.output_dir, args.delay)
    print(f'Terminé : {fetched} téléchargés, {skipped} déjà présents, '
          f'{failed} échecs')


if __name__ == '__main__':
    main()
