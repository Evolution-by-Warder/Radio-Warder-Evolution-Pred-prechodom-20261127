#!/usr/bin/env python3
"""One 224-country, 7451-missing RadaRadio EXACT-STREAM original artwork REVIEW.

Never fetches or changes existing PNG. Requires signed 40768-world and signed
original country ZIPs; only strict country + full name + exact stream identity
may yield a new country candidate. No production publishing.
"""
import argparse
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from hashlib import sha256
from io import BytesIO
import ipaddress,json,re,socket,time
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler
from complete_world_country_original_logos import verify_source,get_country,engine
from recover_missing_radio_logos import original_package,encode_logos
from build_country_radio_packages import save
from stage_two_independent_radio_directories_all_7826 import namekey,streamkey

WORLD_SHA="a3237e7d3ee5218eee4b30b6bff15c73e384657d17d8b8fb28fa21a690e4863b"
API="https://radaradio.com/api/radios"
EXPECTED_STATIONS=48219
EXPECTED_ORIGINALS=40768
EXPECTED_MISSING=7451
PER_PAGE=250
MAX_PAGES=75
WORKERS=4
IMG_MAX=1500000
JSON_MAX=3500000
IMAGE_KEYS=("logo_url","logoUrl","logo","image_url","imageUrl","image","favicon","cover_url")
STREAM_KEYS=("stream_url","streamUrl","stream","url_resolved","streamURL","audio_url","audioUrl")

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args):raise ValueError("Untrusted redirect")
OPENER=build_opener(NoRedirect())

def safe_url(url,directory=False):
    if not isinstance(url,str) or len(url)>1800:return ""
    try:
        p=urlsplit(url.strip());h=(p.hostname or "").lower().rstrip(".")
        if (p.scheme!="https" or p.username or p.password or
            p.port not in (None,443) or p.fragment or
            not re.fullmatch(r"[a-z0-9.-]{4,190}",h) or "." not in h or
            h.startswith(("localhost.","127.")) or
            h.endswith((".local",".internal",".test",".invalid"))):return ""
        if directory and (h!="radaradio.com" or p.path!="/api/radios"):return ""
        try:ipaddress.ip_address(h);return ""
        except ValueError:pass
        return url.strip()
    except (ValueError,TypeError,AttributeError):return ""

def public_host(host):
    try:
        return all(ipaddress.ip_address(a[4][0]).is_global
                   for a in socket.getaddrinfo(host,None,proto=socket.IPPROTO_TCP))
    except (OSError,ValueError):return False

def fetch(url,*,limit,expected_type):
    clean=safe_url(url,directory=(expected_type=="application/json"))
    if not clean or not public_host(urlsplit(clean).hostname):
        raise ValueError("Unsafe upstream URL")
    r=Request(clean,headers={"User-Agent":"WarderRadioOneGlobalOriginalArtworkReview/1.0",
                             "Accept":expected_type})
    with OPENER.open(r,timeout=15) as response:
        mime=response.headers.get("Content-Type","").split(";")[0].lower().strip()
        if (response.status!=200 or response.geturl()!=clean or
            (mime and (mime!="application/json" if expected_type=="application/json"
                       else not mime.startswith("image/")))):
            raise ValueError("Unexpected upstream MIME or redirect")
        data=response.read(limit+1)
    if not 1<=len(data)<=limit:raise ValueError("Unbounded source bytes")
    return data

def records(doc):
    if isinstance(doc,list):return doc,{},None
    if not isinstance(doc,dict):raise ValueError("Unrecognized catalog")
    for block in (doc,doc.get("data") if isinstance(doc.get("data"),dict) else {}):
        for k in ("radios","stations","results","items","list"):
            if isinstance(block.get(k),list):
                return block[k],block,block.get("total") or block.get("count")
    if isinstance(doc.get("data"),list):
        return doc["data"],doc,doc.get("total") or doc.get("count")
    raise ValueError("Catalog contains no recognized station list")

def field(item,keys):
    for k in keys:
        v=item.get(k)
        if isinstance(v,str) and v.strip():return v.strip()
        if isinstance(v,dict):
            for sub in ("url","src","value","code"):
                if isinstance(v.get(sub),str) and v[sub].strip():return v[sub].strip()
    return ""

def iso_country(item):
    v=field(item,("country_code","countryCode","countrycode","country","iso","cc"))
    if len(v)==2 and v.isalpha():return v.upper()
    if v:
        try:
            import pycountry
            return pycountry.countries.lookup(v).alpha_2
        except (ImportError,LookupError,KeyError,ValueError,AttributeError):pass
    return ""

def match_logo(row,target):
    if (not isinstance(row,dict) or iso_country(row)!=target["country"] or
        namekey(field(row,("name","title","station_name","stationName")))!=namekey(target["name"])):
        return ""
    stream=field(row,STREAM_KEYS)
    if not (streamkey(stream) and streamkey(stream)==streamkey(target["stream"])):
        return ""
    return safe_url(field(row,IMAGE_KEYS))

def get_country_directory(cc,get=fetch,per_page=PER_PAGE,max_pages=MAX_PAGES):
    output=[];pages=[];fingerprints=set();errors=[];complete=False
    for page in range(1,max_pages+1):
        url=API+"?"+urlencode({"country":cc,"limit":per_page,"page":page})
        try:
            raw=get(url,limit=JSON_MAX,expected_type="application/json")
            data,meta,total=records(json.loads(raw))
            if len(data)>per_page or any(not isinstance(x,dict) for x in data):
                raise ValueError("Invalid public catalog page")
        except (OSError,HTTPError,URLError,TimeoutError,ValueError,UnicodeError,KeyError) as e:
            errors.append(type(e).__name__);break
        fingerprint=sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if fingerprint in fingerprints:
            errors.append("pagination_repeats_previous_page");break
        fingerprints.add(fingerprint)
        pages.append({"page":page,"rows":len(data),"sha256":sha256(raw).hexdigest()})
        output.extend(data)
        try:total=int(total) if total is not None else None
        except (ValueError,TypeError):total=None
        if (not data or meta.get("hasMore",meta.get("has_more")) is False or
            (total is not None and len(output)>=total) or
            (len(data)<per_page and total is None and meta.get("hasMore",meta.get("has_more")) is not True)):
            complete=True;break
        time.sleep(0.12)
    return {"country":cc,"rows":output,"pages":pages,"catalog_complete":complete,"errors":errors}

def png224(raw):
    from PIL import Image,ImageOps
    with Image.open(BytesIO(raw)) as src:
        if (src.format not in ("PNG","JPEG","WEBP") or
            not 80<=src.width<=4000 or not 80<=src.height<=4000 or
            max(src.width,src.height)>4*min(src.width,src.height)):
            raise ValueError("Not a valid broadcaster logo bitmap")
        img=ImageOps.exif_transpose(src).convert("RGBA")
        img.thumbnail((224,224),Image.Resampling.LANCZOS)
        colors=img.convert("RGB").resize((48,48)).getcolors(2304)
        if colors is not None and len(colors)<12:raise ValueError("Generic placeholder")
        canvas=Image.new("RGBA",(224,224),(0,0,0,0))
        canvas.alpha_composite(img,((224-img.width)//2,(224-img.height)//2))
        bio=BytesIO();canvas.save(bio,format="PNG",optimize=True)
        data=bio.getvalue()
        if not 512<len(data)<=500000:raise ValueError("Bad normalized PNG")
        return data

def inventory(world,root):
    index=verify_source(world,WORLD_SHA)
    if ((index["country_count"],index["station_count"])!=(224,EXPECTED_STATIONS) or
        sum(x["logos_found"] for x in index["countries"].values())!=EXPECTED_ORIGINALS):
        raise ValueError("Unexpected previous complete radio world")
    _,_,_,validator=engine(Path(__file__).resolve().parents[1]/"src")
    targets={};previous={};missing=0
    for cc in sorted(index["countries"]):
        bouquet,catalog,manifest,rows=get_country(world,index,cc,validator)
        originals,_=original_package(root,cc,bouquet,catalog,rows)
        if len(originals)!=index["countries"][cc]["logos_found"]:
            raise ValueError("Previous originals count or SHA mismatch "+cc)
        previous[cc]=(originals,manifest,bouquet,catalog)
        targets[cc]=[]
        for row in rows:
            if row["stem"]+".png" in originals:continue
            targets[cc].append({"country":cc,"uuid":row["stationuuid"],"name":row["name"],
                                "stem":row["stem"],"stream":row["url"]})
            missing+=1
    if missing!=EXPECTED_MISSING:raise ValueError("Previous 7451 gap checkpoint mismatch")
    return index,targets,previous

def run(world,root,out,country_fetch=get_country_directory,image_fetch=fetch,workers=WORKERS):
    out=Path(out)
    if out.exists() or out.is_symlink():raise ValueError("Refuse overwrite")
    if type(workers) is not int or not 1<=workers<=WORKERS:raise ValueError("Bad worker count")
    idx,targets,previous=inventory(world,root)
    out.mkdir(parents=True)
    stats=Counter();country_reports={};matches=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(country_fetch,cc):cc for cc in sorted(idx["countries"])}
        for future in as_completed(jobs):
            cc=jobs[future];r=future.result()
            if r["country"]!=cc:raise ValueError("Wrong country response")
            country_reports[cc]={"pages":r["pages"],"rows":len(r["rows"]),
                                 "catalog_complete":r["catalog_complete"],"errors":r["errors"]}
            stats["countries_checked"]+=1;stats["directory_rows"]+=len(r["rows"])
            if not r["pages"]:stats["failed_countries"]+=1
            if r["catalog_complete"]:stats["complete_upstream_countries"]+=1
            byname=defaultdict(list)
            for target in targets[cc]:byname[namekey(target["name"])].append(target)
            for source in r["rows"]:
                for target in byname.get(namekey(field(source,("name","title","station_name","stationName"))),[]):
                    link=match_logo(source,target)
                    if link:matches.append((target,link))
    if stats["failed_countries"]>16:
        raise ValueError("Public directory unavailable; do not retry rate limits")
    choices=defaultdict(set);links=defaultdict(set)
    for target,url in matches:
        choices[target["uuid"]].add(url)
        links[url].add((target["country"],namekey(target["name"])))
    strong={t["uuid"]:(t,u) for t,u in matches if
            len(choices[t["uuid"]])==1 and len(links[u])==1}
    stats["strict_source_matches"]=len(matches)
    stats["unique_identity_candidates"]=len(strong)
    images={}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(image_fetch,url,limit=IMG_MAX,expected_type="image/"):(t,url)
              for t,url in strong.values()}
        for future in as_completed(jobs):
            t,url=jobs[future]
            try:
                raw=future.result();png=png224(raw)
                images[t["uuid"]]={"target":t,"image_url":url,"png":png,
                                    "source_sha256":sha256(raw).hexdigest(),"png_sha256":sha256(png).hexdigest()}
            except (OSError,ValueError,TypeError,TimeoutError,URLError,HTTPError):
                stats["image_rejections"]+=1
    duplicates=defaultdict(set)
    for r in images.values():
        duplicates[r["png_sha256"]].add((r["target"]["country"],namekey(r["target"]["name"])))
    additions=Counter();evidence=[]
    for r in images.values():
        if len(duplicates[r["png_sha256"]])!=1:
            stats["quarantined_generic_shared_images"]+=1;continue
        t=r["target"];cc=t["country"]
        previous[cc][0][t["stem"]+".png"]=r["png"]
        additions[cc]+=1
        evidence.append({**t,"directory":"RadaRadio","image_url":r["image_url"],
                         "image_source_sha256":r["source_sha256"],"png_sha256":r["png_sha256"],
                         "identity":"exact_country_name_stream","visual_review_required":True})
    for cc in sorted(additions):
        pngs,manifest,bouquet,catalog=previous[cc]
        if len(pngs)!=idx["countries"][cc]["logos_found"]+additions[cc]:
            raise ValueError("Changed country logo count mismatch")
        archive=encode_logos(pngs)
        latest=dict(manifest);latest.update({"logos_found":len(pngs),
            "logos_missing":idx["countries"][cc]["stations"]-len(pngs),
            "logo_attempted":idx["countries"][cc]["stations"],"logo_package_complete":True})
        latest["files"]=dict(manifest["files"])
        latest["files"]["logos/"+cc+".zip"]={"sha256":sha256(archive).hexdigest(),"bytes":len(archive)}
        path=out/"candidates"/("radio-country-"+cc+"-REVIEW-NOT-PRODUCTION")
        for rel,data in ((f"bouquets/{cc}.radio",bouquet),(f"catalog/{cc}.json",catalog),
                         (f"logos/{cc}.zip",archive),(f"manifests/{cc}.json",
                         (json.dumps(latest,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode())):
            save(path/rel,data)
    report={"schema":1,"review_only":True,"directory":"RadaRadio read-only",
            "previous_world_sha256":WORLD_SHA,"countries_scanned":224,
            "stations":EXPECTED_STATIONS,"originals_before":EXPECTED_ORIGINALS,
            "missing_before":EXPECTED_MISSING,"new_candidate_png":len(evidence),
            "new_total_candidate_png":EXPECTED_ORIGINALS+len(evidence),
            "missing_after_candidate":EXPECTED_MISSING-len(evidence),
            "new_countries":len(additions),"per_country_additions":dict(sorted(additions.items())),
            "stats":dict(stats),"upstream_countries":country_reports,
            "candidate_images":sorted(evidence,key=lambda x:(x["country"],x["uuid"])),
            "previous_pngs_byte_unchanged":True,"visual_review_required":True,
            "production_published":False}
    save(out/"radaradio-7451-global-REVIEW.json",
         (json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode())
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--world",type=Path,required=True)
    p.add_argument("--old-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=run(a.world,a.old_root,a.out)
    print(json.dumps({"countries":result["countries_scanned"],"prior":result["originals_before"],
       "new_candidates":result["new_candidate_png"],"missing":result["missing_after_candidate"],
       "stats":result["stats"]},sort_keys=True),flush=True)

if __name__=="__main__":main()
