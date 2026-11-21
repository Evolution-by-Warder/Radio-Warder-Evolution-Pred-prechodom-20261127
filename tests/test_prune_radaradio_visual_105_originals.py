#!/usr/bin/env python3
"""Reject any stale, duplicated, unapproved or non-source visual UUID decision."""
import unittest
from uuid import UUID
from prune_radaradio_visual_105_originals import verify_decisions,PREVIOUS_SHA,SOURCE_SHA

class VisualDecisionsTests(unittest.TestCase):
    def setUp(self):
        ids=[str(UUID(int=i+1)) for i in range(105)]
        self.source={"schema":2,"review_only":True,
            "previous_world_sha256":PREVIOUS_SHA,"new_candidate_png":105,
            "candidate_images":[{"uuid":u} for u in ids]}
        self.decisions={"schema":1,"review_only":True,
            "source_candidate_world_sha256":SOURCE_SHA,"source_reviewed_images":105,
            "visual_approved_count":69,"production_published":False,
            "visual_rejected":[{"stationuuid":u,"reason":"visibly_wrong_station_logo"}
                               for u in ids[:36]]}
    def test_full_unique_review_pass(self):
        matched,rejected=verify_decisions(self.source,self.decisions)
        self.assertEqual((len(matched),len(rejected)),(105,36))
    def test_reject_missing_or_duplicate_decisions(self):
        for mutation in ("missing","duplicate","unknown","bad_reason","wrong_sha","wrong_count"):
            with self.subTest(mutation=mutation):
                doc={**self.decisions,
                    "visual_rejected":[dict(x) for x in self.decisions["visual_rejected"]]}
                if mutation=="missing":doc["visual_rejected"].pop()
                if mutation=="duplicate":doc["visual_rejected"][-1]=dict(doc["visual_rejected"][0])
                if mutation=="unknown":doc["visual_rejected"][-1]["stationuuid"]=str(UUID(int=500))
                if mutation=="bad_reason":doc["visual_rejected"][0]["reason"]="image incorrectly"
                if mutation=="wrong_sha":doc["source_candidate_world_sha256"]="0"*64
                if mutation=="wrong_count":doc["visual_approved_count"]=70
                with self.assertRaises(ValueError):verify_decisions(self.source,doc)
    def test_unchanged_original_source_required(self):
        doc={**self.source,"previous_world_sha256":"0"*64}
        with self.assertRaises(ValueError):verify_decisions(doc,self.decisions)
if __name__=="__main__":unittest.main()
