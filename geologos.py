#!/usr/bin/env python
import os
import tarfile

import requests
from pymongo import MongoClient

DBPEDIA_MEDIA_URL = 'http://commons.wikimedia.org/wiki/Special:FilePath/'
LOGOS_FOLDER_PATH = 'logos'


def retrieve_zones():
    """Retrieve (geo)zones with a `flag` or a `blazon` value."""
    zones = MongoClient().geozones.geozones
    return zones.find({'$or': [
        {'flag': {'$exists':  True}},
        {'blazon': {'$exists':  True}}
    ]})


def fetch_logos(zones):
    """
    Fetch logos (flags or blazons) from `zones`.

    Not optimized to avoid being blacklisted by wikimedia.
    That command takes about 3h30 as of February 2016.

    Existing files are not fetched but previous 404 are retried.
    """
    if not os.path.exists(LOGOS_FOLDER_PATH):
        os.makedirs(LOGOS_FOLDER_PATH)
    for zone in zones:
        filename = zone.get('flag', zone.get('blazon'))
        if not filename:
            continue
        filepath = os.path.join(LOGOS_FOLDER_PATH, filename)
        if os.path.exists(filepath):
            continue
        url = DBPEDIA_MEDIA_URL + filename
        print('Fetching {url}'.format(url=url))
        r = requests.get(url, stream=True)
        if r.status_code == 404:
            continue
        with open(filepath, 'wb') as file_destination:
            for chunk in r.iter_content(chunk_size=1024):
                file_destination.write(chunk)


def compress_logos():
    """Compress the `logos` folders into a unique archive file."""
    filename = 'geologos.tar.xz'
    print('Compressing to {0}'.format(filename))
    with tarfile.open(filename, 'w:xz') as txz:
        for (dirpath, dirnames, filenames) in os.walk(LOGOS_FOLDER_PATH):
            for name in filenames:
                txz.add(os.path.join(LOGOS_FOLDER_PATH, name))
            break


def main():
    """Fetch logos from geozones data and optionally compress."""
    print('Retrieving zones from mongo')
    zones = retrieve_zones()

    print('Fetching logos from Wikimedia')
    fetch_logos(zones)
    print('Fetching done')

    print('Compressing retrieved logos')
    compress_logos()
    print('Compressing done')


if __name__ == '__main__':
    main()
