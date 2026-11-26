"""Write the manifest and the archive."""

import os
import tarfile

import pandas as pd

from .config import ARCHIVE_FILE, MANIFEST_FILE, OUTPUT_DIR


def write_manifest(kept, output_dir=OUTPUT_DIR):
    """Write manifest.csv describing every downloaded file."""
    path = os.path.join(output_dir, MANIFEST_FILE)
    columns = ['path', 'insee', 'method', 'title', 'sources',
               'mime', 'size', 'sha1', 'url']
    df = pd.DataFrame(kept, columns=columns).sort_values('path')
    df.to_csv(path, index=False, encoding='utf-8')

    print(f'Manifeste écrit : {path}')
    print('Association INSEE : ' + ', '.join(
        f'{count} {method}'
        for method, count in df['method'].value_counts().items()))


def compress_logos(source_dir=OUTPUT_DIR, archive_name=ARCHIVE_FILE):
    """Compress downloaded files into a .tar.xz archive."""
    if not os.path.isdir(source_dir):
        print(f'Dossier {source_dir} introuvable, archive ignorée.')
        return

    print(f'Compression vers {archive_name}...')
    with tarfile.open(archive_name, 'w:xz') as txz:
        for dirpath, _, filenames in os.walk(source_dir):
            for name in sorted(filenames):
                if name.endswith('.part'):
                    continue
                full_path = os.path.join(dirpath, name)
                txz.add(full_path, arcname=os.path.relpath(full_path, source_dir))
    print('Compression terminée.')
