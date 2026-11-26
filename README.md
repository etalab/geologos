# GeoLogos

Extract logos (flags or blazons) of French towns from Wikimedia Commons.

Two scripts are available:

- `geologos.py` uses [GeoZones](https://github.com/etalab/geozones)' data:
  you have to run GeoZones commands first to build the MongoDB database
  GeoLogos reads logos' file names from.
- `download_logos.py` crawls the Commons category
  [Logos of communes of France](https://commons.wikimedia.org/wiki/Category:Logos_of_communes_of_France)
  directly and does not need any database.

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

From the Commons category:

    $ ./download_logos.py [--category "Category:Logos of communes of France"] \
                          [--depth 2] [--output-dir logos_commons_cat] \
                          [--delay 0.4]

Both scripts can be interrupted and re-run: already downloaded files
are skipped and only missing ones are fetched again.
