#!/usr/bin/env python3
"""Enrich the published 224-country index from its immutable world ZIP.

No artwork and no user settings are modified.  The extra verified bouquet,
catalogue and coverage fields make the stable index suitable as a baseline
for future fortnightly delta checks while retaining its receiver schema.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

EXPECTED_CODES = 224
EXPECTED_STATIONS = 48219
EXPECTED_LOGOS = 40837


def guard(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest_file(file):
    result = hashlib.sha256()
    with Path(file).open('rb') as src:
        for block in iter(lambda: src.read(262144), b''):
            result.update(block)
    return result.hexdigest()


def enrich(stable, world, expected_codes=EXPECTED_CODES,
           expected_stations=EXPECTED_STATIONS, expected_logos=EXPECTED_LOGOS):
    guard(isinstance(stable, dict) and stable.get('schema') == 1 and
          stable.get('source') == 'WarderRadio.RadioBrowser' and
          stable.get('complete') is True and
          stable.get('country_count') == expected_codes and
          stable.get('station_count') == expected_stations and
          isinstance(stable.get('countries'), dict) and
          len(stable['countries']) == expected_codes,
          'Untrusted published stable country catalogue')
    info = stable.get('world')
    guard(isinstance(info, dict) and info.get('file') == 'radio-countries-bouquets.zip' and
          type(info.get('bytes')) is int and
          Path(world).stat().st_size == info['bytes'] and
          digest_file(world) == info.get('sha256'),
          'World ZIP differs from published immutable SHA')
    result = copy.deepcopy(stable)
    sum_stations = sum_logos = 0
    with ZipFile(world) as zipped:
        world_index = json.loads(zipped.read('index.json'))
        guard(world_index.get('country_count') == expected_codes and
              world_index.get('station_count') == expected_stations and
              set(world_index.get('countries', {})) == set(stable['countries']),
              'World ZIP country/station index mismatch')
        for code, country in sorted(result['countries'].items()):
            asset = world_index['countries'][code]
            meta = json.loads(zipped.read('manifests/' + code + '.json'))
            files = meta.get('files', {})
            logo = country.get('logos', {})
            guard(meta.get('country') == code and
                  meta.get('name') == country.get('name') and
                  meta.get('stations') == country.get('stations') ==
                     asset.get('stations') and
                  meta.get('catalogue_complete') is True and
                  meta.get('logo_package_complete') is True and
                  country.get('logo_package_complete') is True and
                  files.get('logos/' + code + '.zip', {}).get('sha256') ==
                     logo.get('sha256') == asset.get('logo_sha256') and
                  files.get('logos/' + code + '.zip', {}).get('bytes') ==
                     logo.get('bytes'),
                  'Original country or logo SHA mismatch: ' + code)
            attempted, found, missing = (meta.get('logo_attempted'),
                                         meta.get('logos_found'),
                                         meta.get('logos_missing'))
            guard(type(attempted) is int and type(found) is int and
                  type(missing) is int and attempted == meta['stations'] and
                  attempted == found + missing and
                  found == asset.get('logos_found') and found >= 0 and missing >= 0,
                  'Original logo coverage mismatch: ' + code)
            bouquet = files.get('bouquets/' + code + '.radio', {}).get('sha256')
            catalog = files.get('catalog/' + code + '.json', {}).get('sha256')
            guard(bouquet == asset.get('bouquet_sha256') and
                  catalog == asset.get('catalog_sha256') and
                  isinstance(bouquet, str) and len(bouquet) == 64 and
                  isinstance(catalog, str) and len(catalog) == 64,
                  'Bouquet/catalogue SHA mismatch: ' + code)
            country.update(bouquet_sha256=bouquet,
                           catalog_sha256=catalog, logo_attempted=attempted,
                           logos_found=found, logos_missing=missing)
            sum_stations += meta['stations']
            sum_logos += found
    guard(sum_stations == expected_stations and sum_logos == expected_logos,
          'Incomplete world coverage totals')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--current', type=Path, required=True)
    p.add_argument('--world', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    x = p.parse_args()
    source = json.loads(x.current.read_text(encoding='utf-8'))
    result = enrich(source, x.world)
    x.out.parent.mkdir(parents=True, exist_ok=True)
    x.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                 indent=2) + '\n', encoding='utf-8')
    print('VERIFIED 224-country stable delta baseline: 48219 stations, 40837 original logos')


if __name__ == '__main__':
    main()
