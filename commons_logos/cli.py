"""Command line interface."""

import argparse

import requests

from .config import ARCHIVE_FILE, OUTPUT_DIR, ROOT_CATEGORY, USER_AGENT
from .download import download_all
from .export import compress_logos, write_manifest
from .metadata import get_image_info
from .planning import plan_files
from .sources import get_category_files, get_wikidata_logos, load_communes_index


DESCRIPTION = """Fetch logos of French communes from Wikimedia Commons, named FR-{INSEE}.{ext}.

Logos come from two sources:

- the Commons category tree "Logos of communes of France" (all depths);
- Wikidata: the "logo image" (P154) of every item with an INSEE code (P374).

The INSEE code of each logo is taken from Wikidata when available (exact),
otherwise guessed from the file name, but only when the commune name is
unambiguous. Logos of groups of communes and unmatched logos keep their
Commons name, in separate folders.

Files are kept in their original format, with an extension matching their
real MIME type, and checked against the size and SHA-1 published by Commons.
A manifest.csv lists, for every file, its source and how it was matched.
"""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--category', default=ROOT_CATEGORY,
                        help='catégorie Commons racine (défaut : %(default)s)')
    parser.add_argument('--depth', type=int, default=None,
                        help='profondeur maximale des sous-catégories '
                             '(défaut : illimitée)')
    parser.add_argument('--no-wikidata', action='store_true',
                        help='ne pas utiliser Wikidata')
    parser.add_argument('--output-dir', default=OUTPUT_DIR,
                        help='dossier de destination (défaut : %(default)s)')
    parser.add_argument('--refresh', action='store_true',
                        help='ignorer le cache des URLs')
    parser.add_argument('--delay', type=float, default=0.4,
                        help='pause entre deux téléchargements, en secondes '
                             '(défaut : %(default)s)')
    parser.add_argument('--archive', default=ARCHIVE_FILE,
                        help="nom de l'archive (défaut : %(default)s)")
    parser.add_argument('--no-compress', action='store_true',
                        help="ne pas créer l'archive")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    with requests.Session() as session:
        session.headers['User-Agent'] = USER_AGENT
        communes_index = load_communes_index(session)

        print(f'Exploration de {args.category}...')
        category_files = get_category_files(session, args.category, args.depth)

        wikidata_logos = {}
        if not args.no_wikidata:
            try:
                wikidata_logos = get_wikidata_logos(session)
            except (requests.RequestException, KeyError, ValueError) as exc:
                print(f'Wikidata indisponible, source ignorée : {exc}')

        titles = set(category_files) | set(wikidata_logos)
        print(f'{len(titles)} fichiers uniques au total.')
        if not titles:
            return

        infos = get_image_info(session, titles, refresh=args.refresh)
        print(f'{len(infos)} fichiers résolus sur Commons.')

        plan = plan_files(infos, category_files, wikidata_logos, communes_index)
        kept = download_all(session, plan, args.output_dir, args.delay)

    write_manifest(kept, args.output_dir)
    if not args.no_compress:
        compress_logos(args.output_dir, args.archive)
