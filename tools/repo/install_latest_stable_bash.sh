#!/usr/bin/env bash
# Reproducibly build Bash 5.3 plus the first 20 upstream GNU patches.
# This is an isolated CI tool, never a replacement for the OS /bin/bash.
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
target="${1:?usage: install_latest_stable_bash.sh ABSOLUTE_OUTPUT_DIRECTORY}"
[[ "$target" = /* ]] || { echo "Target must be absolute" >&2; exit 2; }
manifest="$repo/tools/repo/bash-5.3.20.sha256"
[[ -f "$manifest" ]] || { echo "Missing pinned upstream SHA-256 manifest" >&2; exit 2; }
[[ "$(wc -l < "$manifest")" -eq 21 ]] || { echo "Expected 1 source + 20 patches" >&2; exit 2; }

if [[ -x "$target/bin/bash" ]] && "$target/bin/bash" -c '[[ "$BASH_VERSION" == "5.3.20(1)-release" ]]'; then
  echo "Bash 5.3.20 already verified in isolated target"
  exit 0
fi

scratch="$(mktemp -d "${RUNNER_TEMP:-/tmp}/ordivon-gnu-bash5320.XXXXXXXX")"
trap 'rm -rf -- "$scratch"' EXIT
mkdir -p "$scratch/dist" "$scratch/src" "$scratch/prefix"
base='https://ftp.gnu.org/gnu/bash'

download_one() {
  local name="$1" remote="$2"
  if [[ -n "${ORDIVON_BASH_DIST_DIR:-}" ]]; then
    # Air-gapped/local proof uses identical upstream bytes and hash checks.
    cp -- "${ORDIVON_BASH_DIST_DIR}/$name" "$scratch/dist/$name"
    return
  fi
  local url
  for url in \
    "https://ftp.osuosl.org/pub/gnu/bash/$remote" \
    "https://mirrors.ocf.berkeley.edu/gnu/bash/$remote" \
    "$base/$remote"; do
    # Use bounded first-attempt latency rather than a multi-minute retry on
    # one stalled mirror; SHA-256 enforces exact bytes, not server trust.
    if curl --fail --location --silent --show-error --connect-timeout 5 \
        --max-time 40 --speed-time 10 --speed-limit 16384 \
        "$url" -o "$scratch/dist/$name"; then
      return
    fi
  done
  echo "All GNU mirrors failed for $name" >&2
  return 1
}

download_one bash-5.3.tar.gz bash-5.3.tar.gz
for number in $(seq -f '%03g' 1 20); do
  download_one "bash53-$number" "bash-5.3-patches/bash53-$number"
done
(
  cd "$scratch/dist"
  sha256sum --status --check "$manifest"
) || { echo "FAIL: upstream Bash 5.3 + 20 patches do not match pinned SHA-256" >&2; exit 7; }

tar -xzf "$scratch/dist/bash-5.3.tar.gz" -C "$scratch/src"
for number in $(seq -f '%03g' 1 20); do
  patch --silent --directory="$scratch/src/bash-5.3" --strip=0 \
    < "$scratch/dist/bash53-$number"
done
(
  cd "$scratch/src/bash-5.3"
  ./configure --prefix="$scratch/prefix" --without-bash-malloc >/dev/null
  make -j "${BASH_BUILD_JOBS:-4}" >/dev/null
  make install >/dev/null
)
[[ -x "$scratch/prefix/bin/bash" ]] || { echo "Bash binary missing" >&2; exit 8; }
"$scratch/prefix/bin/bash" -c '[[ "$BASH_VERSION" == "5.3.20(1)-release" ]]' ||
  { echo "Wrong Bash patchlevel" >&2; exit 9; }

# Deploy the small isolated executable, not an OS package mutation.
mkdir -p "$target/bin"
install -m 755 "$scratch/prefix/bin/bash" "$target/bin/bash"
"$target/bin/bash" --version | head -1
