#!/usr/bin/env python3
"""Strict upload-integrity regression; never downloads logos or changes a feed."""
import copy
import hashlib
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import verify_published_radio_country_assets as audit


def digest(value):
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def fixture():
    names = ("SK", "CZ")
    countries = {
        name: {
            "stations": i + 1, "logo_package_complete": True,
            "logos": {"file": name + ".zip", "bytes": i + 20,
                      "sha256": digest(name)}
        } for i, name in enumerate(names)
    }
    index = {"schema": 1, "source": "WarderRadio.RadioBrowser",
             "release_tag": "radio-country-20261122", "complete": True,
             "test_only": True, "review_only": True,
             "country_count": 2, "station_count": 3,
             "world": {"file": "radio-countries-bouquets.zip", "bytes": 100,
                       "sha256": digest("world")},
             "countries": countries}
    assets = [{"name": "radio-countries-bouquets.zip", "size": 100,
               "digest": "sha256:" + digest("world")}]
    assets += [{"name": code + ".zip", "size": countries[code]["logos"]["bytes"],
                "digest": "sha256:" + countries[code]["logos"]["sha256"]}
               for code in names]
    release = {"tag_name": index["release_tag"], "draft": False,
               "prerelease": True, "assets": assets}
    return index, release


class Tests(unittest.TestCase):
    def test_matching_release_passes_but_is_explicitly_test_only(self):
        index, release = fixture()
        result = audit.verify(index, release, expected_countries=2)
        self.assertEqual(result["asset_count"], 3)
        self.assertEqual(result["station_count"], 3)
        self.assertEqual(result["asset_bytes"], 141)
        self.assertEqual(result["legal_redistribution_clearance"], "NOT_VERIFIED")
        self.assertTrue(result["test_only"])

    def test_one_missing_uploaded_logo_fails_before_promotion(self):
        index, release = fixture()
        release["assets"].pop()
        with self.assertRaisesRegex(ValueError, "missing or adding"):
            audit.verify(index, release, expected_countries=2)

    def test_wrong_country_sha_even_at_correct_size_fails(self):
        index, release = fixture()
        release["assets"][2]["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "Size/SHA256 mismatch: CZ"):
            audit.verify(index, release, expected_countries=2)

    def test_modified_world_sha_rejected(self):
        index, release = fixture()
        index["world"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "world"):
            audit.verify(index, release, expected_countries=2)

    def test_extra_asset_rejected(self):
        index, release = fixture()
        release["assets"].append(copy.deepcopy(release["assets"][1]))
        with self.assertRaisesRegex(ValueError, "missing or adding"):
            audit.verify(index, release, expected_countries=2)

    def test_wrong_tag_and_nonprerelease_rejected(self):
        for change in ("tag", "not-test", "draft"):
            index, release = fixture()
            if change == "tag":
                release["tag_name"] = "radio-country-20261201"
            elif change == "not-test":
                release["prerelease"] = False
            else:
                release["draft"] = True
            with self.assertRaisesRegex(ValueError, "immutable TEST prerelease"):
                audit.verify(index, release, expected_countries=2)

    def test_incomplete_or_unapproved_index_rejected(self):
        for field in ("complete", "review_only", "test_only"):
            index, release = fixture()
            index[field] = False
            with self.assertRaisesRegex(ValueError, "complete TEST-only"):
                audit.verify(index, release, expected_countries=2)

    def test_partial_country_or_changed_station_inventory_rejected(self):
        index, release = fixture()
        index["countries"]["CZ"]["logo_package_complete"] = False
        with self.assertRaisesRegex(ValueError, "Incomplete country CZ"):
            audit.verify(index, release, expected_countries=2)
        index, release = fixture()
        index["station_count"] += 1
        with self.assertRaisesRegex(ValueError, "station inventory"):
            audit.verify(index, release, expected_countries=2)

    def test_index_cannot_point_to_foreign_or_unsafe_asset(self):
        index, release = fixture()
        index["countries"]["CZ"]["logos"]["file"] = "../CZ.zip"
        with self.assertRaisesRegex(ValueError, "Unexpected logo package path"):
            audit.verify(index, release, expected_countries=2)

    def test_duplicate_file_identity_rejected(self):
        index, release = fixture()
        release["assets"][2]["name"] = "SK.zip"
        with self.assertRaisesRegex(ValueError, "Duplicate public asset"):
            audit.verify(index, release, expected_countries=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
