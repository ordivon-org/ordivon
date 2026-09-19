#!/usr/bin/env python
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from distribution_preflight import PreflightError, run_preflight

ROOT = Path(__file__).resolve().parents[1]
BASE_PROFILE = ROOT / "profiles/steam-linux-directory-r1.json"


def make_candidate(root: Path, *, obsolete: bool, label: str) -> None:
    root.mkdir(parents=True)
    shutil.copy2("/usr/bin/printf", root / "app")
    (root / "common.txt").write_text(label + "\n")
    if obsolete:
        (root / "obsolete.txt").write_text("remove-on-update\n")
    else:
        (root / "new.txt").write_text("added-on-update\n")


def profile_for_test(path: Path) -> None:
    value = json.loads(BASE_PROFILE.read_text())
    value["entrypoint"] = "app"
    value["launch"] = {"args": ["ORDIVON_DISTRIBUTION_PREFLIGHT_OK\\n"], "successMarker": "ORDIVON_DISTRIBUTION_PREFLIGHT_OK"}
    path.write_text(json.dumps(value, indent=2) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ordivon-distribution-preflight-test-") as raw:
        root = Path(raw)
        a = root / "a"
        b = root / "b"
        make_candidate(a, obsolete=True, label="A")
        make_candidate(b, obsolete=False, label="B")
        profile = root / "profile.json"
        profile_for_test(profile)
        receipt = run_preflight(
            profile_path=profile,
            candidate_a=a,
            candidate_b=b,
            work_root=root / "work",
            vdf_dir=root / "steam",
            rclone=Path("/usr/bin/rclone"),
            readelf=Path("/usr/bin/readelf"),
            ldd=Path("/usr/bin/ldd"),
            candidate_a_ref="test:A",
            candidate_b_ref="test:B",
        )
        assert receipt["status"] == "PASS"
        assert receipt["lifecycle"]["updateAToB"]["staleFileDetection"] == "PASS_BY_EXACT_TREE_EQUALITY"
        assert receipt["steam"]["realSteamPipePreview"] == "NOT_PERFORMED"
        assert "__STEAM_APP_ID__" in (root / "steam/app_build.template.vdf").read_text()
        assert "__STEAM_DEPOT_ID__" in (root / "steam/depot_build.template.vdf").read_text()
        assert not (root / "work/install/obsolete.txt").exists()
        assert (root / "work/install/new.txt").is_file()

        (b / ".env").write_text("SHOULD_NOT_SHIP=1\n")
        try:
            run_preflight(
                profile_path=profile,
                candidate_a=a,
                candidate_b=b,
                work_root=root / "negative",
                vdf_dir=root / "negative-steam",
                rclone=Path("/usr/bin/rclone"),
                readelf=Path("/usr/bin/readelf"),
                ldd=Path("/usr/bin/ldd"),
                candidate_a_ref="test:A",
                candidate_b_ref="test:B-leak",
            )
        except PreflightError as error:
            assert "forbidden release paths" in str(error)
        else:
            raise AssertionError("forbidden .env candidate was not rejected")

    print("PASS Distribution local preflight lifecycle + Steam static-template boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
