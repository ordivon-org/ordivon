#!/usr/bin/env python3
"""Phase 1 source CONTENT-facet probe, complementary to source locator census.

Reads exact immutable Git objects. No working-tree search, eval, imports,
executions, filesystem moves, owner admission, or semantic/proof claims.
"""
from __future__ import annotations
import argparse
import ast
import collections
import hashlib
import json
import re
import subprocess
import tomllib
from pathlib import Path, PurePosixPath

SEED_PATH = "docs/architecture/evidence/ORDIVON_PHASE1_NAME_SEEDS_20261027_R4.json"
MAX_READ_BYTES = 98304
BINARY_EXTENSIONS = frozenset({".png",".jpg",".jpeg",".gif",".webp",".svgz",".ico",".wav",".mp3",".mp4",".mkv",".mov",".ogg",".flac",".pdf",".woff",".woff2",".ttf",".otf",".zip",".gz",".tar",".exe",".dll",".so",".bin",".wasm",".jar",".pkl",".sqlite",".db"})
SOURCE_EXTENSIONS = frozenset({".py",".rs",".ts",".tsx",".js",".mjs",".sh",".ps1",".gd",".lean",".sql",".rego",".cpp",".c",".h"})
TOPIC_HINTS = frozenset({"kind","schemaVersion","id","name","type","status","subjectRef","sourceCut","sourceRevision"})


def git(*args: str, repo: Path) -> bytes:
    p = subprocess.run(["git","--no-replace-objects","-C",str(repo),*args],capture_output=True)
    if p.returncode:
        raise ValueError(f"Git failed at {args[:2]}: {p.stderr[:280]!r}")
    return p.stdout


def exact_git_commit(repo: Path, oid: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{40}",oid):
        raise ValueError("subject SourceCut must be exact 40-char lowercase OID")
    v=git("rev-parse","--verify",oid+"^{commit}",repo=repo).decode().strip()
    if oid!=v: raise ValueError("sourceCut does not identify an exact Git commit")
    return oid


def exact_tree(repo: Path, cut: str) -> list[dict]:
    cut=exact_git_commit(repo,cut)
    rows=[]
    for raw in git("ls-tree","-r","-z",cut,repo=repo).split(b"\0"):
        if not raw: continue
        header,name=raw.split(b"\t",1)
        mode,typ,oid=header.decode("ascii").split()
        rows.append({"path":name.decode("utf8","surrogateescape"),"mode":mode,
                     "objectType":typ,"blobOid":oid})
    if len(rows)!=len({x["path"] for x in rows}):
        raise ValueError("duplicate path in Git cut")
    return sorted(rows,key=lambda x:x["path"])


def batch_sizes(repo: Path, oids: list[str]) -> dict[str,int]:
    p=subprocess.run(["git","--no-replace-objects","-C",str(repo),"cat-file","--batch-check"],
                     input=("".join(s+"\n" for s in oids)).encode(),capture_output=True,check=True)
    d={}
    for line in p.stdout.decode().splitlines():
        parts=line.split()
        if len(parts)!=3 or parts[1]!="blob": raise ValueError("unexpected Git object type")
        d[parts[0]]=int(parts[2])
    if len(d)!=len(oids): raise ValueError("incomplete Git object sizes")
    return d


def batch_contents(repo: Path, oids: list[str], sizes: dict[str,int]) -> dict[str,bytes]:
    p=subprocess.run(["git","--no-replace-objects","-C",str(repo),"cat-file","--batch"],
                     input=("".join(s+"\n" for s in oids)).encode(),capture_output=True,check=True)
    result={}; data=p.stdout; pos=0
    for oid in oids:
        nl=data.index(b"\n",pos)
        header=data[pos:nl].decode().split()
        if len(header)!=3 or header[0]!=oid or header[1]!="blob":
            raise ValueError("wrong object returned for requested blob")
        n=int(header[2]); assert n==sizes[oid]
        start=nl+1;stop=start+n
        if stop>=len(data) or data[stop:stop+1]!=b"\n":
            raise ValueError("missing complete blob delimiter")
        result[oid]=data[start:stop]
        pos=stop+1
    if pos!=len(data): raise ValueError("trailing bytes in Git batch")
    return result


def content_probe(path: str, mode: str, size: int, content: bytes | None) -> dict:
    ext=PurePosixPath(path).suffix.lower()
    if ext in BINARY_EXTENSIONS:
        return {"contentForm":"BINARY_OR_MEDIA_FILE","readStanding":"SKIPPED_BINARY"}
    if content is None:
        return {"contentForm":"LARGE_OR_UNREAD_FILE","readStanding":"SKIPPED_SIZE_BOUND",
                "bytes":size}
    try:
        text=content.decode("utf8")
    except UnicodeDecodeError:
        return {"contentForm":"OPAQUE_NON_UTF8","readStanding":"OPAQUE_ENCODING"}
    if "\x00" in text:
        return {"contentForm":"OPAQUE_BINARY_BYTES","readStanding":"OPAQUE_ENCODING"}
    if ext in (".json",".jsonl"):
        try:
            doc=json.loads(text if ext==".json" else text.splitlines()[0])
        except (ValueError,IndexError) as e:
            return {"contentForm":"JSON_SYNTAX_UNQUALIFIED","readStanding":"PARSE_FAILURE",
                    "errorClass":type(e).__name__}
        if isinstance(doc,dict):
            wanted={k:doc[k] for k in TOPIC_HINTS if k in doc and isinstance(doc[k],(str,int,bool))}
            return {"contentForm":"JSON_OBJECT_DECLARATION","readStanding":"SYNTAX_PARSED",
                    "claimedFields":dict(sorted(wanted.items()))}
        return {"contentForm":"JSON_"+type(doc).__name__.upper(),"readStanding":"SYNTAX_PARSED"}
    if ext==".py":
        try: mod=ast.parse(text)
        except SyntaxError:
            return {"contentForm":"PYTHON_SOURCE","readStanding":"SYNTAX_INVALID_OR_INCOMPATIBLE"}
        symbols=[n.name for n in mod.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
        return {"contentForm":"PYTHON_TEST_SOURCE" if path.split("/")[-1].startswith("test_") else "PYTHON_SOURCE",
                "readStanding":"SYNTAX_PARSED","topSymbols":symbols[:6]}
    if ext==".toml":
        try: config=tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            return {"contentForm":"TOML_CONFIGURATION","readStanding":"PARSE_FAILURE"}
        return {"contentForm":"TOML_CONFIGURATION","readStanding":"SYNTAX_PARSED",
                "topKeys":list(config)[:8]}
    if ext==".md":
        heads=re.findall(r"(?m)^#{1,3}\s+(.+)$",text)
        return {"contentForm":"MARKDOWN_DOCUMENT","readStanding":"HEADING_EXTRACTED" if heads else "TEXT_ONLY",
                "headings":heads[:3]}
    if ext in SOURCE_EXTENSIONS:
        syntax={" .lean":"Lean"}.get(" "+ext,ext[1:].upper())
        matches=re.findall(r"(?m)^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:fn|def|theorem|lemma|function|class|interface|export\s+(?:function|class|const)|CREATE\s+(?:TABLE|INDEX))\s+([A-Za-z_][\w]*)",text)
        return {"contentForm":"SOURCE_"+syntax,"readStanding":"LEXICAL_ONLY",
                "declaredSymbols":matches[:6]}
    if text.startswith("#!"):
        return {"contentForm":"SHEBANG_SCRIPT","readStanding":"SHEBANG_OBSERVED",
                "shebangInterpreter":text.splitlines()[0][:110]}
    if ext in (".yaml",".yml",".xml",".lock",".cfg",".ini",".service",".target",".timer"):
        return {"contentForm":"STRUCTURED_TEXT_OR_CONFIG","readStanding":"TEXT_OBSERVED"}
    if not ext and mode=="100755":
        return {"contentForm":"EXECUTABLE_TEXT_UNKNOWN_LANGUAGE","readStanding":"TEXT_OBSERVED"}
    return {"contentForm":"TEXT_OTHER_UNKNOWN_FUNCTION","readStanding":"TEXT_OBSERVED"}


def candidate_zone(path: str,zones: list[dict]) -> str:
    hits=[z for z in zones if z.get("sourcePrefix") and path.startswith(z["sourcePrefix"])]
    if hits:
        # An explicitly narrower source region (the LEGO method Skill)
        # overrides the broad .agents/skills navigation region. This is
        # lexical source placement only; it does not confer ownership.
        specificity=max(len(z["sourcePrefix"]) for z in hits)
        specific=[z for z in hits if len(z["sourcePrefix"])==specificity]
        if len(specific)==1:return specific[0]["sourceRef"]
        raise ValueError("equally-specific source zones for "+path)
    roots=[z["sourceRef"] for z in zones if z.get("sourcePrefix")==""
           and "repository-root" in z.get("sourceRef","")]
    if len(roots)==1 and "/" not in path:
        return roots[0]
    raise ValueError("Unclassified physical source path: "+path)


def compile_projection(repo: Path, cut: str) -> dict:
    rows=exact_tree(repo,cut)
    # The bounded source naming seeds are part of the same exact Git cut.
    # Avoid a private unmerged local commit as an implicit dependency.
    seed=json.loads(git("show",cut+":"+SEED_PATH,repo=repo))
    if seed.get("truthRole")!="NON_AUTHORITATIVE_SOURCE_LABEL_EVIDENCE_NOT_IMPLEMENTATION":
        raise ValueError("source naming seed cannot grant functional authority")
    zones=seed["sourceRegions"]
    dense=seed["denseCellAliases"]
    specific=seed["specificPathDisplayAliases"]
    if len(dense)!=60 or len(zones)!=30 or len(specific)!=26:
        raise ValueError("SourceCut must provide 30 zones, 60 dense and 26 specific alias candidates")
    if len({v["candidateName"] for v in specific})!=26:
        raise ValueError("duplicate scoped source display aliases")
    for v in specific:
        prefix=v.get("sourcePrefix")
        if (not isinstance(prefix,str) or not prefix.endswith("/")
                or prefix.startswith("/") or ".." in prefix.split("/")
                or chr(92) in prefix):
            raise ValueError("specific alias requires canonical Git source directory")
        if v.get("semanticQualification")!="UNQUALIFIED" or v.get("canRenamePhysicalPath") is not False:
            raise ValueError("source-only aliases cannot qualify meaning or authorize renames")
    oids=sorted({x["blobOid"] for x in rows if x["objectType"]=="blob"})
    sizes=batch_sizes(repo,oids)
    eligible=[oid for oid in oids if sizes[oid]<=MAX_READ_BYTES]
    content=batch_contents(repo,eligible,sizes)
    content_counts=collections.Counter(); zones_count=collections.Counter()
    inspected=collections.Counter();labels=collections.Counter(); ambiguity=collections.Counter()
    path_rows=[];dense_hits=collections.defaultdict(list); maxsize=0
    for entry in rows:
        path=entry["path"]; zone=candidate_zone(path,zones)
        sz=sizes[entry["blobOid"]]; maxsize=max(maxsize,sz)
        content_info=content_probe(path,entry["mode"],sz,content.get(entry["blobOid"]))
        content_counts[content_info["contentForm"]]+=1;zones_count[zone]+=1
        inspected[content_info["readStanding"]]+=1
        match=[]
        for label in dense:
            prefix=label["sourcePrefix"]
            direct=label["directOnly"]
            if path.startswith(prefix) and (not direct or "/" not in path[len(prefix):]):
                match.append(label["proposedName"])
        if len(match)>1: ambiguity["DENSE_GROUP_OVERLAP"]+=1
        for name in match:dense_hits[name].append(path)
        observed={"path":path,"sourceIdentity":entry["mode"]+":"+entry["objectType"]+":"+entry["blobOid"],
                  "sourceZone":zone,"contentProbe":content_info,
                  "denseCandidateLabels":match,"functionalIdentity":"UNKNOWN",
                  "actualConsumers":"UNKNOWN","installedState":"UNKNOWN",
                  "lifecycleCurrentness":"SOURCECUT_ONLY","semanticProof":"NOT_EVALUATED"}
        path_rows.append(observed)
    # Source-level proposed rename labels are *data*, not a second resolver.
    # The existing affected_owners/source lookup remains the sole exact-cut
    # identity selector. These rows add observed *contents* at specific prefixes.
    scoped_summary=[]
    for alias in specific:
        prefix=alias["sourcePrefix"]
        members=[row for row in path_rows if row["path"].startswith(prefix)]
        contents=collections.Counter(row["contentProbe"]["contentForm"] for row in members)
        # A kind field is a syntactic self-description, not verification
        # of a live authority, producer, consumer or executable behavior.
        claimed=collections.Counter(
            str(kind) for row in members
            if isinstance((kind := row["contentProbe"].get("claimedFields",{}).get("kind")),str)
        )
        scoped_summary.append({
            "oldSourcePrefix":prefix,
            "proposedAgentDisplayName":alias["candidateName"],
            "priorSourceCutCount":alias["priorTrackedCount"],
            "observedCurrentCount":len(members),
            "sourceCutCountDelta":len(members)-alias["priorTrackedCount"],
            "observedFileContentForms":dict(sorted(contents.items())),
            "observedSelfDeclaredKinds":dict(sorted(claimed.items())),
            "agentNameStanding":"ADVISORY_LEXICAL_AND_SYNTAX_ONLY",
            "sourceIdentityStanding":"PHYSICAL_GIT_PREFIX_ONLY",
            "semanticStanding":"UNKNOWN",
            "consumerStanding":"UNKNOWN",
            "installedStanding":"UNKNOWN",
            "mayPhysicallyRename":False
        })
    # Independent peer's 12 exact Git blob + literal marker counterexamples
    # constrain naming errors; they do NOT prove actual runtime consumption.
    peer_counterexamples=seed["contentObservedNameCounterexamples"]
    if len(peer_counterexamples)!=12:
        raise ValueError("the bounded independent source counterexample set must have 12 entries")
    pathindex={row["path"]:row for row in rows}
    peer_summary=[]
    for witness in peer_counterexamples:
        original=witness["witnessPath"]
        entry=pathindex.get(original)
        prior_oid=witness["baselineWitnessGitBlob"]
        present_oid=entry["blobOid"] if entry is not None else None
        marker=witness["expectedLiteralContentMarker"].encode("utf8")
        blob=content.get(present_oid) if present_oid is not None else None
        status=("WITNESS_NOT_IN_GIT_CUT" if entry is None else
                "WITNESS_BLOB_CHANGED" if present_oid!=prior_oid else
                "WITNESS_CONTENT_NOT_READ" if blob is None else
                "WITNESS_GIT_BLOB_AND_LITERAL_MATCH" if marker in blob else
                "WITNESS_MARKER_MISSING")
        prefix=witness["sourcePrefix"]
        source_count=sum(x["path"].startswith(prefix) for x in rows)
        other=[x["proposedName"] for x in specific if
               x["sourcePrefix"]==prefix]
        peer_summary.append({
           "sourcePrefix":prefix,
           "displayCandidate":witness["proposedDisplayName"],
           "otherDisplayCandidatesSamePrefix":sorted(other),
           "semanticFalseFriend":witness["misleadingLegacyConflation"],
           "witnessSourcePath":original,
           "witnessSourceIdentity":None if entry is None else
                                   entry["mode"]+":"+entry["blobOid"],
           "baselineWitnessBlob":prior_oid,
           "witnessStatus":status,
           "priorMemberCount":witness["priorPrefixFileCount"],
           "currentMemberCount":source_count,
           "consumerStanding":"UNKNOWN",
           "formalSemanticStanding":"NOT_PROVED",
           "physicalRenameAllowed":False,
        })
    dense_summary=[]
    for label in dense:
        name=label["proposedName"];paths=sorted(dense_hits[name])
        if not paths: raise ValueError("prior dense label became empty: "+name)
        byform=collections.Counter(r["contentProbe"]["contentForm"] for r in path_rows if r["path"] in set(paths))
        dense_summary.append({"cellRef":label["sourceCell"],"label":name,
                              "oldCount":label["baselineCount"],"newCount":len(paths),
                              "sourceCutDrift":len(paths)-label["baselineCount"],
                              "observedForms":dict(sorted(byform.items())),
                              "scopeStanding":"DENSE_LABEL_CONTENT_SYNTAX_REFINEMENT_ONLY"})
    payload={
      "kind":"ordivon.phase1.source-content-facets-r4",
      "sourceCut":cut,"sourceTree":git("rev-parse",cut+"^{tree}",repo=repo).decode().strip(),
      "baselinePeerSourceCut":seed["baseGitSourceCut"],
      "r2PeerObservationGitCut":seed["priorR2ObservationGitCut"],
      "r3PeerObservationGitCut":seed["priorR3ObservationGitCut"],
      "namingSeedFile":SEED_PATH,
      "namingSeedBlob":next((r["blobOid"] for r in rows if r["path"]==SEED_PATH),None),
      "truthRole":"ADVISORY_REPRODUCIBLE_SOURCE_CONTENT_NOT_SEMANTIC_OWNER_OR_PROOF",
      "summary":{
       "tracked":len(rows),"accountedFor":len(path_rows),"zones":len(zones),
       "registeredSourceAreas":len([z for z in zones if z["sourceRef"].startswith("zone/")]),
       "allZones":dict(sorted(zones_count.items())),"contentForms":dict(sorted(content_counts.items())),
       "readStandings":dict(sorted(inspected.items())),"maxBlobSize":maxsize,
       "dense60":dense_summary,
       "specific26":scoped_summary,
       "contentObservedCounterexamples12":peer_summary,
       "scopedNameSyntaxOnly":True,
       "denseGroupOverlap":dict(ambiguity),
       "r2RecursiveCellClaimsFromPriorSurvey":718,
       "nestedCellsAreNotDisjoint":True,
       "allFunctionalIdentitiesQualified":0,
       "sourcePathMoves":0},
      "paths":path_rows
    }
    payload["sourcePathSetHash"]="sha256:"+hashlib.sha256(
        "\n".join(x["path"]+" "+x["sourceIdentity"] for x in path_rows).encode("utf8","surrogateescape")
    ).hexdigest()
    if len(path_rows)!=len({x["path"] for x in path_rows}):
        raise AssertionError("nonunique source path")
    return payload


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-cut",required=True)
    p.add_argument("--summary",action="store_true")
    p.add_argument("--output")
    p.add_argument("--repo",type=Path,default=Path.cwd())
    args=p.parse_args()
    doc=compile_projection(args.repo, args.source_cut)
    if args.summary:doc={k:v for k,v in doc.items() if k!="paths"}
    body=json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if args.output:Path(args.output).write_text(body,encoding="utf8")
    else:print(body,end="")


if __name__=="__main__":main()
