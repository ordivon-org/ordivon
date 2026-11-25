#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/ordivon-media-timedtext-smoke.XXXXXX")
trap 'rm -rf "$work"' EXIT

ttconv="$root/processing/bin/ttconv-pinned.sh"
probe="$root/processing/bin/probe-timed-text.sh"

cat > "$work/good.vtt" <<'EOF'
WEBVTT

one
00:00:00.000 --> 00:00:02.000
First cue.

two
00:00:02.000 --> 00:00:05.000
Second cue.
EOF

"$ttconv" convert -i "$work/good.vtt" -o "$work/good.ttml" --otype TTML \
  --config '{"general":{"progress_bar":false,"log_level":"WARN","document_lang":"en"},"imsc_writer":{"time_format":"clock_time"}}'

cat > "$work/profile.json" <<'EOF'
{
  "schemaVersion":1,
  "kind":"ordivon.media.v2.timed-text-profile",
  "id":"timedtext-smoke-good",
  "format":"ttml",
  "expectedLanguage":"en",
  "expectedCueCount":2,
  "maxEndSeconds":5.0,
  "requirePositiveDurations":true,
  "requireNonemptyPackets":true
}
EOF

bash "$probe" "$work/good.ttml" "$work/profile.json" "$work/good-evidence" >/dev/null
jq -e '.mechanicalDelivery.ok == true and .normalizedFacts.cueCount == 2 and .normalizedFacts.maxEndSeconds == 5' "$work/good-evidence/evidence.json" >/dev/null

"$ttconv" convert -i "$work/good.vtt" -o "$work/direct.srt" --otype SRT --config '{"general":{"progress_bar":false,"log_level":"WARN"}}'
"$ttconv" convert -i "$work/good.ttml" -o "$work/via-ttml.srt" --otype SRT --config '{"general":{"progress_bar":false,"log_level":"WARN"}}'
diff -u "$work/direct.srt" "$work/via-ttml.srt"

cat > "$work/bad-interval.vtt" <<'EOF'
WEBVTT

bad
00:00:10.000 --> 00:00:05.000
Impossible interval.
EOF
jq '.id="timedtext-smoke-negative-interval" | .format="vtt" | .expectedLanguage=null | .expectedCueCount=1 | .maxEndSeconds=20' "$work/profile.json" > "$work/bad-interval-profile.json"
if bash "$probe" "$work/bad-interval.vtt" "$work/bad-interval-profile.json" "$work/bad-interval-evidence" >/dev/null 2>"$work/bad-interval.stderr"; then
  echo "negative-duration timed text unexpectedly passed" >&2
  exit 1
fi
grep -q 'FAIL timedText.positiveDurations' "$work/bad-interval.stderr"

jq '.id="timedtext-smoke-negative-overflow" | .maxEndSeconds=4.0' "$work/profile.json" > "$work/overflow-profile.json"
if bash "$probe" "$work/good.ttml" "$work/overflow-profile.json" "$work/overflow-evidence" >/dev/null 2>"$work/overflow.stderr"; then
  echo "overflow timed text unexpectedly passed" >&2
  exit 1
fi
grep -q 'FAIL timedText.maxEndSeconds' "$work/overflow.stderr"

printf '%s\n' '<tt><body><div></body></tt>' > "$work/malformed.ttml"
if bash "$probe" "$work/malformed.ttml" "$work/profile.json" "$work/malformed-evidence" >/dev/null 2>/dev/null; then
  echo "malformed TTML unexpectedly passed" >&2
  exit 1
fi

# Explicit false is a policy choice, not an absent value. Preserve the measured
# negative interval while making the corresponding check optional.
jq '.requirePositiveDurations=false | .requireNonemptyPackets=false' "$work/bad-interval-profile.json" > "$work/optional-profile.json"
bash "$probe" "$work/bad-interval.vtt" "$work/optional-profile.json" "$work/optional-evidence" >/dev/null
jq -e '.ok and any(.checks[]; .name=="timedText.positiveDurations" and .required==false and .actual==false and .ok==true) and any(.checks[]; .name=="timedText.nonemptyPackets" and .required==false and .ok==true)' "$work/optional-evidence/assertions.json" >/dev/null

# Omitting the field preserves the strict default.
jq 'del(.requirePositiveDurations)' "$work/bad-interval-profile.json" > "$work/default-profile.json"
if bash "$probe" "$work/bad-interval.vtt" "$work/default-profile.json" "$work/default-evidence" >/dev/null 2>"$work/default.stderr"; then
  echo "absent duration requirement unexpectedly disabled strict default" >&2
  exit 1
fi
grep -q 'FAIL timedText.positiveDurations' "$work/default.stderr"

# Non-boolean policy values are invalid, not silently coerced.
for invalid in null '"false"' 0; do
  jq --argjson invalid "$invalid" '.requirePositiveDurations=$invalid' "$work/profile.json" > "$work/invalid-profile.json"
  dest="$work/invalid-policy-$invalid"
  if bash "$probe" "$work/good.ttml" "$work/invalid-profile.json" "$dest" >/dev/null 2>"$work/invalid.stderr"; then
    echo "invalid boolean profile unexpectedly accepted" >&2
    exit 1
  fi
  grep -q 'invalid timed-text profile' "$work/invalid.stderr"
  test ! -e "$dest/evidence.json"
done

echo 'processing timed-text smoke: PASS (round-trip preserved; negative duration, overflow, malformed XML rejected)'
