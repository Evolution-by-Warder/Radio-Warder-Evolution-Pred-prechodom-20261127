#!/usr/bin/env python3
"""Offline negative tests for the all-224-country independent original-logo pass."""
import io,json,unittest
from recover_radaradio_7451_world import (
    API,safe_url,records,iso_country,match_logo,get_country_directory,png224
)
class StrictReviewTest(unittest.TestCase):
    def setUp(self):
        self.target={"country":"SK","name":"Radio Krásna 98.1",
                     "stream":"https://stream.example.org/live.mp3?x=1"}
        self.source={"country_code":"sk","name":"Radio Krásna 98.1",
                     "stream_url":"https://stream.example.org/live.mp3?x=2",
                     "logo_url":"https://assets.example.org/real.png"}
    def test_identity_exact_country_name_stream(self):
        self.assertEqual(match_logo(self.source,self.target),self.source["logo_url"])
        for field,value in (("country_code","CZ"),("name","Radio Krásna 98.2"),
                            ("stream_url","https://other.example.org/live.mp3"),
                            ("stream_url","https://stream.example.org/other.mp3"),
                            ("logo_url","http://assets.example.org/real.png"),
                            ("logo_url","https://127.0.0.1/real.png")):
            bad=dict(self.source);bad[field]=value
            self.assertEqual(match_logo(bad,self.target),"",field)
    def test_public_rest_only_and_no_untrusted_redirect_targets(self):
        for url in ("http://radaradio.com/api/radios",
                    "https://radaradio.com@evil.org/api/radios",
                    "https://radaradio.com.evil.org/api/radios",
                    "https://radaradio.com/api/unrelated"):
            self.assertEqual(safe_url(url,directory=True),"",url)
        self.assertTrue(safe_url(API+"?country=SK",directory=True))
    def test_json_envelopes_and_iso(self):
        self.assertEqual(iso_country({"country":{"code":"sk"}}),"SK")
        self.assertEqual(iso_country({"country":"Germany"}),"DE")
        for doc in ([{"name":"a"}],{"data":[{"name":"a"}]},
                    {"data":{"results":[{"name":"a"}],"total":1}},
                    {"stations":[{"name":"a"}]}):
            self.assertEqual(len(records(doc)[0]),1)
        for doc in ({},{ "data":{"unknown":[]} },{"error":"forbidden"}):
            with self.assertRaises(ValueError):records(doc)
    def test_stop_when_server_ignores_pagination(self):
        sample=[{"country":"SK","name":"A"},{"country":"SK","name":"B"}]
        calls=[]
        def fake(url,*,limit,expected_type):
            calls.append(url);return json.dumps({"data":sample,"total":5}).encode()
        info=get_country_directory("SK",fake,per_page=2,max_pages=50)
        self.assertEqual(len(calls),2)
        self.assertFalse(info["catalog_complete"])
        self.assertIn("pagination_repeats_previous_page",info["errors"])
    def test_country_pages_finish_on_explicit_total(self):
        def fake(url,*,limit,expected_type):
            number=int(url.split("page=")[-1])
            return json.dumps({"data":[{"name":str(number)}],"total":2}).encode()
        info=get_country_directory("SK",fake,per_page=1,max_pages=30)
        self.assertEqual(len(info["rows"]),2)
        self.assertTrue(info["catalog_complete"])
    def test_reject_generic_near_uniform_image(self):
        from PIL import Image
        im=Image.new("RGB",(120,120),(20,20,20));b=io.BytesIO();im.save(b,format="PNG")
        with self.assertRaises(ValueError):png224(b.getvalue())
        for x in range(120):
            for y in range(120):im.putpixel((x,y),((x*7)%256,(y*5)%256,(x+y)%256))
        b=io.BytesIO();im.save(b,format="PNG")
        self.assertTrue(png224(b.getvalue()).startswith(bytes.fromhex("89504e470d0a1a0a")))
if __name__=="__main__":unittest.main()
