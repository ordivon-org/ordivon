#!/usr/bin/env bash
set -euo pipefail
for f in external-lock.json adapters/*.json evidence/r7-artifact-development-publication-intent.json; do jq -e . "$f" >/dev/null; done
# Retired executable surfaces must not remain wired into CI or forward scripts.
retired_surfaces=(
  'scripts/temporal_integration_dispatch_smoke.py'
  'scripts/test-temporal-integration-boundary.py'
  'scripts/distribution_preflight.py'
  'scripts/test-distribution-preflight.py'
  'contracts/distribution-preflight.schema.json'
  'profiles/steam-linux-directory-r1.json'
)
repo="$(git rev-parse --show-toplevel)"
for retired in "${retired_surfaces[@]}"; do
  if matches="$(git -C "$repo" grep -n -F -e "$retired" -- .github capabilities/distribution/scripts ':!capabilities/distribution/scripts/test-structure.sh')"; then
    echo "FAIL retired Distribution surface remains executable: $retired" >&2
    printf '%s\n' "$matches" >&2
    exit 1
  else
    result=$?
    if ((result != 1)); then
      echo "FAIL unable to inspect tracked CI and Distribution scripts (git grep exit=$result)" >&2
      exit "$result"
    fi
  fi
done
# Exercise the real smoke entrypoint with a synthetic lock and a local Podman stand-in.
# A different image in the lock detects reintroduction of a hard-coded default.
probe="$(mktemp -d)"
trap 'rm -rf "$probe"' EXIT
mkdir -p "$probe/scripts" "$probe/bin"
cp scripts/test-openapi-generator.sh "$probe/scripts/"
cat > "$probe/external-lock.json" <<'JSON'
{"activated":{"openapi-generator":{"containerImage":"example.invalid/generator:lock-probe"}}}
JSON
cat > "$probe/bin/podman" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
out=""
while (($#)); do
  if [[ "$1" == -v && "$2" == *:/out ]]; then
    out="${2%:/out}"
  elif [[ "$1" == generate ]]; then
    printf '%s\n' "$previous"
    break
  fi
  previous="$1"
  shift
done
test -n "$out"
mkdir -p "$out/client/openapi_client/api"
touch "$out/client/README.md"
printf 'def get_object\n' > "$out/client/openapi_client/api/probe.py"
SH
chmod +x "$probe/bin/podman"
actual="$(env -u OPENAPI_GENERATOR_IMAGE PATH="$probe/bin:$PATH" bash "$probe/scripts/test-openapi-generator.sh")"
[[ "$actual" == $'example.invalid/generator:lock-probe\nPASS openapi-generator provider client smoke' ]]
actual="$(PATH="$probe/bin:$PATH" OPENAPI_GENERATOR_IMAGE=example.invalid/generator:override bash "$probe/scripts/test-openapi-generator.sh")"
[[ "$actual" == $'example.invalid/generator:override\nPASS openapi-generator provider client smoke' ]]
printf '%s\n' '{"activated":{"openapi-generator":{}}}' > "$probe/external-lock.json"
if env -u OPENAPI_GENERATOR_IMAGE PATH="$probe/bin:$PATH" bash "$probe/scripts/test-openapi-generator.sh" > "$probe/rejected.log" 2>&1; then
  echo 'FAIL missing default generator image unexpectedly accepted' >&2
  exit 1
fi
printf 'PASS Distribution source profiles and consumed R7 fixture\n'
