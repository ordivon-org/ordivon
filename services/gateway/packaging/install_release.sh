#!/bin/bash
set -euo pipefail

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ] || { [ "$#" -eq 4 ] && [ "$4" != "--prepare-only" ]; }; then
  echo "usage: install_release.sh <repo> <commit> <prefix> [--prepare-only]" >&2
  exit 2
fi

REPO=$1
COMMIT=$2
PREFIX=$3
PREPARE_ONLY=false
if [ "$#" -eq 4 ]; then
  PREPARE_ONLY=true
fi
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

/usr/bin/python3 "$SCRIPT_DIR/verify_tool_surface.py" \
  "$RELEASE/mcp-surface.json" \
  "$RELEASE/pyproject.toml" \
  "$PREFIX/current/mcp-surface.json"

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

# Preserve actual public MCP contracts across in-place upgrades, not only
# tool names and their manifest digest. Observe original SDK schemas through
# each release's own Python environment; never maintain a second tool registry.
# This is a separate Agent-consumer gate, not a Security or Host cutover grant.
if [ -f "$PREFIX/current/mcp-surface.json" ]; then
  if [ ! -x "$PREFIX/current/.venv/bin/python" ]; then
    echo "native public ABI baseline is unavailable in current release" >&2
    exit 1
  fi
  ABI_OLD=$(mktemp)
  ABI_NEW=$(mktemp)
  trap 'rm -f -- "$ABI_OLD" "$ABI_NEW"' EXIT
  "$PREFIX/current/.venv/bin/python" "$RELEASE/packaging/verify_tool_surface.py" --emit-native > "$ABI_OLD"
  "$RELEASE/.venv/bin/python" "$RELEASE/packaging/verify_tool_surface.py" --emit-native > "$ABI_NEW"
  if /usr/bin/python3 "$RELEASE/packaging/verify_tool_surface.py" --compare-native "$ABI_OLD" "$ABI_NEW"; then
    printf 'native_public_abi=COMPATIBLE\n'
  else
    abi_status=$?
    if [ "$abi_status" -ne 2 ]; then
      exit "$abi_status"
    fi
    if [ "$PREPARE_ONLY" != true ]; then
      echo "native_public_abi=INCOMPATIBLE: preserve old Agent ABI or qualify versioned migration" >&2
      exit 2
    fi
    printf 'native_public_abi=INCOMPATIBLE_PREPARED_ONLY_NOT_PROMOTABLE\n'
  fi
  rm -f -- "$ABI_OLD" "$ABI_NEW"
  trap - EXIT
fi

# Pre-staging prepares and verifies the exact immutable candidate using the
# same installed native MCP SDK and optional service-user checks, but MUST NOT
# promote it or change any running service. This decouples dependency builds
# from an Operator-coordinated Host/Gateway cutover. The ordinary 3-argument
# activation path below ALWAYS rechecks live Host/Security/consumer conditions
# before any production symlink promotion. Staging is never an authorization
# or a successful migration witness.
if [ "$PREPARE_ONLY" = true ]; then
  printf 'prepared_release=%s\n' "$COMMIT"
  printf 'prepared_dir=%s\n' "$RELEASE"
  printf 'activation=NOT_PERFORMED\n'
  exit 0
fi

# Two different production changes must not borrow one another's proof.
# Class A: an unchanged-authority same-route software upgrade requires the
# currently installed Security/PEP bytes and exact MCP composition, equal
# authenticated Owner endpoint configuration, a real Host read, positive
# running-source identity and live anonymous-denial canaries. Source itself
# does not grant another Principal or certify a new Host/Cloudflare route.
# Class B: any route, ingress, policy or Owner-authority change must still pass
# the original Host/Security/Cloudflare migration admission. Unknown fails
# closed. Classification comes from the native system, never a caller flag.
# Isolated test/staging prefixes keep their original installer semantics.
if [ "$(realpath -m "$PREFIX")" = "/opt/ordivon/gateway" ]; then
  if "$RELEASE/.venv/bin/python" "$RELEASE/packaging/check_same_route_admission.py" \
    --installed-release "$PREFIX/current" --candidate-release "$RELEASE"; then
    printf 'release_change_class=SAME_ROUTE_EXISTING_AUTHORITY\n'
  else
    "$RELEASE/.venv/bin/python" "$RELEASE/packaging/check_live_host_admission.py" \
      --policy-data "/run/credentials/ordivon-security-gateway-authzen.service/trusted-issuer"
  fi
fi

ln -sfn "releases/$COMMIT" "$PREFIX/current.next"
mv -Tf "$PREFIX/current.next" "$PREFIX/current"

printf 'installed_release=%s\n' "$COMMIT"
printf 'release_dir=%s\n' "$RELEASE"
