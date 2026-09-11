#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
envelope="evidence/r2-github-public-read-envelope.json"
source="evidence/r2-github-public-read-source.json"
source_ref="$(jq -r '.providerObservation.sourceRef' "$envelope")"
job_id="$(jq -r '.runtimeJobId' "$source")"
artifact_id="$(jq -r '.runtimeArtifactId' "$source")"
digest="$(jq -r '.runtimeArtifactDigest' "$source")"
expected="runtime-artifact:${job_id}/${artifact_id}@${digest}"
[[ "$source_ref" == "$expected" ]] || { echo 'FAIL positive-control source binding mismatch' >&2; exit 1; }
normalized="$(mktemp)"
trap 'rm -f "$normalized"' EXIT
uv run python scripts/admission.py normalize "$envelope" --now 2026-09-11T11:30:00Z > "$normalized"
action="$(opa eval --format raw --data policy/distribution.rego --input "$normalized" 'data.ordivon.distribution.decision.action')"
[[ "$action" == "preflight_ready" ]] || { echo "FAIL github positive control action=$action" >&2; exit 1; }
printf 'PASS GitHub provider-native historical read positive control -> %s\n' "$action"
