#!/usr/bin/env python3
"""Read-only release gate for automatic fortnightly Radio Browser assets.

The schedule may produce a new full-country world and a small set of changed
logo ZIPs, but this gate must pass before publishing any GitHub Release or
altering the receiver's stable latest.json index.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from plan_radio_country_release_assets import plan as expected_asset_plan
from review_country_release_changes import diff as expected_changes

TAG = re.compile(r'^radio-country-20[0-9]{6}$')
CODE = re.compile(r'^[A-Z]{2}$')
SHA = re.compile(r'^[a-f0-9]{64}$')


def fail(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(262144), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(previous, current, planned, changes, source, staged, min_countries=200):
    fail(isinstance(previous, dict) and isinstance(current, dict),
         'Invalid current/previous country release metadata')
    prior_tag, tag = previous.get('release_tag'), current.get('release_tag')
    fail(isinstance(prior_tag, str) and TAG.fullmatch(prior_tag) and
         isinstance(tag, str) and TAG.fullmatch(tag) and prior_tag < tag,
         'Expected a new immutable dated release after published baseline')
    expected_plan = expected_asset_plan(current, previous,
                                        min_countries=min_countries)
    expected_diff = expected_changes(previous, current)
    fail(planned == expected_plan and changes == expected_diff,
         'Release change plan differs from the independent full-world review')
    fail(expected_diff['eligible_for_manual_release_review'],
         'Country/source/logo coverage regression blocks production update')
    fail(not expected_diff['countries_removed_requires_review'] and
         not expected_diff['possible_logo_coverage_regression'],
         'Approved world must not lose existing countries/original logos')
    path = Path(source)
    fail(path.is_file() and not path.is_symlink() and
         path.stat().st_size == current['world']['bytes'] and
         digest(path) == current['world']['sha256'],
         'New world bouquet ZIP SHA/size mismatch')
    codes = current['countries']
    old = previous['countries']
    fail(set(codes) >= set(old) and
         len(codes) == current['country_count'] and
         sum(info['stations'] for info in codes.values()) ==
         current.get('station_count'), 'Incomplete 224-country inventory')

    target = Path(staged)
    fail(target.is_dir() and not target.is_symlink(),
         'No safe staged changed-country ZIP directory')
    expected_names = {c + '.zip' for c in planned['country_logo_zip_uploads']}
    observed = {item.name for item in target.iterdir()}
    fail(observed == expected_names,
         'Changed country ZIP set differs from SHA release plan')

    total_logos = 0
    with ZipFile(path) as archive:
        index = json.loads(archive.read('index.json'))
        fail(index.get('country_count') == len(codes) and
             index.get('station_count') == current['station_count'] and
             set(index.get('countries', {})) == set(codes),
             'New world ZIP index lacks a country')
        for code in sorted(codes):
            entry = codes[code]
            world = index['countries'][code]
            original = json.loads(archive.read('manifests/' + code + '.json'))
            logo = entry['logos']
            fail(original.get('country') == code and
                 original.get('stations') == entry['stations'] == world['stations'] and
                 original.get('catalogue_complete') is True and
                 original.get('logo_package_complete') is True and
                 entry['logo_package_complete'] is True and
                 entry['bouquet_sha256'] == world['bouquet_sha256'] and
                 entry['catalog_sha256'] == world['catalog_sha256'] and
                 logo['sha256'] == world['logo_sha256'] and
                 original['files']['logos/' + code + '.zip']['sha256'] == logo['sha256'] and
                 original['files']['logos/' + code + '.zip']['bytes'] == logo['bytes'] and
                 entry['logo_attempted'] == original['logo_attempted'] ==
                    entry['stations'] and
                 entry['logos_found'] == original['logos_found'] == world['logos_found'] and
                 entry['logos_missing'] == original['logos_missing'] and
                 entry['logos_found'] + entry['logos_missing'] == entry['stations'],
                 'Untrusted station/logo identity for country ' + code)
            total_logos += entry['logos_found']
            asset_tag = logo.get('asset_tag', tag)
            fail(isinstance(asset_tag, str) and TAG.fullmatch(asset_tag)
                 and asset_tag <= tag, 'Unsafe immutable country asset reference')
            if code in planned['country_logo_zip_uploads']:
                source_logo = target / (code + '.zip')
                fail(not source_logo.is_symlink() and source_logo.is_file() and
                     source_logo.stat().st_size == logo['bytes'] and
                     digest(source_logo) == logo['sha256'] and
                     asset_tag == tag, 'Changed original country ZIP SHA mismatch: ' + code)
            else:
                prior = old.get(code, {}).get('logos', {})
                fail(asset_tag == prior.get('asset_tag', prior_tag) and
                     logo['bytes'] == prior.get('bytes') and
                     logo['sha256'] == prior.get('sha256') and
                     logo['file'] == prior.get('file'),
                     'Unverified reuse of old original country ZIP: ' + code)

    if planned['no_change']:
        fail(not expected_names and
             current['world']['sha256'] == previous['world']['sha256'],
             'No-change plan is inconsistent')
    else:
        fail(planned['world_upload_required'],
             'Changed country release must contain new world snapshot')
    return {'status': 'PASS', 'tag': tag,
            'previous_tag': prior_tag, 'countries': len(codes),
            'stations': current['station_count'], 'logos_found': total_logos,
            'changed_country_zip_count': len(expected_names),
            'changed_logo_zip_bytes': planned['new_logo_zip_bytes'],
            'world_sha256': current['world']['sha256'],
            'no_change': planned['no_change'], 'published': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', required=True, type=Path)
    parser.add_argument('--current', required=True, type=Path)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--changes', required=True, type=Path)
    parser.add_argument('--world', required=True, type=Path)
    parser.add_argument('--assets', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    x = parser.parse_args()
    doc = lambda name: json.loads(getattr(x, name).read_text(encoding='utf-8'))
    proof = verify(doc('previous'), doc('current'), doc('plan'),
                   doc('changes'), x.world, x.assets)
    x.out.parent.mkdir(parents=True, exist_ok=True)
    x.out.write_text(json.dumps(proof, indent=2, sort_keys=True) + '\n',
                     encoding='utf-8')
    print(json.dumps(proof, sort_keys=True))


if __name__ == '__main__':
    main()
