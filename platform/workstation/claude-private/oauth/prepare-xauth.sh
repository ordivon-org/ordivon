#!/usr/bin/env bash
set -euo pipefail

AUTH=/run/claude-private-oauth/xauth
DISPLAY_ID=:90
cookie=$(/usr/bin/mcookie)
[[ $cookie =~ ^[0-9a-fA-F]{32}$ ]]
: >"$AUTH"
chmod 0600 "$AUTH"
/usr/bin/xauth -f "$AUTH" add "$DISPLAY_ID" . "$cookie"
