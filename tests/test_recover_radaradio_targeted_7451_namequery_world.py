#!/usr/bin/env python3
"""Offline negative tests for all-7451 country/name + operator-site logo recovery."""
import json, unittest
from urllib.parse import parse_qs,urlsplit
from recover_radaradio_targeted_7451_namequery_world import (
    website_identity,exact_match,search_name,source_detail
)
class ContractTests(unittest.TestCase):
    def setUp(self):
        self.target={"country":"SK","name":"Rádio Život","homepage":"https://www.zivot.sk/live/"}
        self.source={"id":"station_123","name":"Rádio Život","country":"SK",
          "logo":"https://cdn.radaradio.com/uploads/radios/zivot.jpg"}
        self.detail={**self.source,"website":"http://zivot.sk/live/"}
    def test_exact_country_name_verified_owner_homepage(self):
        self.assertEqual(exact_match(self.source,self.detail,self.target),self.source["logo"])
        for k,v in (("country","CZ"),("name","Rádio Život Hits"),("id","station_124"),
                    ("logo","https://cdn.radaradio.com/uploads/radios/other.jpg")):
            bad=dict(self.detail);bad[k]=v
            self.assertEqual(exact_match(self.source,bad,self.target),"",k)
        for homepage in ("https://other.sk/live","https://zivot.sk/another",
                         "https://facebook.com/zivot","http://127.0.0.1/live"):
            bad={**self.target,"homepage":homepage}
            self.assertEqual(exact_match(self.source,self.detail,bad),"",homepage)
    def test_web_homepage_variants(self):
        self.assertEqual(website_identity("http://www.zivot.sk/live/index.html"),
                         website_identity("https://zivot.sk/live"))
        self.assertNotEqual(website_identity("https://zivot.sk/rock"),
                            website_identity("https://zivot.sk/live"))
    def test_name_search_uses_q_and_country_instead_of_capped_list(self):
        responses=[]
        def fetch(url,*,limit,expected_type):
            params=parse_qs(urlsplit(url).query)
            self.assertEqual(params["q"],["Rádio Život"])
            self.assertEqual(params["country"],["SK"])
            self.assertEqual(params["limit"],["100"])
            responses.append(url)
            return json.dumps([self.source,dict(self.source,name="Rádio Život Hits"),
                dict(self.source,country="CZ")]).encode()
        hits,digest,examined=search_name("SK","Rádio Život",get=fetch)
        self.assertEqual(len(hits),1)
        self.assertEqual(examined,3)
        self.assertEqual(len(digest),64)
        self.assertEqual(len(responses),1)
    def test_bad_name_and_invalid_detail(self):
        for name in ("", "R"*181):
            with self.assertRaises(ValueError):search_name("SK",name,get=lambda *a,**k:b"[]")
        with self.assertRaises(ValueError):source_detail("../bad",get=lambda url:b"{}")
        with self.assertRaises(ValueError):source_detail("station_123",
            get=lambda url:json.dumps({**self.detail,"id":"elsewhere"}).encode())
        got,digest=source_detail("station_123",get=lambda url:json.dumps(self.detail).encode())
        self.assertEqual(got["id"],"station_123")
        self.assertEqual(len(digest),64)
if __name__=="__main__":unittest.main()
