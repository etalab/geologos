#!/usr/bin/env python3
"""Fetch French towns' logos (flags or blazons) referenced by GeoZones."""
import argparse
import os
import tarfile
import time
from urllib.parse import quote

import requests
from pymongo import MongoClient

COMMONS_FILEPATH_URL = 'https://commons.wikimedia.org/wiki/Special:FilePath/'
DEFAULT_LOGOS_DIR = 'logos'
DEFAULT_ARCHIVE = 'geologos.tar.xz'
DEFAULT_MONGO_URI = 'mongodb://localhost:27017/'
USER_AGENT = 'GeoLogos/1.0 (https://github.com/etalab/geologos)'


def retrieve_zones(mongo_uri):
    """Retrieve (geo)zones with a `flag` or a `blazon` value."""
    zones = MongoClient(mongo_uri).geozones.geozones
    return zones.find(
        {'$or': [{'flag': {'$exists': True}}, {'blazon': {'$exists': True}}]},
        {'flag': 1, 'blazon': 1},
    )


def logo_filename(zone):
    """Return the logo file name of a zone, preferring the flag."""
    return zone.get('flag') or zone.get('blazon')


def fetch_logo(session, filename, destination):
    """Download a single logo to `destination`. Return True on success."""
    url = COMMONS_FILEPATH_URL + quote(filename)
    response = session.get(url, stream=True, timeout=30)
    if response.status_code != 200:
        print('Failed {url} ({status})'.format(
            url=url, status=response.status_code))
        return False
    tmp = destination + '.part'
    with open(tmp, 'wb') as file_destination:
        for chunk in response.iter_content(chunk_size=8192):
            file_destination.write(chunk)
    os.replace(tmp, destination)
    return True


def fetch_logos(zones, logos_dir, delay=0.0):
    """
    Fetch logos (flags or blazons) from `zones`.

    Existing files are not fetched again but previous failures are retried.
    Return a (fetched, skipped, failed) tuple.
    """
    os.makedirs(logos_dir, exist_ok=True)
    fetched = skipped = failed = 0
    seen = set()
    with requests.Session() as session:
        session.headers['User-Agent'] = USER_AGENT
        for zone in zones:
            filename = logo_filename(zone)
            if not filename or filename in seen:
                continue
            seen.add(filename)
            filepath = os.path.join(logos_dir, filename.replace('/', '_'))
            if os.path.exists(filepath):
                skipped += 1
                continue
            print('Fetching {0}'.format(filename))
            try:
                ok = fetch_logo(session, filename, filepath)
            except requests.RequestException as exc:
                print('Error on {0}: {1}'.format(filename, exc))
                ok = False
            if ok:
                fetched += 1
            else:
                failed += 1
            if delay:
                time.sleep(delay)
    return fetched, skipped, failed


def compress_logos(logos_dir, archive):
    """Compress the logos folder into a unique archive file."""
    print('Compressing to {0}'.format(archive))
    with tarfile.open(archive, 'w:xz') as txz:
        for name in sorted(os.listdir(logos_dir)):
            path = os.path.join(logos_dir, name)
            if os.path.isfile(path) and not name.endswith('.part'):
                txz.add(path)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mongo-uri', default=DEFAULT_MONGO_URI,
                        help='MongoDB URI of the GeoZones database '
                             '(default: %(default)s)')
    parser.add_argument('--output-dir', default=DEFAULT_LOGOS_DIR,
                        help='where to store logos (default: %(default)s)')
    parser.add_argument('--archive', default=DEFAULT_ARCHIVE,
                        help='archive file name (default: %(default)s)')
    parser.add_argument('--no-compress', action='store_true',
                        help='do not build the archive')
    parser.add_argument('--delay', type=float, default=0.0,
                        help='seconds to wait between downloads')
    return parser.parse_args(argv)


def main(argv=None):
    """Fetch logos from geozones data and optionally compress."""
    args = parse_args(argv)

    print('Retrieving zones from mongo')
    zones = retrieve_zones(args.mongo_uri)

    print('Fetching logos from Wikimedia')
    fetched, skipped, failed = fetch_logos(zones, args.output_dir, args.delay)
    print('Fetching done: {0} fetched, {1} already present, {2} failed'.format(
        fetched, skipped, failed))

    if not args.no_compress:
        compress_logos(args.output_dir, args.archive)
        print('Compressing done')


if __name__ == '__main__':
    main()
