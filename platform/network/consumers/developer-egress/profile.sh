# shellcheck shell=bash
# Ordivon Network v2 developer egress.
# Reuse the existing shared Surfshark provider-egress endpoint; do not open
# another WireGuard session or change the host default route.
# Explicit caller proxy settings win. Applies only to login-shell tooling,
# not to managed systemd/network service transport.
if [ "${ORDIVON_DEV_VPN:-auto}" != "off" ]; then
    _ordivon_dev_proxy="http://10.252.246.2:19680"
    # curl and Python prefer lowercase proxy aliases when both are supplied.
    # Normalize once so subprocesses cannot choose contradictory transports.
    # Keep curl, Python and other client aliases on exactly one route.
    HTTPS_PROXY="${https_proxy:-${HTTPS_PROXY:-$_ordivon_dev_proxy}}"
    HTTP_PROXY="${http_proxy:-${HTTP_PROXY:-$_ordivon_dev_proxy}}"
    https_proxy="$HTTPS_PROXY"
    http_proxy="$HTTP_PROXY"
    # Model Provider is the existing allowlisted HTTPS transport for model clients.
    # Generic CLI egress remains on the separate shared VPN proxy.
    ORDIVON_MODEL_PROVIDER_HTTPS_PROXY="${ORDIVON_MODEL_PROVIDER_HTTPS_PROXY:-http://127.0.0.1:19881}"
    export ORDIVON_MODEL_PROVIDER_HTTPS_PROXY

    # Merge case aliases and defaults exactly once. A wildcard would turn
    # off the VPN for every hostname; use ORDIVON_DEV_VPN=off explicitly.
    # urllib ignores CIDR NO_PROXY: prevent routing the provider host back into itself.
    _ordivon_private_no_proxy="localhost,127.0.0.1,::1,.local,.internal,.ts.net,host.docker.internal,host.containers.internal,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,100.64.0.0/10,169.254.169.254,10.252.246.2"
    _ordivon_no_proxy_source="${no_proxy:+$no_proxy,}${NO_PROXY:+$NO_PROXY,}$_ordivon_private_no_proxy"
    # Bash read consumes only the first line. Reject controls instead of
    # silently dropping later NO_PROXY entries or misrepresenting the route.
    if [[ "$_ordivon_no_proxy_source" =~ [[:cntrl:]] ]]; then
        NO_PROXY="$_ordivon_private_no_proxy"
        no_proxy="$NO_PROXY"
        export NO_PROXY no_proxy
        echo 'Ordivon network: inherited NO_PROXY contains control characters' >&2
        if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then exit 64; fi
        return 64
    fi
    IFS=',' read -r -a _ordivon_no_proxy_parts <<< "$_ordivon_no_proxy_source"
    _ordivon_no_proxy_merged=""
    _ordivon_no_proxy_unsafe=0
    for _ordivon_no_proxy_part in "${_ordivon_no_proxy_parts[@]}"; do
        [ -n "$_ordivon_no_proxy_part" ] || continue
        if [[ "$_ordivon_no_proxy_part" =~ ^[[:space:]]*(\*|0\.0\.0\.0/0|::/0)[[:space:]]*$ ]]; then
            # Preserve private exclusions while rejecting global proxy bypass,
            # including curl's IPv4/IPv6 CIDR syntax.
            _ordivon_no_proxy_unsafe="${BASH_REMATCH[1]}"
            continue
        fi
        # curl accepts arbitrary CIDRs in NO_PROXY. Source-declared private
        # networks are the only permitted CIDR exclusions; a caller-supplied
        # /1, /2 or other public network must never silently bypass this VPN.
        if [[ "$_ordivon_no_proxy_part" == */* ]]; then
            case ",$_ordivon_private_no_proxy," in
                *,"$_ordivon_no_proxy_part",*) ;;
                *)
                    _ordivon_no_proxy_unsafe="unapproved CIDR"
                    continue
                    ;;
            esac
        fi
        # Only source-owned private destinations and internal-name suffixes
        # may bypass the VPN. A public hostname exception is as unsafe as a
        # broad CIDR, but must not invalidate the private exceptions.
        case ",$_ordivon_private_no_proxy," in
            *,"$_ordivon_no_proxy_part",*) ;;
            *)
                case "${_ordivon_no_proxy_part,,}" in
                    *.internal|*.local|*.ts.net) ;;
                    *)
                        _ordivon_no_proxy_unsafe="unapproved destination"
                        continue
                        ;;
                esac
                ;;
        esac
        case ",$_ordivon_no_proxy_merged," in
            *,"$_ordivon_no_proxy_part",*) ;;
            *) _ordivon_no_proxy_merged="${_ordivon_no_proxy_merged:+$_ordivon_no_proxy_merged,}$_ordivon_no_proxy_part" ;;
        esac
    done
    NO_PROXY="$_ordivon_no_proxy_merged"
    no_proxy="$NO_PROXY"
    export HTTPS_PROXY https_proxy HTTP_PROXY http_proxy NO_PROXY no_proxy
    if [ "$_ordivon_no_proxy_unsafe" != 0 ]; then
        printf 'Ordivon network: NO_PROXY=%s disables required VPN; use ORDIVON_DEV_VPN=off for direct egress\n' "$_ordivon_no_proxy_unsafe" >&2
        unset _ordivon_dev_proxy _ordivon_private_no_proxy _ordivon_no_proxy_source _ordivon_no_proxy_parts _ordivon_no_proxy_merged _ordivon_no_proxy_part _ordivon_no_proxy_unsafe
        if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
            exit 1
        fi
        return 1
    fi
    # Managed Runtime EnvironmentFile must use the canonical outbound
    # transports. Interactive developer shells can choose another proxy;
    # that permission must not leak into the production service.
    if [[ "${BASH_SOURCE[0]}" == "$0" && "${1:-}" == "--systemd-env" && $# -eq 1 ]]; then
        if [[ "$HTTPS_PROXY" != "$_ordivon_dev_proxy" ||
              "$HTTP_PROXY" != "$_ordivon_dev_proxy" ||
              "$ORDIVON_MODEL_PROVIDER_HTTPS_PROXY" != "http://127.0.0.1:19881" ]]; then
            printf '%s\\n' "Ordivon Runtime network: inherited proxy conflicts with approved provider" >&2
            exit 64
        fi
    fi
    unset _ordivon_dev_proxy _ordivon_private_no_proxy _ordivon_no_proxy_source _ordivon_no_proxy_parts _ordivon_no_proxy_merged _ordivon_no_proxy_part _ordivon_no_proxy_unsafe
fi

# Reuse the same scoped Network-v2 proxy for non-login Agent/Runtime tools:
#   bash /etc/profile.d/91-ordivon-development-vpn.sh -- /absolute/tool args...
# Sourcing the profile never starts a subprocess. Direct invocation alone
# starts the child, preserving command identity and argument boundaries.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    # A systemd EnvironmentFile is not a login shell. Export the existing
    # generic VPN aliases AND the distinct allowlisted model transport.
    # These are public endpoints, not credentials or additional VPN sessions.
    if [[ "${1:-}" == "--systemd-env" && $# -eq 1 ]]; then
        if [[ "${ORDIVON_DEV_VPN:-auto}" == "off" ]]; then
            echo "Runtime VPN materialization cannot use disabled egress" >&2
            exit 64
        fi
        _ordivon_env_keys=(HTTPS_PROXY HTTP_PROXY https_proxy http_proxy NO_PROXY no_proxy ORDIVON_MODEL_PROVIDER_HTTPS_PROXY)
        # EnvironmentFile syntax interprets newlines, quoting, and backslashes.
        # Validate every value before emitting any assignment (atomic projection).
        for _ordivon_key in "${_ordivon_env_keys[@]}"; do
            _ordivon_value="${!_ordivon_key:-}"
            if [[ -z "$_ordivon_value" ]]; then
                echo "Runtime VPN setting $_ordivon_key is missing" >&2
                exit 64
            fi
            if [[ "$_ordivon_value" =~ [[:space:]] || "$_ordivon_value" == *\\* || "$_ordivon_value" == *\"* || "$_ordivon_value" == *\'* ]]; then
                echo "Runtime VPN setting $_ordivon_key cannot be represented as a literal EnvironmentFile value" >&2
                exit 64
            fi
        done
        for _ordivon_key in "${_ordivon_env_keys[@]}"; do
            printf '%s=%s\n' "$_ordivon_key" "${!_ordivon_key}"
        done
        exit 0
    fi
    if [[ "${1:-}" != "--" || $# -lt 2 ]]; then
        printf '%s\n' 'usage: bash profile.sh -- /absolute/command [args...]' >&2
        exit 64
    fi
    shift
    exec "$@"
fi
