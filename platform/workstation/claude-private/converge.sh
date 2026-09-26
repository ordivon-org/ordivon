#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_BIN=${CLAUDE_SOURCE_BIN:-/root/.local/share/claude/versions/2.1.274}
EXPECTED_SHA256=15e2d05148f801b5774032faad87e624ecd172e9903288bda448b892eb58fa07
EXPECTED_VERSION='2.1.274 (Claude Code)'
DEST=/opt/claude-private/versions/2.1.274/claude

[[ -x "$SOURCE_BIN" ]]
actual=$(sha256sum "$SOURCE_BIN" | awk '{print $1}')
[[ "$actual" == "$EXPECTED_SHA256" ]]
[[ "$($SOURCE_BIN --version)" == "$EXPECTED_VERSION" ]]

install -d -m 0755 /opt/claude-private/versions/2.1.274 /usr/local/libexec/claude-private /etc/claude-private /workspace
install -d -m 0700 /var/lib/claude-private/home /var/lib/claude-private/auth-workspace
install -m 0755 "$SOURCE_BIN" "$DEST"
[[ "$(sha256sum "$DEST" | awk '{print $1}')" == "$EXPECTED_SHA256" ]]

install -m 0644 "$ROOT/settings.json" /etc/claude-private/settings.json
install -m 0644 "$ROOT/nsswitch.conf" /etc/claude-private/nsswitch.conf
install -m 0644 "$ROOT/resolv.conf" /etc/claude-private/resolv.conf
install -m 0644 "$ROOT/hosts" /etc/claude-private/hosts
install -m 0644 "$ROOT/hostname" /etc/claude-private/hostname
install -m 0644 "$ROOT/machine-id" /etc/claude-private/machine-id
install -m 0755 "$ROOT/claude-private-enter" /usr/local/libexec/claude-private/claude-private-enter
install -m 0755 "$ROOT/claude-private" /usr/local/bin/claude-private

/usr/local/bin/claude-private --version
