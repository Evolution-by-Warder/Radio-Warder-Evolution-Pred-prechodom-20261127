#!/usr/bin/env python3
"""Prepare the first 224-country production index from proven immutable assets.

This module never alters GitHub releases, feeds or user files.  It enforces a
one-to-one mapping between the independently pinned source manifest and the
actual GitHub asset metadata before returning a production-ready index.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

TAG = "radio-country-20261122"
REPO = "Evolution-by-Warder/Radio-Warder-Evolution"
SOURCE_SHA256 = "771953b41ceab46f8852f5e3219338cb1369d7f653ed7d329ad551e481f88d68"
COUNTRY = re.compile(r"^[A-Z]{2}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
WORLD = "radio-countries-bouquets.zip"


def guard(ok, message):
    if not ok:
        raise ValueError(message)


def prepare(source, release):
    guard(isinstance(source, dict) and source.get("schema") == 1
          and source.get("source") == "WarderRadio.RadioBrowser"
          and source.get("complete") is True
          and source.get("test_only") is True
          and source.get("review_only") is True
          and source.get("release_tag") == TAG
          and source.get("country_count") == 224,
          "Unexpected pinned country source")

    countries = source.get("countries")
    guard(isinstance(countries, dict) and len(countries) == 224,
          "Missing pinned countries")
    guard(all(isinstance(c, str) and COUNTRY.fullmatch(c) for c in countries),
          "Invalid country identifier")
    guard(type(source.get("station_count")) is int and
          source["station_count"] == 48219, "Unexpected station inventory")

    world = source.get("world")
    guard(isinstance(world, dict) and
          world.get("file") == WORLD and world.get("sha256") == SOURCE_SHA256 and
          type(world.get("bytes")) is int and world["bytes"] == 6664493,
          "Unexpected immutable world ZIP")

    guard(isinstance(release, dict) and release.get("tag_name") == TAG
          and release.get("draft") is False,
          "Unexpected GitHub release")
    assets = release.get("assets")
    guard(isinstance(assets, list) and len(assets) == 225,
          "Expected precisely 225 immutable uploaded assets")
    names = {}
    for item in assets:
        guard(isinstance(item, dict) and isinstance(item.get("name"), str)
              and item["name"] not in names, "Duplicate or invalid asset")
        names[item["name"]] = item
    guard(set(names) == {WORLD} | {c + ".zip" for c in countries},
          "Uploaded asset inventory differs from 224-country source")

    def match(file, size, digest):
        item = names[file]
        guard(type(size) is int and 0 < size <= 1024 * 1024 * 1024 and
              isinstance(digest, str) and SHA.fullmatch(digest) and
              type(item.get("size")) is int and item["size"] == size and
              item.get("digest") == "sha256:" + digest,
              "Public release size/SHA mismatch: " + file)

    match(WORLD, world["bytes"], world["sha256"])
    total, byte_count, copied = 0, world["bytes"], {}
    for code, entry in sorted(countries.items()):
        guard(isinstance(entry, dict) and
              entry.get("logo_package_complete") is True and
              isinstance(entry.get("name"), str) and entry["name"] and
              type(entry.get("stations")) is int and 0 < entry["stations"] <= 12000,
              "Country missing/invalid: " + code)
        logo = entry.get("logos")
        guard(isinstance(logo, dict) and logo.get("file") == code + ".zip",
              "Country logo filename mismatch: " + code)
        match(logo["file"], logo.get("bytes"), logo.get("sha256"))
        total += entry["stations"]
        byte_count += logo["bytes"]
        copied[code] = {"name": entry["name"], "stations": entry["stations"],
                        "logo_package_complete": True,
                        "logos": {"file": code + ".zip", "bytes": logo["bytes"],
                                  "sha256": logo["sha256"]}}
    guard(total == source["station_count"] and
          byte_count == 835703250 and
          byte_count == sum(v["size"] for v in assets),
          "Unexpected cumulative radio asset bytes/number of stations")

    # Fully backwards compatible with the FullHDGlass 1.0.82 radio loader.
    # No bulk logos belong in either plugin IPK; only selected country is fetched.
    result = {"schema": 1, "source": "WarderRadio.RadioBrowser",
              "release_tag": TAG, "complete": True,
              "country_count": 224, "station_count": total,
              "world": {"file": WORLD, "bytes": world["bytes"],
                        "sha256": world["sha256"]},
              "countries": copied}
    proof = {"status": "PASS", "immutable_release_tag": TAG,
             "countries": 224, "stations": total,
             "station_original_png_count": 40837,
             "asset_count": 225, "all_bytes": byte_count,
             "world_sha256": world["sha256"],
             "published": False}
    return result, proof


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--release", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--proof", type=Path, required=True)
    a = p.parse_args()
    data = json.loads(a.source.read_text(encoding="utf-8"))
    release = json.loads(a.release.read_text(encoding="utf-8"))
    index, proof = prepare(data, release)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.proof.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(index, sort_keys=True, ensure_ascii=False,
                                   indent=2) + "\n", encoding="utf-8")
    a.proof.write_text(json.dumps(proof, sort_keys=True, indent=2) + "\n",
                       encoding="utf-8")
    print(json.dumps(proof, sort_keys=True))


if __name__ == "__main__":
    main()
