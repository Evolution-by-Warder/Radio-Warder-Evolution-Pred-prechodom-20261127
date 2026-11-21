#!/usr/bin/env python3
"""Single 7451-gap global name-query + exact broadcaster homepage logo REVIEW.

RadaRadio's public /api/radios list is capped at 100 and ignores page/offset.
Only q=station-name exposes stations outside the top 100. Source's list and
detail endpoints do NOT expose stream URLs. Match only exact country/name
and identical broadcaster-owned website host+path from verified Radio Browser
catalogues. Ambiguous/other-brand images are quarantined. REVIEW ONLY.
"""
import argparse
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from pathlib import Path
import ipaddress, json, re, time
from urllib.parse import urlsplit, urlencode
from urllib.request import Request
from urllib.error import HTTPError, URLError
from recover_radaradio_7451_world import (
    inventory, png224, fetch, safe_url, public_host, field, iso_country,
    records, API, OPENER, JSON_MAX, IMG_MAX, IMAGE_KEYS, WORKERS, WORLD_SHA,
    EXPECTED_STATIONS, EXPECTED_ORIGINALS, EXPECTED_MISSING
)
from stage_two_independent_radio_directories_all_7826 import namekey
from recover_missing_radio_logos import encode_logos
from build_country_radio_packages import save

MAX_Q_LEN=180
Q_LIMIT=100
BATCH=100
HASH_RE=re.compile(r"^[a-zA-Z0-9_-]{3,100}$")

def website_identity(url):
    if not isinstance(url,str) or len(url)>1800:return ()
    try:
        p=urlsplit(url.strip())
        host=(p.hostname or "").lower().removeprefix("www.")
        if (p.scheme not in ("http","https") or not host or "." not in host or
            p.username or p.password or p.port not in (None,80,443) or
            host.endswith((".local",".internal",".test",".invalid")) or
            host in ("facebook.com","youtube.com","instagram.com","linktr.ee")):
            return ()
        try:ipaddress.ip_address(host);return ()
        except ValueError:pass
        path=p.path.lower().rstrip("/")
        path=re.sub(r"/(?:index|default)\.(?:html?|aspx?)$","",path)
        return (host,path.rstrip("/"))
    except (ValueError,TypeError,AttributeError):return ()

def exact_match(source, detail, target):
    if not isinstance(source,dict) or not isinstance(detail,dict):return ""
    if (iso_country(source)!=target["country"] or
        iso_country(detail)!=target["country"] or
        source.get("id")!=detail.get("id") or
        namekey(field(source,("name",)))!=namekey(target["name"]) or
        namekey(field(detail,("name",)))!=namekey(target["name"])):
        return ""
    owner=website_identity(target.get("homepage"))
    current=website_identity(field(detail,("website","homepage")))
    if not owner or owner!=current:return ""
    if field(source,IMAGE_KEYS)!=field(detail,IMAGE_KEYS):return ""
    return safe_url(field(source,IMAGE_KEYS))

def search_name(cc,name,get=fetch):
    if not re.fullmatch(r"[A-Z]{2}",cc) or not 1<=len(name.strip())<=MAX_Q_LEN:
        raise ValueError("Invalid country or target station name")
    query=API+"?"+urlencode({"country":cc,"q":name,"limit":Q_LIMIT})
    raw=get(query,limit=JSON_MAX,expected_type="application/json")
    arr,_,_=records(json.loads(raw))
    if len(arr)>Q_LIMIT or any(not isinstance(x,dict) for x in arr):
        raise ValueError("Bad public search response")
    match=[x for x in arr if (
        iso_country(x)==cc and namekey(field(x,("name",)))==namekey(name)
        and safe_url(field(x,IMAGE_KEYS))
        and isinstance(x.get("id"),str) and HASH_RE.fullmatch(x["id"]))]
    return match,sha256(raw).hexdigest(),len(arr)

def source_detail(station_id, get=None):
    if not isinstance(station_id,str) or not HASH_RE.fullmatch(station_id):
        raise ValueError("Invalid public station detail ID")
    endpoint=API+"/"+station_id
    if get is not None:
        data=get(endpoint)
    else:
        if not public_host("radaradio.com"):raise ValueError("Untrusted source DNS")
        request=Request(endpoint,headers={
            "User-Agent":"WarderRadioCountryNameOwnerEvidence/1.0",
            "Accept":"application/json"})
        with OPENER.open(request,timeout=15) as response:
            if (response.status!=200 or response.geturl()!=endpoint or
                response.headers.get("Content-Type","").split(";")[0].strip().lower()!="application/json"):
                raise ValueError("Unexpected official source detail response")
            data=response.read(JSON_MAX+1)
    if len(data)>JSON_MAX:raise ValueError("Oversized source detail")
    doc=json.loads(data)
    if not isinstance(doc,dict) or doc.get("id")!=station_id:
        raise ValueError("Mismatched upstream station detail")
    return doc,sha256(data).hexdigest()

def run(world, originals, out, name_fetch=search_name, detail_fetch=source_detail,
        image_fetch=fetch, workers=WORKERS):
    out=Path(out)
    if out.exists() or out.is_symlink():raise ValueError("Do not overwrite previous REVIEW")
    if type(workers) is not int or not 1<=workers<=WORKERS:
        raise ValueError("Unsafe source concurrency")
    idx,targets,previous=inventory(world,originals)
    out.mkdir(parents=True)
    stats=Counter()
    queries=defaultdict(list)
    for cc in sorted(idx["countries"]):
        for target in targets[cc]:
            if not website_identity(target.get("homepage")):
                stats["no_verified_owner_homepage"]+=1
                continue
            if not 1<=len(target["name"].strip())<=MAX_Q_LEN:
                stats["unqueryable_station_name"]+=1
                continue
            queries[(cc,namekey(target["name"]))].append(target)
    keys=sorted(queries)
    if len(keys)>EXPECTED_MISSING:raise ValueError("Not a 7451-station missing inventory")
    results=[];proof=[]
    for offset in range(0,len(keys),BATCH):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            jobs={pool.submit(name_fetch,cc,queries[(cc,n)][0]["name"]):(cc,n)
                  for cc,n in keys[offset:offset+BATCH]}
            for job in as_completed(jobs):
                cc,n=jobs[job];stats["source_searches_attempted"]+=1
                try:
                    records_found,digest,total=job.result()
                    stats["source_rows_examined"]+=total
                    stats["exact_country_station_hits"]+=len(records_found)
                    proof.append({"country":cc,"station_name_key":n,
                                  "source_sha256":digest,"matching_rows":len(records_found),
                                  "source_rows":total})
                    for entry in records_found:
                        for target in queries[(cc,n)]:results.append((target,entry))
                except (HTTPError,URLError,OSError,TimeoutError,ValueError,KeyError) as exc:
                    stats["source_search_failures"]+=1
                    if isinstance(exc,HTTPError) and exc.code==429:stats["rate_limited"]+=1
        if stats["rate_limited"]>=2:
            raise ValueError("Rate-limited public API; do not bypass or continue mass requests")
        if offset%1000==0:
            print("ONE GLOBAL 7451 MISSING SOURCE NAME PASS",offset+len(jobs),"/",len(keys),
                  "source_hits",stats["exact_country_station_hits"],flush=True)
    stats["unique_name_country_queries"]=len(keys)
    if (stats["source_searches_attempted"]!=len(keys) or
        stats["source_search_failures"]>max(8,len(keys)//100)):
        raise ValueError("Incomplete public source search pass; refuse to merge")
    detail_by_id={}
    ids=sorted({source["id"] for _,source in results})
    for offset in range(0,len(ids),BATCH):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            jobs={pool.submit(detail_fetch,station_id):station_id for station_id in ids[offset:offset+BATCH]}
            for job in as_completed(jobs):
                station_id=jobs[job];stats["detail_requests"]+=1
                try:detail_by_id[station_id]=job.result()
                except (HTTPError,URLError,OSError,TimeoutError,ValueError,KeyError) as exc:
                    stats["detail_failures"]+=1
                    if isinstance(exc,HTTPError) and exc.code==429:stats["rate_limited"]+=1
        if stats["rate_limited"]>=2:
            raise ValueError("Upstream detail rate limit; do not bypass")
    if stats["detail_failures"]>max(5,len(ids)//50):
        raise ValueError("Too many missing broadcaster identity details")
    per_uuid=defaultdict(set);target_by_uuid={}
    for target,source in results:
        detail_tuple=detail_by_id.get(source["id"])
        if detail_tuple is None:continue
        detail,detail_sha=detail_tuple
        url=exact_match(source,detail,target)
        if url:
            per_uuid[target["uuid"]].add((url,source["id"],detail_sha))
            target_by_uuid[target["uuid"]]=target
    matched={uuid:next(iter(candidates)) for uuid,candidates in per_uuid.items()
             if len(candidates)==1}
    stats["exact_name_country_official_homepage"]=len(matched)
    images={}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(image_fetch,evidence[0],limit=IMG_MAX,expected_type="image/"):
              (target_by_uuid[uuid],evidence) for uuid,evidence in matched.items()}
        for job in as_completed(jobs):
            target,evidence=jobs[job];url,station_id,detail_sha=evidence
            try:
                data=job.result();png=png224(data)
                images[target["uuid"]]=dict(target=target,image_url=url,
                     source_station_id=station_id,detail_sha256=detail_sha,png=png,
                     image_sha256=sha256(data).hexdigest(),png_sha256=sha256(png).hexdigest())
            except (HTTPError,URLError,OSError,TimeoutError,ValueError,TypeError):
                stats["unusable_images"]+=1
    reuse=defaultdict(set)
    for record in images.values():
        t=record["target"]
        reuse[record["png_sha256"]].add((t["country"],namekey(t["name"])))
    accepted=[];additions=Counter()
    for record in images.values():
        if len(reuse[record["png_sha256"]])!=1:
            stats["quarantined_shared_other_brand_images"]+=1
            continue
        target=record["target"];cc=target["country"]
        previous[cc][0][target["stem"]+".png"]=record["png"]
        additions[cc]+=1
        accepted.append({**target,"source":"RadaRadio", "source_station_id":record["source_station_id"],
                         "source_detail_sha256":record["detail_sha256"],
                         "image_url":record["image_url"],
                         "image_source_sha256":record["image_sha256"],
                         "png_sha256":record["png_sha256"],
                         "identity":"exact_country_name_official_homepage",
                         "visual_review_required":True})
    for cc in sorted(additions):
        pngs,manifest,bouquet,catalog=previous[cc]
        assert len(pngs)==idx["countries"][cc]["logos_found"]+additions[cc]
        archive=encode_logos(pngs)
        latest=dict(manifest)
        latest.update(logos_found=len(pngs),
                      logos_missing=idx["countries"][cc]["stations"]-len(pngs),
                      logo_attempted=idx["countries"][cc]["stations"],logo_package_complete=True)
        latest["files"]=dict(manifest["files"])
        latest["files"]["logos/"+cc+".zip"]={"sha256":sha256(archive).hexdigest(),"bytes":len(archive)}
        path=out/"candidates"/("radio-country-"+cc+"-REVIEW-NOT-PRODUCTION")
        for relative,data in ((f"bouquets/{cc}.radio",bouquet),(f"catalog/{cc}.json",catalog),
                              (f"logos/{cc}.zip",archive),
                              (f"manifests/{cc}.json",
                               (json.dumps(latest,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode())):
            save(path/relative,data)
    report={"schema":2,"review_only":True,"source":"RadaRadio public exact-name + operator-website directory",
            "previous_world_sha256":WORLD_SHA,"countries_scanned":224,
            "stations":EXPECTED_STATIONS,"originals_before":EXPECTED_ORIGINALS,
            "missing_before":EXPECTED_MISSING,"new_candidate_png":len(accepted),
            "new_total_candidate_png":EXPECTED_ORIGINALS+len(accepted),
            "missing_after_candidate":EXPECTED_MISSING-len(accepted),
            "new_countries":len(additions),"per_country_additions":dict(sorted(additions.items())),
            "stats":dict(stats),"targeted_search_evidence":sorted(proof,key=lambda r:(r["country"],r["station_name_key"])),
            "candidate_images":sorted(accepted,key=lambda r:(r["country"],r["uuid"])),
            "previous_pngs_byte_unchanged":True,"visual_review_required":True,
            "production_published":False}
    save(out/"radaradio-7451-global-REVIEW.json",
         (json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode())
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world",type=Path,required=True)
    parser.add_argument("--old-root",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.world,args.old_root,args.out)
    print(json.dumps({"countries":result["countries_scanned"],
          "searched":result["stats"]["unique_name_country_queries"],
          "exact_candidate_original_png":result["new_candidate_png"],
          "remaining_without_artwork":result["missing_after_candidate"],
          "stats":result["stats"]},sort_keys=True),flush=True)

if __name__=="__main__":main()
