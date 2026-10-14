#!/usr/bin/env bash
set -euo pipefail

network_root=$(cd "$(dirname "$0")/../../.." && pwd)
lock="$network_root/capabilities/gluetun/external/gluetun.lock"

repo=$(awk -F= '$1=="repo"{print substr($0,index($0,"=")+1)}' "$lock")
version=$(awk -F= '$1=="version"{print substr($0,index($0,"=")+1)}' "$lock")
revision=$(awk -F= '$1=="revision"{print substr($0,index($0,"=")+1)}' "$lock")

test "$repo" = "https://github.com/passteque/gluetun.git"
test "$version" = "v3.41.3"
test "$revision" = "3d1e20c5551e9cae1f9d938dc7b7214a6987f27e"

tmp=$(mktemp -d /tmp/network-v2-gluetun-source.XXXXXX)
trap 'rm -rf "$tmp"' EXIT

(
  cd "$tmp"
  git init -q
  git remote add origin "$repo"
  git fetch --quiet --depth 1 origin "refs/tags/$version"
  git checkout --quiet --detach FETCH_HEAD
  test "$(git rev-parse HEAD)" = "$revision"
)

test -f "$tmp/Dockerfile"
test -f "$tmp/go.mod"
test -d "$tmp/internal"

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.gluetun-source-qualification","standing":"PASS","version":"%s","revision":"%s","tagBound":true,"productionEffect":false}\n' "$version" "$revision"
