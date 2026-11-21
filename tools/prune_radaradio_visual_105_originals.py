#!/usr/bin/env python3
"""Prune exact UUIDs of visibly wrong RadaRadio artwork, rebuild ONE 224-country REVIEW.

This is strictly additive to original world 40768 PNG. The only deletions are
from the 105 *new* candidate source UUIDs. No existing country logo may be
replaced or removed; no production release code is present.
"""
import argparse,hashlib,json,re
from collections import Counter,defaultdict
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from recover_missing_radio_logos import encode_logos
from build_country_radio_packages import save

PREVIOUS_SHA="a3237e7d3ee5218eee4b30b6bff15c73e384657d17d8b8fb28fa21a690e4863b"
SOURCE_SHA="ed8928350a6b5270ef1871b0196630082572f9105977667fdb4cc5b19ed28d0a"
UUID_RE=re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")
PNG_RE=re.compile(r"^4097_0_2_(?:[0-9A-F]{1,8}_){6}[0-9A-F]{1,8}\.png$")

def hash_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for data in iter(lambda:f.read(1<<20),b""):h.update(data)
    return h.hexdigest()
def sha(raw):return hashlib.sha256(raw).hexdigest()

def verify_decisions(source,decisions):
    if (source.get("schema")!=2 or source.get("review_only") is not True or
        source.get("previous_world_sha256")!=PREVIOUS_SHA or
        source.get("new_candidate_png")!=105):
        raise ValueError("Wrong SHA-pinned 105-candidate source")
    if (decisions.get("schema")!=1 or decisions.get("review_only") is not True or
        decisions.get("source_candidate_world_sha256")!=SOURCE_SHA or
        decisions.get("source_reviewed_images")!=105 or
        decisions.get("visual_approved_count")!=69 or
        decisions.get("production_published") is not False):
        raise ValueError("Visual decision source/count mismatch")
    records=source["candidate_images"]
    by_uuid={r["uuid"]:r for r in records}
    if len(by_uuid)!=105 or len(records)!=105:
        raise ValueError("Duplicate source station candidate")
    rejects={}
    for row in decisions["visual_rejected"]:
        uuid=row.get("stationuuid");reason=row.get("reason")
        if (not isinstance(uuid,str) or not UUID_RE.fullmatch(uuid) or uuid not in by_uuid
            or uuid in rejects or not isinstance(reason,str) or
            not re.fullmatch(r"[a-z_]{5,80}",reason)):
            raise ValueError("Unpinned or ambiguous visual rejection")
        rejects[uuid]=reason
    if len(rejects)!=36 or len(rejects)+decisions["visual_approved_count"]!=105:
        raise ValueError("Unexpected visual rejection count")
    return by_uuid,rejects

def country_bytes(stage,cc,source_index,previous_index,by_uuid,rejects):
    root=Path(stage)/"candidates"/("radio-country-"+cc+"-REVIEW-NOT-PRODUCTION")
    package=root/"logos"/(cc+".zip")
    manifest_path=root/"manifests"/(cc+".json")
    if not package.is_file() or package.is_symlink() or not manifest_path.is_file():
        raise ValueError("Missing source changed-country candidate bundle "+cc)
    source_meta=source_index["countries"][cc]
    original_meta=previous_index["countries"][cc]
    current=package.read_bytes()
    if (sha(current)!=source_meta["logo_sha256"] or
        len(current)>1024*1024*1024):
        raise ValueError("Source changed-country PNG SHA mismatch "+cc)
    manifest=json.loads(manifest_path.read_bytes())
    if (manifest.get("logos_found")!=source_meta["logos_found"] or
        manifest["files"]["logos/"+cc+".zip"]["sha256"]!=sha(current)):
        raise ValueError("Signed source country manifest not verified "+cc)
    with ZipFile(package) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)) or len(names)!=source_meta["logos_found"]:
            raise ValueError("Unexpected source PNG member count "+cc)
        if any(not PNG_RE.fullmatch(name) for name in names):
            raise ValueError("Invalid Enigma2 logo filename "+cc)
        picon={name:archive.read(name) for name in names}
    items={uuid:r for uuid,r in by_uuid.items() if r["country"]==cc}
    if len(picon)!=original_meta["logos_found"]+len(items):
        raise ValueError("Old originals were already lost before visual review "+cc)
    source_new_names={r["stem"]+".png" for r in items.values()}
    if len(source_new_names)!=len(items) or not source_new_names<=set(picon):
        raise ValueError("Unknown source visual candidate PNG basename "+cc)
    for row in items.values():
        name=row["stem"]+".png"
        if sha(picon[name])!=row["png_sha256"]:
            raise ValueError("Visually reviewed PNG differs from source SHA "+cc)
    # Drop only source-stage additions; all original names are outside this set.
    removed=[]
    for uuid in rejects:
        row=items.get(uuid)
        if row is not None:
            removed.append(uuid)
            del picon[row["stem"]+".png"]
    approved_count=len(items)-len(removed)
    assert len(picon)==original_meta["logos_found"]+approved_count
    assert len(picon)>=original_meta["logos_found"]
    archive=encode_logos(picon)
    latest=dict(manifest)
    latest["logos_found"]=len(picon)
    latest["logos_missing"]=source_meta["stations"]-len(picon)
    latest["logo_attempted"]=source_meta["stations"]
    latest["logo_package_complete"]=True
    latest["files"]=dict(manifest["files"])
    latest["files"]["logos/"+cc+".zip"]={"sha256":sha(archive),"bytes":len(archive)}
    return archive,(json.dumps(latest,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode(),{
        "country":cc,"original":original_meta["logos_found"],
        "source_candidate":len(items),"visually_rejected":len(removed),
        "visually_approved":approved_count,"new_total":len(picon),
        "logo_sha256":sha(archive),"bytes":len(archive)}

def run(old_world,new_world,stage,decisions_path,out):
    out=Path(out)
    if out.exists() or out.is_symlink():raise ValueError("Refuse overwrite prior reviewed output")
    if hash_file(old_world)!=PREVIOUS_SHA or hash_file(new_world)!=SOURCE_SHA:
        raise ValueError("Wrong pinned complete world source")
    source_path=Path(stage)/"radaradio-7451-global-REVIEW.json"
    if not source_path.is_file():raise ValueError("Missing source candidates audit JSON")
    source=json.loads(source_path.read_bytes())
    decisions=json.loads(Path(decisions_path).read_bytes())
    by_uuid,rejects=verify_decisions(source,decisions)
    with ZipFile(old_world) as old,ZipFile(new_world) as new:
        before=json.loads(old.read("index.json"))
        candidate=json.loads(new.read("index.json"))
        if (before["country_count"],before["station_count"])!=(224,48219):
            raise ValueError("Old source lost world stations")
        if set(old.namelist())!=set(new.namelist()) or len(before["countries"])!=224:
            raise ValueError("World ZIP members changed")
        if sum(x["logos_found"] for x in before["countries"].values())!=40768:
            raise ValueError("Unexpected old world original count")
        if sum(x["logos_found"] for x in candidate["countries"].values())!=40873:
            raise ValueError("Unexpected visual source candidate count")
        affected=set(source["per_country_additions"])
        if len(affected)!=30 or any(cc not in candidate["countries"] for cc in affected):
            raise ValueError("Wrong candidate country list")
        content={entry.filename:new.read(entry.filename) for entry in new.infolist()}
        for name in old.namelist():
            if name in ("index.json",) or name in {"manifests/"+c+".json" for c in affected}:
                continue
            if old.read(name)!=content[name]:
                raise ValueError("World catalog or bouquet changed "+name)
    report=[]
    for cc in sorted(affected):
        country_archive,manifest,data=country_bytes(stage,cc,candidate,before,by_uuid,rejects)
        expected=source["per_country_additions"][cc]
        if expected!=data["source_candidate"]:
            raise ValueError("Candidate source count mismatch "+cc)
        report.append(data)
        target=out/"approved-countries"/("radio-country-"+cc+"-REVIEW-NOT-PRODUCTION")
        source_root=Path(stage)/"candidates"/target.name
        for rel in (f"bouquets/{cc}.radio",f"catalog/{cc}.json"):
            save(target/rel,(source_root/rel).read_bytes())
        save(target/f"logos/{cc}.zip",country_archive)
        save(target/f"manifests/{cc}.json",manifest)
        content[f"manifests/{cc}.json"]=manifest
        candidate["countries"][cc]["logos_found"]=data["new_total"]
        candidate["countries"][cc]["logo_sha256"]=data["logo_sha256"]
        candidate["countries"][cc]["logo_package_complete"]=True
    if (sum(r["visually_approved"] for r in report)!=69 or
        sum(r["visually_rejected"] for r in report)!=36 or
        sum(x["logos_found"] for x in candidate["countries"].values())!=40837):
        raise ValueError("Visually approved final world count mismatch")
    content["index.json"]=(json.dumps(candidate,ensure_ascii=False,sort_keys=True,
                                    separators=(",",":"))+"\n").encode()
    path=out/"new-world"/"radio-countries-bouquets.zip"
    path.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(path,"w",compression=ZIP_DEFLATED,compresslevel=6,allowZip64=False) as z:
        for name in sorted(content):
            entry=ZipInfo(name,date_time=(1980,1,1,0,0,0))
            entry.compress_type=ZIP_DEFLATED
            entry.external_attr=0o644<<16
            z.writestr(entry,content[name],compress_type=ZIP_DEFLATED,compresslevel=6)
    with ZipFile(path) as final:
        clean=json.loads(final.read("index.json"))
        if sum(x["logos_found"] for x in clean["countries"].values())!=40837:
            raise ValueError("Wrong visually approved world")
        if set(final.namelist())!=set(content):
            raise ValueError("Lost world member during visual prune")
        for name in content:
            if final.read(name)!=content[name]:
                raise ValueError("Changed decompressed world member "+name)
    summary={"schema":1,"review_only":True,"source_world_sha256":PREVIOUS_SHA,
        "unapproved_candidate_world_sha256":SOURCE_SHA,"world_sha256":hash_file(path),
        "world_size":path.stat().st_size,"countries":224,"station_refs":48219,
        "old_png_preserved":40768,"source_candidate_png":105,
        "visually_rejected_png":36,"visually_approved_new_png":69,
        "world_png":40837,"still_missing":7382,
        "changed_country_zips":30,"per_country":report,
        "catalogues_and_bouquets_byte_identical":224,
        "production_published":False}
    save(out/"radaradio-69-visual-approval-review.json",
         (json.dumps(summary,indent=2,sort_keys=True)+"\n").encode())
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old-world",required=True,type=Path)
    p.add_argument("--new-world",required=True,type=Path)
    p.add_argument("--stage",required=True,type=Path)
    p.add_argument("--decisions",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=run(a.old_world,a.new_world,a.stage,a.decisions,a.out)
    print(json.dumps({k:v for k,v in result.items() if k!="per_country"},sort_keys=True),flush=True)

if __name__=="__main__":main()
