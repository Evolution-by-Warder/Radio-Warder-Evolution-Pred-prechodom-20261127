#!/usr/bin/env python3
"""Read-only verification of every uploaded country asset against a pinned index.

This is a technical integrity check, NOT a trademark/license clearance or
authorization to promote a TEST-only GitHub release to production.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO = "Evolution-by-Warder/Radio-Warder-Evolution"
COUNTRY = re.compile(r"[A-Z]{2}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
TEST_TAG = re.compile(r"radio-country-20[0-9]{6}\Z")
WORLD = "radio-countries-bouquets.zip"
MAX_RESPONSE = 3 * 1024 * 1024


def sha_field(value):
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def require(test, why):
    if not test:
        raise ValueError(why)


def verify(index, release, expected_countries=224):
    """Compare ALL GitHub Release asset sizes and server digests, no downloads.

    Server-provided SHA256 digests are checked against the independent pinned
    manifest. This guards uploads but is not equivalent to re-reading every
    830 MB archive locally or proving rights to redistribute station marks.
    """
    require(isinstance(index, dict) and isinstance(release, dict),
            "Missing or invalid index/release")
    tag = index.get("release_tag")
    require(isinstance(tag, str) and TEST_TAG.fullmatch(tag),
            "Unexpected TEST release tag")
    require(index.get("schema") == 1 and
            index.get("source") == "WarderRadio.RadioBrowser" and
            index.get("complete") is True and
            index.get("review_only") is True and
            index.get("test_only") is True,
            "Cannot audit as a complete TEST-only country index")
    require(release.get("tag_name") == tag and
            release.get("draft") is False and
            release.get("prerelease") is True,
            "Release must match the original immutable TEST prerelease")
    countries = index.get("countries")
    require(isinstance(countries, dict) and
            len(countries) == expected_countries and
            index.get("country_count") == expected_countries,
            "Incomplete or unexpected country set")
    require(all(isinstance(k, str) and COUNTRY.fullmatch(k) for k in countries),
            "Invalid country code")
    require(type(index.get("station_count")) is int and
            index["station_count"] > 0 and
            sum(x.get("stations", 0) for x in countries.values()
                if isinstance(x, dict)) == index["station_count"],
            "Inconsistent station inventory")
    world = index.get("world")
    require(isinstance(world, dict) and world.get("file") == WORLD and
            type(world.get("bytes")) is int and world["bytes"] > 0 and
            sha_field(world.get("sha256")),
            "Invalid pinned world snapshot")

    raw_assets = release.get("assets")
    require(isinstance(raw_assets, list) and
            len(raw_assets) == expected_countries + 1,
            "Public release is missing or adding unexpected files")
    by_name = {}
    for asset in raw_assets:
        require(isinstance(asset, dict) and isinstance(asset.get("name"), str),
                "Invalid public asset")
        name = asset["name"]
        require(name not in by_name, "Duplicate public asset " + name)
        by_name[name] = asset
    require(set(by_name) == {WORLD} | {code + ".zip" for code in countries},
            "Public country ZIP set differs from pinned index")

    def match(file, nbytes, digest):
        item = by_name[file]
        require(type(nbytes) is int and nbytes > 0 and
                sha_field(digest) and
                type(item.get("size")) is int and item["size"] == nbytes and
                item.get("digest") == "sha256:" + digest,
                "Size/SHA256 mismatch: " + file)

    match(WORLD, world["bytes"], world["sha256"])
    total_station_logos = 0
    uploaded_bytes = world["bytes"]
    for code, data in sorted(countries.items()):
        require(isinstance(data, dict) and
                data.get("logo_package_complete") is True and
                type(data.get("stations")) is int and data["stations"] > 0,
                "Incomplete country " + code)
        logos = data.get("logos")
        require(isinstance(logos, dict) and logos.get("file") == code + ".zip",
                "Unexpected logo package path: " + code)
        match(logos["file"], logos.get("bytes"), logos.get("sha256"))
        uploaded_bytes += logos["bytes"]
    require(uploaded_bytes == sum(a["size"] for a in raw_assets),
            "Released bytes exceed the pinned manifest")
    return {"status": "PASS", "tag": tag,
            "country_count": len(countries),
            "station_count": index["station_count"],
            "asset_count": len(raw_assets),
            "asset_bytes": uploaded_bytes,
            "world_sha256": world["sha256"],
            "test_only": True, "legal_redistribution_clearance": "NOT_VERIFIED",
            "receiver_validation": "NOT_VERIFIED"}


def read_release(tag, token=None):
    require(TEST_TAG.fullmatch(tag) is not None, "Unsafe test tag")
    url = "https://api.github.com/repos/" + REPO + "/releases/tags/" + quote(tag, safe="")
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "WarderRadio-country-integrity/1",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        data = response.read(MAX_RESPONSE + 1)
    require(0 < len(data) <= MAX_RESPONSE, "GitHub release metadata too large")
    return json.loads(data)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--index", type=Path, default=Path("assets/radio-country/test-20261122.json"))
    p.add_argument("--expected-countries", type=int, default=224)
    p.add_argument("--release-json", type=Path,
                   help="Offline fixture; otherwise query the public GitHub release")
    p.add_argument("--out", type=Path, default=Path("build/radio-country-remote-integrity.json"))
    args = p.parse_args()
    index = json.loads(args.index.read_text(encoding="utf-8"))
    release = (json.loads(args.release_json.read_text(encoding="utf-8"))
               if args.release_json else
               read_release(index["release_tag"], os.getenv("GH_TOKEN")))
    result = verify(index, release, expected_countries=args.expected_countries)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
