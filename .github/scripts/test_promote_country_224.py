#!/usr/bin/env python3
"""Regression guards for immutable release data promotion (offline)."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("country_promotion",
    Path(__file__).resolve().parent / "promote_country_224.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixtures():
    original = json.loads((ROOT / "assets/radio-country/source-20261122.json")
                          .read_text(encoding="utf-8"))
    files = [{"name": original["world"]["file"],
              "size": original["world"]["bytes"],
              "digest": "sha256:" + original["world"]["sha256"]}]
    for code, entry in original["countries"].items():
        f = entry["logos"]
        files.append({"name": code + ".zip", "size": f["bytes"],
                      "digest": "sha256:" + f["sha256"]})
    release = {"tag_name": module.TAG, "draft": False, "prerelease": True,
               "assets": files}
    return original, release


class PromotionTests(unittest.TestCase):
    def test_all_225_original_assets_produce_full_receiver_compatible_feed(self):
        source, release = fixtures()
        out, proof = module.prepare(source, release)
        self.assertEqual(proof["all_bytes"], 835703250)
        self.assertEqual(proof["asset_count"], 225)
        self.assertEqual(out["country_count"], 224)
        self.assertEqual(out["station_count"], 48219)
        self.assertEqual(out["countries"]["SK"]["stations"], 123)
        self.assertTrue(out["complete"])
        self.assertNotIn("test_only", out)
        self.assertNotIn("review_only", out)

    def test_reject_modified_asset_digest(self):
        source, release = fixtures()
        release["assets"][5]["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "size/SHA"):
            module.prepare(source, release)

    def test_reject_modified_asset_size(self):
        source, release = fixtures()
        release["assets"][5]["size"] += 1
        with self.assertRaisesRegex(ValueError, "size/SHA"):
            module.prepare(source, release)

    def test_reject_missing_country_asset(self):
        source, release = fixtures()
        release["assets"].pop()
        with self.assertRaisesRegex(ValueError, "225"):
            module.prepare(source, release)

    def test_reject_duplicate_country_asset(self):
        source, release = fixtures()
        release["assets"][-1] = copy.deepcopy(release["assets"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            module.prepare(source, release)

    def test_reject_unknown_asset(self):
        source, release = fixtures()
        release["assets"][8]["name"] = "bad.zip"
        with self.assertRaisesRegex(ValueError, "Uploaded asset inventory"):
            module.prepare(source, release)

    def test_reject_wrong_country_count(self):
        source, release = fixtures()
        source["country_count"] = 223
        with self.assertRaisesRegex(ValueError, "pinned country"):
            module.prepare(source, release)

    def test_reject_wrong_station_count(self):
        source, release = fixtures()
        source["countries"]["SK"]["stations"] += 1
        with self.assertRaisesRegex(ValueError, "cumulative"):
            module.prepare(source, release)

    def test_reject_incomplete_logo_package(self):
        source, release = fixtures()
        source["countries"]["SK"]["logo_package_complete"] = False
        with self.assertRaisesRegex(ValueError, "Country missing"):
            module.prepare(source, release)

    def test_reject_incomplete_source(self):
        source, release = fixtures()
        source["complete"] = False
        with self.assertRaisesRegex(ValueError, "pinned country"):
            module.prepare(source, release)

    def test_reject_wrong_release(self):
        source, release = fixtures()
        release["tag_name"] = "radio-country-20261201"
        with self.assertRaisesRegex(ValueError, "GitHub release"):
            module.prepare(source, release)


if __name__ == "__main__":
    unittest.main(verbosity=2)
