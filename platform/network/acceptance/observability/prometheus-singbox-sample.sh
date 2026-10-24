#!/usr/bin/env bash
set -euo pipefail

# Read exactly one instant-vector Prometheus response from stdin. A string
# search cannot establish sample identity or freshness. The caller chooses
# the earliest acceptable sample time (milliseconds since Unix epoch).
if [ "$#" -ne 1 ] || ! [[ "$1" =~ ^[0-9]+$ ]]; then
  echo 'expected minimum Prometheus observation timestamp in milliseconds' >&2
  exit 2
fi

jq -s -e --argjson minimum_ms "$1" --argjson current_ms "$(date +%s%3N)" '
  length == 1 and
  .[0].status == "success" and
  .[0].data.resultType == "vector" and
  any(.[0].data.result[]?;
    .metric.__name__ == "probe_success" and
    .metric.job == "blackbox-singbox" and
    .metric.instance == "127.0.0.1:28080" and
    (.value | type == "array" and length == 2) and
    (.value[0] | type == "number") and
    (.value[0] * 1000 >= $minimum_ms) and
    (.value[0] * 1000 <= $current_ms + 2000) and
    .value[1] == "1"
  )
' >/dev/null
