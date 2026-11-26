"""Constants shared by the modules."""

COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
WIKIDATA_SPARQL = 'https://query.wikidata.org/sparql'
GEO_API_COMMUNES = 'https://geo.api.gouv.fr/communes?fields=nom,code'
ROOT_CATEGORY = 'Category:Logos of communes of France'
GROUPS_CATEGORY = 'Category:Logos of groups of communes of France'
OUTPUT_DIR = 'logos_commons_cat'
GROUPS_SUBDIR = 'intercommunalites'
UNMATCHED_SUBDIR = 'non_associes'
URL_CACHE_FILE = 'commons_urls.json'
COMMUNES_CACHE_FILE = 'communes_france.json'
MANIFEST_FILE = 'manifest.csv'
ARCHIVE_FILE = 'geologos.tar.xz'

# Wikimedia blocks generic or fake User-Agents. Put a real contact (project
# URL or e-mail) here: https://meta.wikimedia.org/wiki/User-Agent_policy
USER_AGENT = 'GeoLogos/1.3 (https://github.com/etalab/geologos)'

RETRY_STATUSES = {429, 500, 502, 503, 504}

# Extension written for each MIME type served by Commons.
MIME_EXTENSIONS = {
    'image/svg+xml': '.svg',
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/tiff': '.tif',
}
