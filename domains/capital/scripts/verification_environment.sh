# Sourced by qualified verification tasks; direct developer pytest is separate.
# No operator exploratory selection, injected plugins or disabled assertions.
for override in PYTEST_ADDOPTS PYTEST_PLUGINS PYTHONOPTIMIZE; do
    if [[ -n "${!override-}" ]]; then
        printf 'Capital verification rejects inherited %s\n' "$override" >&2
        return 2
    fi
done
