#!/bin/bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: install_release.sh <repo> <commit> <prefix>" >&2
  exit 2
fi

REPO=$1
COMMIT=$2
PREFIX=$3
UV=${ORDIVON_GATEWAY_RELEASE_UV:-/usr/bin/uv}
PYTHON_INSTALL_DIR=${ORDIVON_GATEWAY_PYTHON_INSTALL_DIR:-$PREFIX/python}
SCRIPT_DIR=$(CDPATH="" cd -- "$(dirname -- "$0")" && pwd)

case "$COMMIT" in
  *[!0-9a-f]*|'') echo "commit must be lowercase hexadecimal" >&2; exit 2 ;;
esac

RESOLVED=$(git -C "$REPO" rev-parse --verify "$COMMIT^{commit}")
if [ "$RESOLVED" != "$COMMIT" ]; then
  echo "commit must be the full resolved Git SHA" >&2
  exit 2
fi

mkdir -p "$PREFIX/releases"
RELEASE="$PREFIX/releases/$COMMIT"
if [ ! -d "$RELEASE" ]; then
  TMP="$PREFIX/releases/.tmp-$COMMIT-$$"
  trap 'rm -rf "$TMP"' EXIT
  mkdir -p "$TMP"
  git -C "$REPO" archive "$COMMIT" services/gateway | tar --strip-components=2 -x -C "$TMP"
  mv "$TMP" "$RELEASE"
  trap - EXIT
fi

# Compare the candidate to the CURRENT active public ABI, never Core against
# an unrelated Full manifest. The release files alone cannot prove which
# profile a running two-profile service selected.
SURFACE_PROFILE="$(printenv ORDIVON_GATEWAY_SURFACE_PROFILE || true)"
CURRENT_PROFILE="$(printenv ORDIVON_GATEWAY_CURRENT_SURFACE_PROFILE || true)"
if [ -z "$SURFACE_PROFILE" ]; then SURFACE_PROFILE=full; fi
case "$SURFACE_PROFILE" in
  full) CANDIDATE_MANIFEST="$RELEASE/mcp-surface.json" ;;
  core) CANDIDATE_MANIFEST="$RELEASE/mcp-surface-core.json" ;;
  collaboration) CANDIDATE_MANIFEST="$RELEASE/mcp-surface-collaboration.json" ;;
  *) echo "Gateway surface profile must be full, core, or collaboration" >&2; exit 2 ;;
esac
if [ -e "$PREFIX/current" ] && [ -f "$PREFIX/current/mcp-surface-core.json" ] \
   && [ -z "$CURRENT_PROFILE" ]; then
  echo "installed Gateway supports multiple profiles: require verified ORDIVON_GATEWAY_CURRENT_SURFACE_PROFILE" >&2
  exit 2
fi
if [ -z "$CURRENT_PROFILE" ]; then CURRENT_PROFILE=full; fi
case "$CURRENT_PROFILE" in
  full) CURRENT_MANIFEST="$PREFIX/current/mcp-surface.json" ;;
  core) CURRENT_MANIFEST="$PREFIX/current/mcp-surface-core.json" ;;
  collaboration) CURRENT_MANIFEST="$PREFIX/current/mcp-surface-collaboration.json" ;;
  *) echo "current Gateway surface profile must be full, core, or collaboration" >&2; exit 2 ;;
esac
if [ -e "$PREFIX/current" ] && [ ! -f "$CURRENT_MANIFEST" ]; then
  echo "current Gateway active profile manifest is absent" >&2
  exit 2
fi
/usr/bin/python3 "$SCRIPT_DIR/verify_tool_surface.py" \
  "$CANDIDATE_MANIFEST" \
  "$RELEASE/pyproject.toml" \
  "$CURRENT_MANIFEST"

if [ ! -f "$RELEASE/.python-version" ]; then
  echo "release is missing .python-version" >&2
  exit 2
fi
PYTHON_REQUEST=$(tr -d '\r\n' < "$RELEASE/.python-version")
if [ -z "$PYTHON_REQUEST" ]; then
  echo ".python-version must contain one Python request" >&2
  exit 2
fi

# A source-qualified interpreter can be supplied only by an explicit
# version-qualified absolute carrier; no unrelated SQLite pin is imposed
# on the Gateway adapter's normal release.
RELEASE_PYTHON=${ORDIVON_GATEWAY_RELEASE_PYTHON:-}
if [ -n "$RELEASE_PYTHON" ]; then
  case "$RELEASE_PYTHON" in
    /*) ;;
    *) echo "ORDIVON_GATEWAY_RELEASE_PYTHON must be an absolute interpreter path" >&2; exit 2 ;;
  esac
  if [ ! -f "$RELEASE_PYTHON" ] || [ ! -x "$RELEASE_PYTHON" ] || [ -L "$RELEASE_PYTHON" ]; then
    echo "qualified Gateway Python must be a regular executable, not a symlink" >&2
    exit 2
  fi
  PYTHON="$RELEASE_PYTHON"
else
  mkdir -p "$PYTHON_INSTALL_DIR"
  "$UV" python install --install-dir "$PYTHON_INSTALL_DIR" --no-bin "$PYTHON_REQUEST"
  PYTHON=$(UV_PYTHON_INSTALL_DIR="$PYTHON_INSTALL_DIR" "$UV" python find --no-project --managed-python "$PYTHON_REQUEST")
  chmod -R a+rX "$PYTHON_INSTALL_DIR"
fi

# Gateway is a stateless router; legacy SQLite worker transport is retired.
# Qualify only the release Python interpreter here.
"$PYTHON" - "$PYTHON_REQUEST" <<'PYTHON_CHECK'
import sys

requested = sys.argv[1]
actual = sys.version.split()[0]
if actual != requested or actual != "3.15.1":
    raise SystemExit(f"Gateway release Python mismatch: expected {requested}, got {actual}")
PYTHON_CHECK

UV_PYTHON_INSTALL_DIR="$PYTHON_INSTALL_DIR" "$UV" sync --locked --no-dev --python "$PYTHON" --project "$RELEASE"
chmod -R a+rX "$RELEASE"

# Source manifests are necessary but not enough: execute the installed
# Gateway package's existing official MCP SDK surface contract before promote.
"$RELEASE/.venv/bin/python" "$RELEASE/packaging/windows/verify_release.py"

# In a live systemd deployment, root-side SDK checks alone cannot prove that
# the service's DynamicUser can traverse the selected interpreter/shebang.
# Prefer the native runuser command for the explicit release service identity.
# Keep this opt-in so disposable CI/other prefixes need no host service account.
SERVICE_USER=${ORDIVON_GATEWAY_RELEASE_SERVICE_USER:-}
if [ -n "$SERVICE_USER" ]; then
  if ! command -v runuser >/dev/null 2>&1; then
    echo "service-user preflight requires runuser" >&2
    exit 1
  fi
  if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    echo "release service user is unavailable" >&2
    exit 1
  fi
  runuser -u "$SERVICE_USER" -- "$RELEASE/.venv/bin/python" -c 'import ordivon_gateway'
  runuser -u "$SERVICE_USER" -- "$RELEASE/.venv/bin/opentelemetry-instrument" --help >/dev/null
  printf 'service_user_preflight=pass user=%s\n' "$SERVICE_USER"
fi

ln -sfn "releases/$COMMIT" "$PREFIX/current.next"
mv -Tf "$PREFIX/current.next" "$PREFIX/current"

printf 'installed_release=%s\n' "$COMMIT"
printf 'release_dir=%s\n' "$RELEASE"
