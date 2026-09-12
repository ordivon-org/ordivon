#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "artifact-delivery/openxml-external-evidence-r1.json"
DEFAULT_VALIDATOR = Path(
    "/root/.local/share/ordivon-workstation/artifact-openxml-v1/current/bin/validate-openxml"
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def fixed_zip(path: Path, entries: list[tuple[str, bytes]]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in entries:
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def docx(path: Path, *, mc_missing_requires: bool) -> None:
    content_types = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'''
    rels = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
    if mc_missing_requires:
        body = b'''<w:p><w:r><mc:AlternateContent><mc:Choice><w:t>bad</w:t></mc:Choice></mc:AlternateContent></w:r></w:p>'''
    else:
        body = b'''<w:p><w:r><w:t>Artifact external evidence control</w:t></w:r></w:p>'''
    prefix = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o15="http://o15.com"><w:body>'''
    suffix = b'''</w:body></w:document>'''
    fixed_zip(
        path,
        [
            ("[Content_Types].xml", content_types),
            ("_rels/.rels", rels),
            ("word/document.xml", prefix + body + suffix),
        ],
    )


def xlsx(path: Path, content: str) -> None:
    content_types = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'''
    rels = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'''
    workbook = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    workbook_rels = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'''
    worksheet = (
        '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/><autoFilter ref="A1:A3"><filterColumn colId="0"><filters>'''
        + content
        + "</filters></filterColumn></autoFilter></worksheet>"
    ).encode()
    fixed_zip(
        path,
        [
            ("[Content_Types].xml", content_types),
            ("_rels/.rels", rels),
            ("xl/workbook.xml", workbook),
            ("xl/_rels/workbook.xml.rels", workbook_rels),
            ("xl/worksheets/sheet1.xml", worksheet),
        ],
    )


def make_fixture(kind: str, path: Path) -> None:
    if kind == "docx-good":
        docx(path, mc_missing_requires=False)
        return
    if kind == "docx-mc-missing-requires":
        docx(path, mc_missing_requires=True)
        return
    content = {
        "xlsx-filter-only": '<filter val="Cookies"/>',
        "xlsx-date-only": '<dateGroupItem year="2024" dateTimeGrouping="year"/>',
        "xlsx-filter-date": '<filter val="Cookies"/><dateGroupItem year="2024" dateTimeGrouping="year"/>',
        "xlsx-date-filter": '<dateGroupItem year="2024" dateTimeGrouping="year"/><filter val="Cookies"/>',
    }.get(kind)
    if content is None:
        raise RuntimeError(f"unknown external-evidence fixture {kind}")
    xlsx(path, content)


def run(validator: Path) -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text())
    if manifest.get("schemaVersion") != 1 or manifest.get("methodId") != "artifact.openxml.conformance.v1":
        raise RuntimeError("external evidence manifest invalid")
    if not validator.is_file():
        raise RuntimeError(f"stable validator absent: {validator}")

    generation = validator.resolve().parents[1]
    binding = json.loads((generation / "binding.json").read_text())
    if binding.get("methodId") != manifest["methodId"]:
        raise RuntimeError("validator generation binding mismatch")

    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="artifact-openxml-ext-") as directory:
        root = Path(directory)
        for case in manifest["cases"]:
            extension = ".xlsx" if case["fixture"].startswith("xlsx-") else ".docx"
            path = root / f'{case["caseId"]}{extension}'
            make_fixture(case["fixture"], path)
            fixture_sha = sha(path)
            frozen = case.get("fixtureSha256")
            digest_ok = frozen is None or fixture_sha == frozen

            completed = subprocess.run(
                [str(validator), str(path)],
                text=True,
                capture_output=True,
                check=False,
                timeout=60,
            )
            try:
                payload = json.loads(completed.stdout)
            except Exception as error:
                raise RuntimeError(
                    f'{case["caseId"]} validator output is not JSON: {error}'
                ) from error
            ids = [entry.get("id") for entry in payload.get("validationErrors", [])]
            behavior_ok = payload.get("status") == case["expectedStatus"] and all(
                expected in ids for expected in case.get("expectedErrorIds", [])
            )
            behavior_ok = behavior_ok and completed.returncode == (
                0 if case["expectedStatus"] == "PASS" else 1
            )
            results.append(
                {
                    "caseId": case["caseId"],
                    "sourceId": case["sourceId"],
                    "fixture": case["fixture"],
                    "fixtureSha256": fixture_sha,
                    "fixtureDigestMatchesFreeze": digest_ok,
                    "validatorStatus": payload.get("status"),
                    "validatorReturnCode": completed.returncode,
                    "validationErrorIds": ids,
                    "evidenceDisposition": case["evidenceDisposition"],
                    "resultAuthority": case.get(
                        "resultAuthority", "METHOD_RULE_EVIDENCE"
                    ),
                    "behaviorMatchesExternalExpectation": behavior_ok,
                    "pass": digest_ok and behavior_ok,
                }
            )

    corpus_material = [
        {
            key: case[key]
            for key in (
                "caseId",
                "fixtureSha256",
                "validatorStatus",
                "validationErrorIds",
                "evidenceDisposition",
                "resultAuthority",
            )
        }
        for case in results
    ]
    corpus_result_digest = "sha256:" + hashlib.sha256(canonical(corpus_material)).hexdigest()
    expected_corpus_digest = manifest["graduationPolicy"].get("expectedCorpusResultDigest")
    corpus_digest_matches_freeze = (
        expected_corpus_digest is None or corpus_result_digest == expected_corpus_digest
    )
    aggregate = all(case["pass"] for case in results) and corpus_digest_matches_freeze
    return {
        "schemaVersion": 1,
        "kind": "artifact-openxml-external-evidence-result",
        "corpusId": manifest["corpusId"],
        "methodId": manifest["methodId"],
        "manifestSha256": "sha256:" + sha(MANIFEST),
        "validatorGenerationId": binding["generationId"],
        "validatorPackageVersion": "3.5.1",
        "cases": results,
        "corpusResultDigest": corpus_result_digest,
        "expectedCorpusResultDigest": expected_corpus_digest,
        "corpusDigestMatchesFreeze": corpus_digest_matches_freeze,
        "standing": (
            "PASS_BOUNDED_EXTERNAL_EVIDENCE"
            if aggregate
            else "FAIL_EXTERNAL_EVIDENCE"
        ),
        "ivvStanding": "NOT_CLAIMED",
        "methodPromotion": (
            "GRADUATED_BOUNDED_STRUCTURAL_GATE" if aggregate else "HOLD"
        ),
        "nonClaims": [
            "external source/corpus reproduction is not organizationally independent IV&V",
            "known upstream false-positive reproduction does not prove the subject document invalid",
            "method graduation does not promote overall Artifact E2E or visual/Office/accessibility/business acceptance",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--validator",
        default=os.environ.get("ARTIFACT_OPENXML_VALIDATOR", str(DEFAULT_VALIDATOR)),
    )
    args = parser.parse_args()
    result = run(Path(args.validator))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["standing"] == "PASS_BOUNDED_EXTERNAL_EVIDENCE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
