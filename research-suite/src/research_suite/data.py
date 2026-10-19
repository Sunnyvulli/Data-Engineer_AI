"""Download explicitly selected primary-source data; record content hashes."""
from pathlib import Path
from urllib.request import urlopen
from .common import sha256, write_json

SOURCES = {
    'phishing': {'phishing.zip': 'https://archive.ics.uci.edu/static/public/327/phishing+websites.zip'},
    'checkpoints': {'alce_annotations.json': 'https://raw.githubusercontent.com/princeton-nlp/ALCE/246c476a4edfc564266b7346b6e29ef4861ae937/human_eval/human_eval_citations_completed.json'},
    'transients': {name: f'https://zenodo.org/api/records/2539456/files/{name}/content' for name in
                   ['plasticc_train_metadata.csv.gz', 'plasticc_train_lightcurves.csv.gz']},
}


SOURCES['followup'] = {
    'phiusiil.zip': 'https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip',
    'plasticc_test_metadata.csv.gz': 'https://zenodo.org/api/records/2539456/files/plasticc_test_metadata.csv.gz/content',
    'plasticc_test_lightcurves_01.csv.gz': 'https://zenodo.org/api/records/2539456/files/plasticc_test_lightcurves_01.csv.gz/content',
}

EXPECTED = {
    'phiusiil.zip': '0a639fd03aea6308c5b1c10c92aa23c2ce1505447a9137271865cd0badc9a59a',
    'plasticc_test_metadata.csv.gz': '8048d59cf84ab30fa539ad69aeeebdac6c7347a149b8724e4a32adc9bbf6897e',
    'plasticc_test_lightcurves_01.csv.gz': '388c76d92b3a9572f9beff646ec240e852c4be164c2a63d735247d0b810899f3',
    'phishing.zip': '514f582cb44cba17251baf1d59f64cddff16efa2b644d091ce8d2a1e8d492940',
    'alce_annotations.json': 'cfed9293752413d7c7631f36524dd4ee9ef58b209cdf9c63f6fc1e280b43cca6',
    'plasticc_train_metadata.csv.gz': '58b008e50426e12aae6a0b9df4d0901bf63e7f9a0da579011988c628a63f23d4',
    'plasticc_train_lightcurves.csv.gz': '1c49a9df7e11a96f774b3d111741ea081321a72a169e311600a7e5ecba0424d3',
}


def fetch(project, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    records = []
    for name, url in SOURCES[project].items():
        target = directory / name
        if not target.exists():
            temporary = target.with_suffix(target.suffix + '.part')
            try:
                with urlopen(url, timeout=90) as response, temporary.open('wb') as output:
                    while chunk := response.read(1024 * 1024):
                        output.write(chunk)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        if sha256(target) != EXPECTED[name]:
            raise ValueError(f'Checksum mismatch for {name}; source changed or download is corrupt')
        records.append({'filename': name, 'url': url, 'bytes': target.stat().st_size, 'sha256': sha256(target)})
    write_json(directory / f'{project}-manifest.json', records)
    return records
