# GeoLogos

Extract logos (flags or blazons) of French towns from Wikimedia Commons.

Two scripts are available:

- `geologos.py` uses [GeoZones](https://github.com/etalab/geozones)' data:
  you have to run GeoZones commands first to build the MongoDB database
  GeoLogos reads logos' file names from.
- `download_logos.py` (code in `commons_logos/`) does not need any database.
  It collects logos from the Commons category
  [Logos of communes of France](https://commons.wikimedia.org/wiki/Category:Logos_of_communes_of_France)
  and its subcategories, and from Wikidata (`P154` of items with an INSEE code).

## Install

    $ python3 -m venv ~/.virtualenvs/geologos
    $ source ~/.virtualenvs/geologos/bin/activate
    $ pip install -r requirements.pip

## Run

From GeoZones data (takes about 3h30 as of February 2016):

    $ ./geologos.py [--mongo-uri mongodb://localhost:27017/] \
                    [--output-dir logos] [--archive geologos.tar.xz] \
                    [--no-compress] [--delay 0]

You should then have an archive file (about 160Mo) with all logos in it.

From Commons and Wikidata:

    $ ./download_logos.py [--category "Category:Logos of communes of France"] \
                          [--depth N] [--no-wikidata] [--refresh] \
                          [--output-dir logos_commons_cat] [--delay 0.4] \
                          [--archive geologos.tar.xz] [--no-compress]

The output folder contains:

- `FR-{INSEE}.{ext}`: logos matched to a commune (`_2`, `_3`... when there
  are several, the Wikidata one coming first);
- `intercommunalites/`: logos of groups of communes;
- `non_associes/`: logos whose commune could not be identified safely;
- `manifest.csv`: for each file, the INSEE code, how it was matched
  (`wikidata`, `nom`, `intercommunalite` or `aucun`), the Commons title,
  format, size, SHA-1 and URL.

Codes marked `nom` are guessed from file names: homonymous communes are
never matched this way, but check them if you need certainty.

Files keep their original format, the extension follows the real MIME type,
and each download is checked against the size and SHA-1 published by Commons.

Before an intensive use, set a contact of yours in `USER_AGENT`
(`commons_logos/config.py`), as required by the
[Wikimedia User-Agent policy](https://meta.wikimedia.org/wiki/User-Agent_policy).

Both scripts can be interrupted and re-run: already downloaded files
are skipped. Use `--refresh` to pick up files updated on Commons.

## Tests

    $ python3 -m unittest
