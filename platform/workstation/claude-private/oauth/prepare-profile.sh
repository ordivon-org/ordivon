#!/usr/bin/env bash
set -euo pipefail

root=/var/lib/claude-private-oauth-browser/profile/Default
prefs=$root/Preferences
mkdir -p "$root"
if [[ ! -s "$prefs" ]]; then
  cat >"$prefs" <<'JSON'
{
  "intl": {"accept_languages": "en-US,en"},
  "profile": {
    "default_content_setting_values": {
      "geolocation": 2,
      "media_stream_camera": 2,
      "media_stream_mic": 2,
      "notifications": 2
    }
  }
}
JSON
fi
chmod 0600 "$prefs"
