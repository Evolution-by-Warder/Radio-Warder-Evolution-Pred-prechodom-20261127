#!/usr/bin/env python3
"""Independent no-network regression for the stable delta baseline."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

spec = importlib.util.spec_from_file_location(
    'stable_enrichment', Path(__file__).with_name('enrich_country_index.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def sample(root):
    path = root / 'radio-countries-bouquets.zip'
    countries = {}
    metadata = {}
    allfiles = {}
    for code in ('CZ', 'SK'):
        f = '1' * 64 if code == 'CZ' else '2' * 64
        s = '3' * 64 if code == 'CZ' else '4' * 64
        k = '5' * 64 if code == 'CZ' else '6' * 64
        name = 'Čechy' if code == 'CZ' else 'Slovensko'
        countries[code] = {'name': name, 'stations': 1,
                           'logo_package_complete': True,
                           'logos': {'file': code + '.zip',
                                     'bytes': 120, 'sha256': k}}
        metadata[code] = {'name': name, 'stations': 1,
                          'bouquet_sha256': f, 'catalog_sha256': s,
                          'logo_sha256': k, 'logos_found': 1}
        allfiles[code] = {'country': code, 'name': name, 'stations': 1,
             'catalogue_complete': True, 'logo_package_complete': True,
             'logo_attempted': 1, 'logos_found': 1, 'logos_missing': 0,
             'files': {'logos/' + code + '.zip': {'sha256': k, 'bytes': 120},
                       'bouquets/' + code + '.radio': {'sha256': f},
                       'catalog/' + code + '.json': {'sha256': s}}}
    with ZipFile(path, 'w') as z:
        z.writestr('index.json', json.dumps({
            'country_count': 2, 'station_count': 2, 'countries': metadata}))
        for code in allfiles:
            z.writestr('manifests/' + code + '.json', json.dumps(allfiles[code]))
    data = {'schema': 1, 'source': 'WarderRadio.RadioBrowser',
            'release_tag': 'radio-country-20261122', 'complete': True,
            'country_count': 2, 'station_count': 2,
            'world': {'file': path.name, 'bytes': path.stat().st_size,
                      'sha256': core.digest_file(path)},
            'countries': countries}
    return path, data


class Tests(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.file, self.source = sample(Path(holder.name))

    def build(self, source=None):
        return core.enrich(source or self.source, self.file,
                           expected_codes=2, expected_stations=2,
                           expected_logos=2)

    def test_exact_shas_added_to_same_stable_index_without_losing_logos(self):
        output = self.build()
        self.assertEqual(output['countries']['SK']['logos'],
                         self.source['countries']['SK']['logos'])
        self.assertEqual(output['countries']['SK']['logo_attempted'], 1)
        self.assertEqual(output['countries']['SK']['logos_found'], 1)
        self.assertEqual(output['countries']['SK']['logos_missing'], 0)
        self.assertEqual(output['countries']['CZ']['bouquet_sha256'], '1' * 64)

    def test_modified_logo_sha_is_rejected(self):
        changed = copy.deepcopy(self.source)
        changed['countries']['CZ']['logos']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
            self.build(changed)

    def test_modified_world_sha_is_rejected(self):
        changed = copy.deepcopy(self.source)
        changed['world']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'World ZIP differs'):
            self.build(changed)

    def test_incomplete_country_is_rejected(self):
        changed = copy.deepcopy(self.source)
        changed['countries']['SK']['logo_package_complete'] = False
        with self.assertRaisesRegex(ValueError, 'country or logo'):
            self.build(changed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
