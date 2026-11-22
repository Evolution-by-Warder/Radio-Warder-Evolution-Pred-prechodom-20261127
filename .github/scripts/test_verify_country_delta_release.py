#!/usr/bin/env python3
"""Offline SHA, country delta and release plan test for fortnightly publisher."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

spec = importlib.util.spec_from_file_location(
    'delta_release', Path(__file__).with_name('verify_country_delta_release.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def h(v):
    return hashlib.sha256(v).hexdigest()


def case(folder):
    prev_tag, tag = 'radio-country-20261122', 'radio-country-20261201'
    old, current = {}, {}
    files = {}
    indexes = {}
    staged = folder / 'release-assets'
    staged.mkdir()
    new_sk = b'SK new original logo test bytes'
    (staged / 'SK.zip').write_bytes(new_sk)
    for code in ('SK', 'CZ'):
        bouquet = h((code + ' bouquet').encode())
        catalog = h((code + ' catalog').encode())
        previous_logo = h((code + ' original').encode())
        new_logo = h(new_sk) if code == 'SK' else previous_logo
        byte_count = len(new_sk) if code == 'SK' else 14
        old[code] = {
            'stations': 1, 'bouquet_sha256': bouquet,
            'catalog_sha256': catalog, 'logo_package_complete': True,
            'logo_attempted': 1, 'logos_found': 1, 'logos_missing': 0,
            'logos': {'file': code + '.zip', 'bytes': 14,
                      'sha256': previous_logo}}
        current[code] = copy.deepcopy(old[code])
        current[code]['logos'] = {'file': code + '.zip',
                                  'bytes': byte_count,
                                  'sha256': new_logo,
                                  'asset_tag': tag if code == 'SK' else prev_tag}
        indexes[code] = {
            'stations': 1, 'bouquet_sha256': bouquet,
            'catalog_sha256': catalog, 'logo_sha256': new_logo,
            'logos_found': 1}
        files[code] = {'country': code, 'stations': 1,
             'catalogue_complete': True, 'logo_package_complete': True,
             'logo_attempted': 1, 'logos_found': 1, 'logos_missing': 0,
             'files': {'logos/' + code + '.zip': {'sha256': new_logo,
                                                  'bytes': byte_count}}}
    zipfile = folder / 'radio-countries-bouquets.zip'
    with ZipFile(zipfile, 'w') as z:
        z.writestr('index.json', json.dumps({'country_count': 2,
                   'station_count': 2, 'countries': indexes}))
        for code in files:
            z.writestr('manifests/' + code + '.json', json.dumps(files[code]))
    oldfeed = {'schema': 1, 'source': 'WarderRadio.RadioBrowser',
        'complete': True, 'release_tag': prev_tag, 'country_count': 2,
        'station_count': 2,
        'world': {'file': zipfile.name, 'bytes': 300,
                  'sha256': '0' * 64},
        'countries': old}
    feed = copy.deepcopy(oldfeed)
    feed['release_tag'] = tag
    feed['countries'] = current
    feed['world'] = {'file': zipfile.name, 'bytes': zipfile.stat().st_size,
                     'sha256': core.digest(zipfile)}
    plan = core.expected_asset_plan(feed, oldfeed, min_countries=2)
    changes = core.expected_changes(oldfeed, feed)
    return oldfeed, feed, plan, changes, zipfile, staged


class Tests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.items = case(Path(t.name))

    def test_exact_country_change_and_immutable_old_reuse_pass(self):
        result = core.verify(*self.items, min_countries=2)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['changed_country_zip_count'], 1)
        self.assertFalse(result['no_change'])
        self.assertEqual(result['stations'], 2)

    def test_bad_staged_sha_blocks_release(self):
        x = self.items
        (x[5] / 'SK.zip').write_bytes(b'altered')
        with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
            core.verify(*x, min_countries=2)

    def test_bad_world_sha_blocks_release(self):
        x = list(self.items)
        x[1] = copy.deepcopy(x[1])
        x[1]['world']['sha256'] = '1' * 64
        x[2] = core.expected_asset_plan(x[1], x[0], min_countries=2)
        x[3] = core.expected_changes(x[0], x[1])
        with self.assertRaisesRegex(ValueError, 'world bouquet ZIP'):
            core.verify(*x, min_countries=2)

    def test_forged_change_plan_rejected(self):
        x = list(self.items)
        x[2] = copy.deepcopy(x[2])
        x[2]['country_logo_zip_uploads'] = ['CZ']
        with self.assertRaisesRegex(ValueError, 'plan differs'):
            core.verify(*x, min_countries=2)

    def test_coverage_drop_rejected(self):
        x = list(self.items)
        x[1] = copy.deepcopy(x[1])
        x[1]['countries']['SK']['logos_found'] = 0
        x[1]['countries']['SK']['logos_missing'] = 1
        x[2] = core.expected_asset_plan(x[1], x[0], min_countries=2)
        x[3] = core.expected_changes(x[0], x[1])
        with self.assertRaisesRegex(ValueError, 'regression'):
            core.verify(*x, min_countries=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
