#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_BIN=${CLAUDE_SOURCE_BIN:-/root/.local/share/claude/versions/2.1.274}
EXPECTED_SHA256=15e2d05148f801b5774032faad87e624ecd172e9903288bda448b892eb58fa07
EXPECTED_VERSION='2.1.274 (Claude Code)'
DEST=/opt/claude-private/versions/2.1.274/claude
CFT_SOURCE=/root/.cache/ms-playwright/chromium-1243
CFT_DEST=/opt/claude-private/cft
CFT_SHA256=8c599d43aec53f2460a31ae2f4af6bd863f8258b34ff519564bc5d4726bfaa1e
WEBSOCKIFY=/opt/ordivon/external/websockify/0.13.0/bin/websockify
WEBSOCKIFY_SHA256=022c85f315e4df97487779c85a21dd0a162ebb1c1e09f75d3445a8583e4c1a26

[[ -x "$SOURCE_BIN" ]]
[[ "$(sha256sum "$SOURCE_BIN" | awk '{print $1}')" == "$EXPECTED_SHA256" ]]
[[ "$($SOURCE_BIN --version)" == "$EXPECTED_VERSION" ]]
[[ -x "$CFT_SOURCE/chrome-linux64/chrome" ]]
[[ "$(sha256sum "$CFT_SOURCE/chrome-linux64/chrome" | awk '{print $1}')" == "$CFT_SHA256" ]]
[[ -x "$WEBSOCKIFY" ]]
[[ "$(sha256sum "$WEBSOCKIFY" | awk '{print $1}')" == "$WEBSOCKIFY_SHA256" ]]
[[ -x /usr/bin/Xvfb && -x /usr/bin/x11vnc && -x /usr/bin/xauth ]]
[[ -f /opt/ordivon/external/novnc/1.7.0/vnc.html ]]

install -d -m 0755 /opt/claude-private/versions/2.1.274 /usr/local/libexec/claude-private /etc/claude-private /workspace
install -d -m 0700 /var/lib/claude-private/home /var/lib/claude-private/auth-workspace
install -m 0755 "$SOURCE_BIN" "$DEST"
[[ "$(sha256sum "$DEST" | awk '{print $1}')" == "$EXPECTED_SHA256" ]]

if [[ ! -x "$CFT_DEST/chrome-linux64/chrome" ]] || [[ "$(sha256sum "$CFT_DEST/chrome-linux64/chrome" | awk '{print $1}')" != "$CFT_SHA256" ]]; then
  rm -rf "$CFT_DEST.new"
  cp -a "$CFT_SOURCE" "$CFT_DEST.new"
  rm -rf "$CFT_DEST"
  mv "$CFT_DEST.new" "$CFT_DEST"
fi
[[ "$(sha256sum "$CFT_DEST/chrome-linux64/chrome" | awk '{print $1}')" == "$CFT_SHA256" ]]

install -m 0644 "$ROOT/settings.json" /etc/claude-private/settings.json
install -m 0644 "$ROOT/nsswitch.conf" /etc/claude-private/nsswitch.conf
install -m 0644 "$ROOT/resolv.conf" /etc/claude-private/resolv.conf
install -m 0644 "$ROOT/hosts" /etc/claude-private/hosts
install -m 0644 "$ROOT/hostname" /etc/claude-private/hostname
install -m 0644 "$ROOT/machine-id" /etc/claude-private/machine-id
install -m 0755 "$ROOT/claude-private-enter" /usr/local/libexec/claude-private/claude-private-enter
install -m 0755 "$ROOT/claude-private" /usr/local/bin/claude-private
install -m 0755 "$ROOT/oauth/prepare-xauth.sh" /usr/local/libexec/claude-private/prepare-oauth-xauth
install -m 0755 "$ROOT/oauth/prepare-profile.sh" /usr/local/libexec/claude-private/prepare-oauth-profile
install -m 0755 "$ROOT/oauth/oauth-browser-open" /usr/local/libexec/claude-private/oauth-browser-open
for unit in "$ROOT"/oauth/*.service "$ROOT"/oauth/*.target; do
  install -m 0644 "$unit" "/etc/systemd/system/$(basename "$unit")"
done
systemctl daemon-reload

/usr/local/bin/claude-private --version
"$CFT_DEST/chrome-linux64/chrome" --version
