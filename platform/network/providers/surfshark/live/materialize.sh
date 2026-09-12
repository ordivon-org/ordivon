#!/usr/bin/env bash
set -euo pipefail
LOCK=${LOCK:-providers/surfshark/external/gluetun.lock}
NETNS=${NETNS:-}
value(){ awk -F= -v k="$1" '$1==k{print substr($0,index($0,"=")+1);exit}' "$LOCK"; }
REPO=$(value repository); TAG=$(value tag); REVISION=$(value revision); CREATED=$(value created); EXPECTED_SHA=$(value sha256); INSTALL=$(value install)
for v in "$REPO" "$TAG" "$REVISION" "$CREATED" "$EXPECTED_SHA" "$INSTALL"; do [ -n "$v" ]; done
if [ -n "$NETNS" ]; then ip netns list | awk '{print $1}' | grep -qx "$NETNS"; fi
run_net(){ if [ -n "$NETNS" ]; then ip netns exec "$NETNS" "$@"; else "$@"; fi; }
TMP=$(mktemp -d /tmp/network-v2-gluetun-materialize.XXXXXX)
cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT
/usr/bin/git init -q "$TMP/src"
/usr/bin/git -C "$TMP/src" remote add origin "$REPO"
run_net /usr/bin/git -C "$TMP/src" fetch --quiet --depth 1 origin "$REVISION"
/usr/bin/git -C "$TMP/src" checkout --quiet --detach FETCH_HEAD
[ "$(/usr/bin/git -C "$TMP/src" rev-parse HEAD)" = "$REVISION" ]
run_net /usr/bin/go -C "$TMP/src" build -trimpath -buildvcs=false \
  -ldflags="-s -w -X 'main.version=$TAG' -X 'main.created=$CREATED' -X 'main.commit=$REVISION'" \
  -o "$TMP/gluetun" cmd/gluetun/main.go
ACTUAL=$(sha256sum "$TMP/gluetun" | awk '{print $1}')
[ "$ACTUAL" = "$EXPECTED_SHA" ]
install -D -m 0755 "$TMP/gluetun" "$INSTALL"
[ "$(sha256sum "$INSTALL" | awk '{print $1}')" = "$EXPECTED_SHA" ]
printf 'repository=%s\ntag=%s\nrevision=%s\nsha256=%s\nnetworkNamespace=%s\n' "$REPO" "$TAG" "$REVISION" "$ACTUAL" "${NETNS:-ambient}"
echo gluetun-live-updater-materialized=PASS
