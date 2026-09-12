#!/usr/bin/env bash
set -euo pipefail
TOPO=${TOPO:-reference/linux/containerlab/reference.clab.yml}
NAME=network-e2e-reference
cleanup(){ containerlab destroy -t "$TOPO" --cleanup >/dev/null 2>&1 || true; }
trap cleanup EXIT
cleanup
containerlab deploy -t "$TOPO" --reconfigure
N1=clab-$NAME-n1; N2=clab-$NAME-n2
docker inspect "$N1" >/dev/null; docker inspect "$N2" >/dev/null
docker exec "$N1" ip addr add 10.253.20.1/30 dev eth1
docker exec "$N2" ip addr add 10.253.20.2/30 dev eth1
docker exec "$N1" ip link set eth1 up; docker exec "$N2" ip link set eth1 up
docker exec "$N1" ping -c 2 -W 2 10.253.20.2 >/dev/null
echo reference-containerlab=PASS
