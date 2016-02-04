# GeoLogos

Extract logos from @etalab/geozones’ data for French towns.

You have to run [GeoZones](https://github.com/etalab/geozones)
commands first to build the Mongo DB that GeoLogos access to
for retrieving logos’ paths.

## Install

    $ python3.5 -m venv ~/.virtualenvs/geologos
    $ source ~/.virtualenvs/geologos/bin/activate
    $ pip install -r requirements.pip

## Run (takes about 3h30 as of February 2016)

    $ ./geologos.py

## Enjoy!

You should have generated an archive file (about 160Mo)
with all logos in it.
