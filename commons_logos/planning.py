"""Choose the local path of every logo."""

import os
import re

from .config import (GROUPS_CATEGORY, GROUPS_SUBDIR, MIME_EXTENSIONS,
                     UNMATCHED_SUBDIR)
from .matching import match_insee_code


def safe_name(text):
    return re.sub(r'[\\/:*?"<>|]+', '_', text).strip(' .')


def plan_files(infos, category_files, wikidata_logos, communes_index):
    """Decide the local path of every file. Return a list of plan rows.

    Names are deterministic, so that re-running the script finds the files
    it already downloaded. The logo declared on Wikidata gets FR-{INSEE},
    other logos of the same commune get FR-{INSEE}_2, _3...
    """
    files = {}
    for title, info in infos.items():
        row = files.setdefault(info['title'], {'info': info, 'sources': set()})
        if title in category_files:
            row['sources'].add('commons')
            row['branch'] = category_files[title]
        if title in wikidata_logos:
            row['sources'].add('wikidata')
            row['insee'] = wikidata_logos[title]
            row['method'] = 'wikidata'

    for title, row in files.items():
        if 'insee' in row:
            continue
        if row.get('branch') == GROUPS_CATEGORY:
            row['method'] = 'intercommunalite'
            continue
        insee = match_insee_code(title, communes_index)
        if insee:
            row['insee'], row['method'] = insee, 'nom'
        else:
            row['method'] = 'aucun'

    priority = {'wikidata': 0, 'nom': 1}
    ordered = sorted(files.items(), key=lambda item: (
        priority.get(item[1]['method'], 2), item[0]))

    used = set()
    plan = []
    for title, row in ordered:
        info = row['info']
        ext = MIME_EXTENSIONS.get(info['mime'])
        if not ext:
            print(f'Format non pris en charge ({info["mime"]}) : {title}')
            continue
        if row['method'] == 'intercommunalite':
            folder = GROUPS_SUBDIR
            base = safe_name(os.path.splitext(title.split(':', 1)[1])[0])
        elif row['method'] == 'aucun':
            folder = UNMATCHED_SUBDIR
            base = safe_name(os.path.splitext(title.split(':', 1)[1])[0])
        else:
            folder = ''
            base = f"FR-{row['insee']}"

        name, counter = base + ext, 2
        while os.path.join(folder, name).lower() in used:
            name = f'{base}_{counter}{ext}'
            counter += 1
        relpath = os.path.join(folder, name)
        used.add(relpath.lower())
        plan.append({
            'path': relpath,
            'title': title,
            'insee': row.get('insee', ''),
            'method': row['method'],
            'sources': '+'.join(sorted(row['sources'])),
            **info,
        })
    return plan
