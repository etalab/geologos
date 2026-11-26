"""Download logos and check their integrity."""

import hashlib
import os
import time

import requests

from .config import OUTPUT_DIR
from .http import request


def sha1sum(path):
    digest = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


def is_valid(path, row):
    """Check a file against the size and SHA-1 published by Commons."""
    return os.path.getsize(path) == row['size'] and sha1sum(path) == row['sha1']


def download_all(session, plan, output_dir=OUTPUT_DIR, delay=0.4):
    """Download planned files. Return the rows that are present and valid."""
    downloaded = skipped = failed = 0
    kept = []
    total = len(plan)

    for index, row in enumerate(plan, start=1):
        dest = os.path.join(output_dir, row['path'])
        prefix = f'[{index}/{total}]'
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        if os.path.exists(dest):
            if is_valid(dest, row):
                skipped += 1
                kept.append(row)
                continue
            print(f'{prefix} Contenu différent de Commons, nouveau '
                  f"téléchargement : {row['path']}")

        tmp_dest = dest + '.part'
        try:
            with request(session, row['url'], stream=True) as resp:
                with open(tmp_dest, 'wb') as out:
                    for chunk in resp.iter_content(chunk_size=65536):
                        out.write(chunk)
            if not is_valid(tmp_dest, row):
                raise ValueError('taille ou SHA-1 différents de Commons')
            os.replace(tmp_dest, dest)
            downloaded += 1
            kept.append(row)
            print(f"{prefix} Téléchargé : {row['path']} (source : {row['title']})")
        except (requests.RequestException, ValueError, OSError) as exc:
            failed += 1
            if os.path.exists(tmp_dest):
                os.remove(tmp_dest)
            print(f"{prefix} Échec ({row['path']}) : {exc}")

        time.sleep(delay)

    print(f'Téléchargement terminé : {downloaded} nouveaux, '
          f'{skipped} déjà présents, {failed} en échec.')
    return kept
