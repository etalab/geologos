"""List logos and communes from Commons, Wikidata and geo.api.gouv.fr."""

import json
import os
import time
from urllib.parse import unquote

import pandas as pd

from .config import COMMUNES_CACHE_FILE, GEO_API_COMMUNES, WIKIDATA_SPARQL
from .http import commons_api, request
from .matching import normalize_key


WIKIDATA_QUERY = """
SELECT ?insee ?logo WHERE {
  ?item wdt:P374 ?insee ;
        wdt:P154 ?logo .
}
"""


def get_category_files(session, root_category, max_depth=None):
    """Return {File: title: top-level category} for the whole category tree.

    The top-level category tells whether a file comes from the groups of
    communes subtree.
    """
    files = {}
    visited = set()
    queue = [(root_category, 0, None)]

    while queue:
        category, depth, branch = queue.pop(0)
        if category in visited:
            continue
        visited.add(category)

        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': category,
            'cmtype': 'file|subcat',
            'cmlimit': 'max',
        }
        while True:
            data = commons_api(session, params)
            for member in data.get('query', {}).get('categorymembers', []):
                title = member['title']
                if member['ns'] == 6:  # File:
                    files.setdefault(title, branch or category)
                elif member['ns'] == 14:  # Category:
                    if max_depth is None or depth < max_depth:
                        queue.append((title, depth + 1, branch or title))
            if 'continue' not in data:
                break
            params.update(data['continue'])
            time.sleep(0.2)

    print(f'{len(visited)} catégories explorées, {len(files)} fichiers.')
    return files


def get_wikidata_logos(session):
    """Return {File: title: INSEE code} from Wikidata (P154 + P374)."""
    resp = request(session, WIKIDATA_SPARQL, timeout=120,
                   params={'query': WIKIDATA_QUERY},
                   headers={'Accept': 'application/sparql-results+json'})
    logos = {}
    for row in resp.json()['results']['bindings']:
        # http://commons.wikimedia.org/wiki/Special:FilePath/Logo%20X.svg
        name = unquote(row['logo']['value'].rsplit('/', 1)[-1])
        title = 'File:' + name.replace('_', ' ')
        logos.setdefault(title, row['insee']['value'])
    print(f'{len(logos)} logos trouvés sur Wikidata.')
    return logos


def load_communes_index(session, cache_path=COMMUNES_CACHE_FILE):
    """Return {normalized name: INSEE code} for unambiguous commune names."""
    if os.path.exists(cache_path):
        with open(cache_path, encoding='utf-8') as f:
            communes = json.load(f)
    else:
        print('Téléchargement du référentiel des communes (geo.api.gouv.fr)...')
        communes = request(session, GEO_API_COMMUNES).json()
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(communes, f, ensure_ascii=False, indent=2)

    df = pd.DataFrame(communes).dropna(subset=['code', 'nom'])
    df['key'] = df['nom'].map(normalize_key)
    # Homonyms (e.g. dozens of "Saint-Martin") cannot be matched by name.
    unique = df.drop_duplicates('key', keep=False)
    index = dict(zip(unique['key'], unique['code']))
    print(f'{len(df)} communes chargées, {len(index)} noms non ambigus.')
    return index
