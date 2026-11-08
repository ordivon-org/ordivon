"""Bounded, offline human-observation CSV kit for the actual Godot Room Encounter.

No gameplay telemetry, network access, invented participants, or subjective
conclusions. Only a human observer may complete empty observation fields.
"""
import argparse
import csv
import hashlib
import os
import re
import secrets
import statistics
from collections import Counter
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
TEMPLATE = GAME / "docs" / "room-encounter-playtest-template.csv"
PLAN_COLUMNS = ("session_code", "pair_code", "period", "condition", "platform", "build_sha256")
CONDITIONS = ("Classic", "Trial")
PLATFORMS = ("windows", "linux")
OUTCOMES = ("win", "loss", "quit", "unknown")
FORECAST = ("understood", "misunderstood", "unknown", "not_applicable")
BOOLEAN = ("yes", "no", "unknown", "not_applicable")
CONTROL_NAMES = frozenset(("A", "G", "N", "R", "T", "C", "S", "L", "unlock"))
REQUIRED = ("session_seconds", "outcome", "controls_discovered",
            "forecast_interpretation", "parry_decision_observed",
            "keyboard_focus_issue", "blocked_or_clipped_content")


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path, expected):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream, strict=True)
        if tuple(reader.fieldnames or ()) != tuple(expected):
            raise ValueError(f"{path}: unexpected CSV schema")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"{path}: malformed CSV row")
    return rows


def create_plan(build, platform, pairs, output):
    if platform not in PLATFORMS or pairs < 1 or pairs > 100:
        raise ValueError("platform must be windows/linux, pairs must be 1..100")
    artifact = Path(build)
    if not artifact.is_file() or artifact.stat().st_size == 0:
        raise ValueError("build must be an existing nonempty release artifact")
    digest = sha256_file(artifact)
    dest = Path(output)
    dest.mkdir(mode=0o700, parents=True, exist_ok=False)
    if os.name == "posix":
        dest.chmod(0o700)
    # Balanced within-subject crossover, AB/BA; order is randomized with
    # SystemRandom, not inferred from a participant's name or characteristics.
    orders = [("Classic", "Trial") if i % 2 == 0
              else ("Trial", "Classic") for i in range(pairs)]
    secrets.SystemRandom().shuffle(orders)
    plan = []
    for condition_order in orders:
        pair_code = "P-" + secrets.token_hex(6)
        for period, condition in enumerate(condition_order, 1):
            plan.append(dict(session_code="S-" + secrets.token_hex(8),
                             pair_code=pair_code, period=str(period),
                             condition=condition, platform=platform,
                             build_sha256=digest))
    columns = read_template_columns()
    if "consent_to_notes" not in columns:
        raise ValueError("observation template lacks explicit consent")
    with (dest / "plan.csv").open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PLAN_COLUMNS)
        writer.writeheader()
        writer.writerows(plan)
    with (dest / "observations.csv").open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in plan:
            writer.writerow({key: row.get(key, "") for key in columns})
    if os.name == "posix":
        (dest / "plan.csv").chmod(0o600)
        (dest / "observations.csv").chmod(0o600)
    return dest, digest, len(plan)


def read_template_columns():
    with TEMPLATE.open("r", encoding="utf-8", newline="") as f:
        return tuple(next(csv.reader(f)))


def inspect(plan_file, observation_file, build=None):
    plan = read_rows(plan_file, PLAN_COLUMNS)
    obs_columns = read_template_columns()
    observations = read_rows(observation_file, obs_columns)
    if not plan:
        raise ValueError("empty plan: cannot claim a human study")
    plan_index = {}
    pairs = {}
    for row in plan:
        code, pair = row["session_code"], row["pair_code"]
        if (re.fullmatch(r"S-[0-9a-f]{16}", code) is None or
                re.fullmatch(r"P-[0-9a-f]{12}", pair) is None or
                code in plan_index):
            raise ValueError("missing/duplicate/invalid anonymous plan codes")
        if row["period"] not in ("1", "2") or row["condition"] not in CONDITIONS:
            raise ValueError("invalid planned order or condition")
        if row["platform"] not in PLATFORMS or len(row["build_sha256"]) != 64:
            raise ValueError("invalid build provenance")
        try:
            int(row["build_sha256"], 16)
        except ValueError as err:
            raise ValueError("invalid SHA-256") from err
        plan_index[code] = row
        pairs.setdefault(pair, []).append(row)
    if any(len(v) != 2 or {x["period"] for x in v} != {"1", "2"}
           or {x["condition"] for x in v} != set(CONDITIONS) for v in pairs.values()):
        raise ValueError("study must have complete Classic/Trial AB or BA pairs")
    ab = sum(next(r["condition"] for r in group if r["period"] == "1") == "Classic"
             for group in pairs.values())
    if abs(2 * ab - len(pairs)) > 1:
        raise ValueError("AB/BA study allocation is not counterbalanced")
    if len({row["build_sha256"] for row in plan}) != 1:
        raise ValueError("mixed release builds in study")
    if len({row["platform"] for row in plan}) != 1:
        raise ValueError("mixed platforms in study")
    if build and sha256_file(build) != plan[0]["build_sha256"]:
        raise ValueError("local release digest does not match study plan")
    results = []
    visited = set()
    declines = 0
    for row in observations:
        code = row["session_code"]
        if code in visited or code not in plan_index:
            raise ValueError("unplanned or duplicate observation session")
        visited.add(code)
        expected = plan_index[code]
        for field in ("condition", "platform", "build_sha256"):
            if row[field] != expected[field]:
                raise ValueError(f"{code}: mismatch in planned {field}")
        consent = row["consent_to_notes"].strip().lower()
        if consent not in ("", "yes", "no"):
            raise ValueError(f"{code}: consent must be yes/no or blank")
        payload = [row[key].strip() for key in REQUIRED + ("post_session_feedback", "observer_uncertainty")]
        for field in ("post_session_feedback", "observer_uncertainty"):
            note = row[field].strip()
            if len(note) > 500 or "\n" in note or "\r" in note or note.startswith(("=", "+", "-", "@")):
                raise ValueError(f"{code}: unsafe or excessively long note")
        if consent == "no":
            if any(payload):
                raise ValueError(f"{code}: declined observation must not retain data")
            declines += 1
            continue
        if consent == "":
            if any(payload):
                raise ValueError(f"{code}: observation data without consent")
            continue
        for field, values in (("outcome", OUTCOMES),
                              ("forecast_interpretation", FORECAST),
                              ("parry_decision_observed", BOOLEAN),
                              ("keyboard_focus_issue", BOOLEAN),
                              ("blocked_or_clipped_content", BOOLEAN)):
            if row[field] and row[field] not in values:
                raise ValueError(f"{code}: unsupported {field}; use unknown, not false")
        controls = row["controls_discovered"]
        if controls and controls != "unknown":
            if not set(controls.split("|")) <= CONTROL_NAMES:
                raise ValueError(f"{code}: unsupported control observation")
        if row["session_seconds"]:
            if not row["session_seconds"].isdigit() or not (1 <= int(row["session_seconds"]) <= 21600):
                raise ValueError(f"{code}: invalid elapsed seconds")
        if all(row[k].strip() for k in REQUIRED):
            results.append(row)
    return dict(planned=len(plan), paired=len(pairs), complete=results,
                declined=declines, pending=len(plan) - len(results) - declines)


def report(data):
    lines = ["# Room Encounter — observer-entered exploratory evidence",
             "", "Evidence scope: manually entered, consented Human observations. "
             "Neither participant authenticity nor unobserved motivations are machine-verifiable.",
             "",
             f"Planned sessions: {data['planned']} ({data['paired']} anonymous AB/BA pairs). "
             f"Completed consenting observations: {len(data['complete'])}. "
             f"Declined: {data['declined']}. Pending/missing: {data['pending']}.",
             ""]
    if not data["complete"]:
        lines.append("**Human evidence: UNKNOWN.** No completed consenting player observation exists.")
        lines.append("No comprehension, engagement, conversion or duration claim is supported.")
        return "\n".join(lines) + "\n"
    for condition in CONDITIONS:
        rows = [r for r in data["complete"] if r["condition"] == condition]
        n = len(rows)
        lines.append(f"## {condition} (n={n})")
        if not n:
            lines.append("No observations; all outcome measures UNKNOWN.")
            continue
        outcomes = Counter(r["outcome"] for r in rows)
        comprehension = Counter(r["forecast_interpretation"] for r in rows)
        parry = Counter(r["parry_decision_observed"] for r in rows)
        seconds = [int(r["session_seconds"]) for r in rows]
        lines.append(f"Outcomes: " + ", ".join(f"{k}={outcomes[k]}/{n}" for k in OUTCOMES))
        lines.append(f"Forecast interpretation: " + ", ".join(
            f"{k}={comprehension[k]}/{n}" for k in FORECAST))
        lines.append(f"Guard decision observed: " + ", ".join(
            f"{k}={parry[k]}/{n}" for k in BOOLEAN))
        lines.append(f"Recorded duration median: {statistics.median(seconds):g}s; "
                     f"range {min(seconds)}–{max(seconds)}s. "
                     "Duration is not an enjoyment score.")
        lines.append("")
    lines.append("This is exploratory description, not a causal estimate or a statistical "
                 "test. AB/BA assignment controls planned order only; incomplete pairs, "
                 "learning effects, attrition and observer judgments limit interpretation. "
                 "UNKNOWN and not_applicable are never counted as NO.")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("prepare", help="make anonymous balanced AB/BA rows with no human measurements")
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--platform", choices=PLATFORMS, required=True)
    p.add_argument("--pairs", type=int, default=4)
    p.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("report", help="validate and describe only consented observer-entered rows")
    r.add_argument("--plan", type=Path, required=True)
    r.add_argument("--observations", type=Path, required=True)
    r.add_argument("--build", type=Path)
    r.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.action == "prepare":
        dest, digest, count = create_plan(args.build, args.platform, args.pairs, args.out)
        print(f"GAME_HUMAN_STUDY_PLAN_READY sessions={count} sha256={digest} "
              f"human_evidence=UNKNOWN private_dir={dest}")
    else:
        data = inspect(args.plan, args.observations, args.build)
        text = report(data)
        if args.out:
            with args.out.open("x", encoding="utf-8") as f:
                f.write(text)
        else:
            print(text, end="")


if __name__ == "__main__":
    main()
