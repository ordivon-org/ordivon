"""Regression evidence for the Network v2 developer shell profile."""

import json
import subprocess

import pytest
import sys
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1] / "consumers/developer-egress/profile.sh"
PROXY = "http://10.252.246.2:19680"


def _source_profile(**env_additions: str) -> dict[str, str]:
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", **env_additions}
    command = (
        'source "$1"; '
        'printf "HTTPS_PROXY=%s\\n" "$HTTPS_PROXY"; '
        'printf "HTTP_PROXY=%s\\n" "$HTTP_PROXY"; '
        'printf "NO_PROXY=%s\\n" "$NO_PROXY"; '
        'printf "https_proxy=%s\\n" "$https_proxy"; '
        'printf "http_proxy=%s\\n" "$http_proxy"; '
        'printf "no_proxy=%s\\n" "$no_proxy"'
    )
    proc = subprocess.run(
        ["/usr/bin/bash", "--noprofile", "--norc", "-c", command, "--", str(PROFILE)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return dict(line.split("=", 1) for line in proc.stdout.splitlines())



def test_python_urllib_bypasses_private_provider_without_self_proxying() -> None:
    # curl understands NO_PROXY CIDR; Python's urllib does not. The shared
    # carrier's *exact* host must bypass itself even if login already ran.
    from urllib.parse import urlsplit

    provider_host = urlsplit(PROXY).hostname
    assert provider_host is not None
    exported = _source_profile()
    assert provider_host in exported["NO_PROXY"].split(",")

    script = (
        "import json,urllib.request; "
        "print(json.dumps({"
        f"'carrier': urllib.request.proxy_bypass('{provider_host}'),"
        "'external': urllib.request.proxy_bypass('pypi.org')"
        "}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", **exported},
    )
    assert json.loads(result.stdout) == {"carrier": True, "external": False}


def test_default_shell_uses_existing_network_provider() -> None:
    env = _source_profile()
    assert env["HTTPS_PROXY"] == PROXY
    assert env["HTTP_PROXY"] == PROXY
    assert "localhost" in env["NO_PROXY"]
    assert "127.0.0.1" in env["NO_PROXY"]
    assert ".ts.net" in env["NO_PROXY"]


def test_model_client_receives_existing_loopback_provider_without_changing_global_vpn() -> None:
    result = subprocess.run(
        ["/usr/bin/bash", "--noprofile", "--norc", "-c",
         'source "$1"; printf "%s|%s" "$HTTPS_PROXY" "$ORDIVON_MODEL_PROVIDER_HTTPS_PROXY"',
         "--", str(PROFILE)],
        env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
        capture_output=True, text=True, check=True,
    )
    assert result.stdout == PROXY + "|http://127.0.0.1:19881"


def test_explicit_caller_proxy_preserved() -> None:
    env = _source_profile(HTTPS_PROXY="http://127.0.0.1:59999", NO_PROXY="example.internal")
    assert env["HTTPS_PROXY"] == "http://127.0.0.1:59999"
    assert "example.internal" in env["NO_PROXY"]
    assert "localhost" in env["NO_PROXY"]


def test_disable_option_leaves_existing_transport_unmodified() -> None:
    env = _source_profile(ORDIVON_DEV_VPN="off")
    assert env["HTTPS_PROXY"] == ""
    assert env["HTTP_PROXY"] == ""
    assert env["NO_PROXY"] == ""


def test_repeated_login_does_not_duplicate_private_exclusions() -> None:
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin"}
    command = 'source "$1"; source "$1"; printf "%s\\n" "$NO_PROXY"'
    proc = subprocess.run(
        ["/usr/bin/bash", "--noprofile", "--norc", "-c", command, "--", str(PROFILE)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    parts = proc.stdout.strip().split(",")
    assert parts.count("localhost") == 1
    assert parts.count("127.0.0.1") == 1


def test_conflicting_proxy_case_aliases_have_one_effective_route() -> None:
    # curl and Python urllib prefer lowercase names; the shell must not
    # offer contradictory transport or bypass choices to child processes.
    env = _source_profile(
        HTTPS_PROXY="http://wrong-uppercase-proxy.invalid:8899",
        https_proxy="http://intended-lowercase-proxy.invalid:8898",
        HTTP_PROXY="http://wrong-uppercase-http.invalid:8877",
        http_proxy="http://intended-lowercase-http.invalid:8876",
        NO_PROXY="upper.internal",
        no_proxy="lower.internal",
    )
    assert env["HTTPS_PROXY"] == env["https_proxy"] == "http://intended-lowercase-proxy.invalid:8898"
    assert env["HTTP_PROXY"] == env["http_proxy"] == "http://intended-lowercase-http.invalid:8876"
    assert env["NO_PROXY"] == env["no_proxy"]
    assert "upper.internal" in env["NO_PROXY"].split(",")
    assert "lower.internal" in env["NO_PROXY"].split(",")
    assert "localhost" in env["NO_PROXY"].split(",")


def test_case_alias_normalization_is_idempotent_across_login_shells() -> None:
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HTTPS_PROXY": "http://upper.invalid:8811",
        "https_proxy": "http://lower.invalid:8822",
        "NO_PROXY": "upper.internal",
        "no_proxy": "lower.internal",
    }
    cmd = (
        'source "$1"; first="$https_proxy|$no_proxy"; '
        'source "$1"; test "$first" = "$https_proxy|$no_proxy"; '
        'test "$HTTPS_PROXY" = "$https_proxy"; '
        'test "$NO_PROXY" = "$no_proxy"'
    )
    subprocess.run(["/usr/bin/bash", "--noprofile", "--norc", "-c", cmd, "--", str(PROFILE)], env=env, check=True)


def _capture_network_env(**env_additions: str) -> subprocess.CompletedProcess[str]:
    script = (
        'set -e; source "$1"; '
        'printf "HTTPS_PROXY=%s\n" "$HTTPS_PROXY"; '
        'printf "https_proxy=%s\n" "$https_proxy"; '
        'printf "HTTP_PROXY=%s\n" "$HTTP_PROXY"; '
        'printf "http_proxy=%s\n" "$http_proxy"; '
        'printf "NO_PROXY=%s\n" "$NO_PROXY"; '
        'printf "no_proxy=%s\n" "$no_proxy"; '
        'printf "consumer-ran=yes\n"'
    )
    return subprocess.run(
        ["/usr/bin/bash", "--noprofile", "--norc", "-c", script, "--", str(PROFILE)],
        check=False,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", **env_additions},
    )


def test_lowercase_only_proxy_populates_uppercase_compatibility() -> None:
    result = _capture_network_env(https_proxy="http://127.0.0.1:57999")
    assert result.returncode == 0
    env = dict(line.split("=", 1) for line in result.stdout.splitlines())
    assert env["HTTPS_PROXY"] == "http://127.0.0.1:57999"
    assert env["https_proxy"] == env["HTTPS_PROXY"]


def test_no_proxy_cases_are_merged_exactly_once() -> None:
    result = _capture_network_env(
        NO_PROXY="example.internal,localhost",
        no_proxy="build.internal,example.internal",
    )
    assert result.returncode == 0
    env = dict(line.split("=", 1) for line in result.stdout.splitlines())
    assert env["NO_PROXY"] == env["no_proxy"]
    items = env["NO_PROXY"].split(",")
    for item in ["localhost", "127.0.0.1", "example.internal", "build.internal"]:
        assert items.count(item) == 1


def test_global_cidr_exclusions_cannot_disable_required_proxy() -> None:
    # curl accepts global CIDR exclusions; they are as wide as NO_PROXY=*.
    for excluded in ("0.0.0.0/0", "::/0", " 0.0.0.0/0 ", " ::/0 "):
        result = _capture_network_env(no_proxy=excluded)
        assert result.returncode != 0
        assert "consumer-ran=yes" not in result.stdout


def test_ignored_cidr_profile_failure_preserves_other_private_bypasses() -> None:
    command = (
        'source "$1" || :; '
        'printf "HTTPS_PROXY=%s\\n" "$HTTPS_PROXY"; '
        'printf "https_proxy=%s\\n" "$https_proxy"; '
        'printf "NO_PROXY=%s\\n" "$NO_PROXY"; '
        'printf "no_proxy=%s\\n" "$no_proxy"'
    )
    for excluded in ("0.0.0.0/0", "::/0", " 0.0.0.0/0 "):
        result = subprocess.run(
            ["/usr/bin/bash", "--noprofile", "--norc", "-c", command, "--", str(PROFILE)],
            env={"PATH": "/usr/bin:/bin", "no_proxy": f"{excluded},registry.private.internal"},
            check=True, capture_output=True, text=True,
        )
        values = dict(line.split("=", 1) for line in result.stdout.splitlines())
        assert values["HTTPS_PROXY"] == values["https_proxy"] == PROXY
        assert values["NO_PROXY"] == values["no_proxy"]
        assert "registry.private.internal" in values["NO_PROXY"].split(",")
        assert excluded.strip() not in [x.strip() for x in values["NO_PROXY"].split(",")]


def test_wildcard_no_proxy_cannot_bypass_required_vpn() -> None:
    result = _capture_network_env(no_proxy="*")
    assert result.returncode != 0
    assert "consumer-ran=yes" not in result.stdout


def test_ignored_wildcard_error_cannot_leave_direct_bypass_environment() -> None:
    # Login shells and some startup scripts may ignore a sourced script's
    # return code. Fail closed in the exported environment even then.
    command = (
        'source "$1" || :; '
        'printf "HTTPS_PROXY=%s\n" "$HTTPS_PROXY"; '
        'printf "https_proxy=%s\n" "$https_proxy"; '
        'printf "NO_PROXY=%s\n" "$NO_PROXY"; '
        'printf "no_proxy=%s\n" "$no_proxy"'
    )
    result = subprocess.run(
        ["/usr/bin/bash", "--noprofile", "--norc", "-c", command, "--", str(PROFILE)],
        env={"PATH": "/usr/bin:/bin", "no_proxy": "*"},
        capture_output=True,
        text=True,
        check=True,
    )
    values = dict(line.split("=", 1) for line in result.stdout.splitlines())
    assert values["HTTPS_PROXY"] == PROXY
    assert values["https_proxy"] == PROXY
    assert values["NO_PROXY"] == values["no_proxy"]
    assert "*" not in values["NO_PROXY"].split(",")
    assert "127.0.0.1" in values["NO_PROXY"].split(",")

def _curl_with_profile(url: str, **env_additions: str) -> subprocess.CompletedProcess[str]:
    """Exercise the actual CLI consumer rather than inspecting only shell text."""
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", **_source_profile(**env_additions)}
    return subprocess.run(
        [
            "/usr/bin/curl", "-q", "--fail", "--silent", "--show-error",
            "--max-time", "4", "-I", "-o", "/dev/null", "-w", "%{http_code}", url,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=7,
        env=env,
    )


def test_public_https_connect_is_routed_to_exact_proxy_and_fails_closed(tmp_path: Path) -> None:
    """A broken Provider must not turn an external HTTPS consumer into a direct request."""
    import socketserver
    import threading

    observed: list[str] = []

    class RejectingProxy(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            request = self.request.recv(4096)
            observed.append(request.split(b"\r\n", 1)[0].decode("ascii"))
            self.request.sendall(
                b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n"
                b"Connection: close\r\n\r\n"
            )

    with socketserver.TCPServer(("127.0.0.1", 0), RejectingProxy) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        proxy = f"http://127.0.0.1:{server.server_address[1]}"
        # Replace only the physical Provider address; exercise the real profile's
        # default environment and curl consumption, without network access.
        source = PROFILE.read_text(encoding="utf-8")
        assert source.count(PROXY) == 1
        candidate = tmp_path / "profile.sh"
        candidate.write_text(source.replace(PROXY, proxy), encoding="utf-8")
        command = (
            'source "$1"; exec /usr/bin/curl -q --fail --silent --show-error '
            '--max-time 4 -I -o /dev/null -w "%{http_code}" '
            '"https://consumer-contract.example.invalid/"'
        )
        try:
            result = subprocess.run(
                ["/usr/bin/bash", "--noprofile", "--norc", "-c", command, "--", str(candidate)],
                env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
                text=True, capture_output=True, check=False, timeout=7,
            )
        finally:
            server.shutdown()
            worker.join(timeout=2)

    assert observed == ["CONNECT consumer-contract.example.invalid:443 HTTP/1.1"]
    assert result.returncode != 0
    assert result.stdout == "000"


def test_private_loopback_bypasses_unavailable_provider_without_public_fallback() -> None:
    """The private-side consumer can reach its local service when the VPN is absent."""
    import http.server
    import threading

    class LocalHandler(http.server.BaseHTTPRequestHandler):
        def do_HEAD(self) -> None:
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args: object) -> None:
            pass

    with http.server.HTTPServer(("127.0.0.1", 0), LocalHandler) as local:
        worker = threading.Thread(target=local.serve_forever, daemon=True)
        worker.start()
        url = f"http://127.0.0.1:{local.server_address[1]}/local"
        try:
            result = _curl_with_profile(
                url,
                HTTP_PROXY="http://127.0.0.1:1",
                HTTPS_PROXY="http://127.0.0.1:1",
            )
        finally:
            local.shutdown()
            worker.join(timeout=2)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "204"

def _execute_with_profile(*args: str, **env_additions: str) -> subprocess.CompletedProcess[str]:
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", **env_additions}
    return subprocess.run(
        ["/usr/bin/bash", str(PROFILE), "--", *args],
        check=False,
        text=True,
        capture_output=True,
        env=env,
        timeout=20,
    )


def test_nonlogin_agent_process_explicitly_uses_same_provider_without_shell_login() -> None:
    command = (
        "import json,os,sys;print(json.dumps({"
        "'https':os.getenv('HTTPS_PROXY'),'http':os.getenv('HTTP_PROXY'),"
        "'bypass':os.getenv('NO_PROXY'),'argv':sys.argv[1:]}))"
    )
    result = _execute_with_profile(sys.executable, "-c", command, "one two", ";danger")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["https"] == PROXY
    assert data["http"] == PROXY
    assert ".ts.net" in data["bypass"]
    assert data["argv"] == ["one two", ";danger"]


def test_nonlogin_agent_exit_status_and_explicit_proxy_preserved() -> None:
    result = _execute_with_profile(
        sys.executable,
        "-c",
        "import os,sys; assert os.getenv('HTTPS_PROXY') == 'http://127.0.0.1:59999';sys.exit(23)",
        HTTPS_PROXY="http://127.0.0.1:59999",
    )
    assert result.returncode == 23, result.stderr


def test_nonlogin_agent_can_explicitly_opt_out() -> None:
    result = _execute_with_profile(
        sys.executable,
        "-c",
        "import os;assert not os.getenv('HTTPS_PROXY');assert not os.getenv('HTTP_PROXY')",
        ORDIVON_DEV_VPN="off",
    )
    assert result.returncode == 0, result.stderr


def test_direct_profile_execution_without_command_fails_instead_of_false_success() -> None:
    result = subprocess.run(
        ["/usr/bin/bash", str(PROFILE), "--"],
        check=False,
        text=True,
        capture_output=True,
        timeout=10,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
    )
    assert result.returncode != 0
    assert "usage" in result.stderr.lower()


def test_nonlogin_agent_never_runs_on_global_no_proxy_cidr() -> None:
    for excluded in ("0.0.0.0/0", "::/0"):
        result = _execute_with_profile(
            sys.executable, "-c", "print('UNSAFE_CHILD_EXECUTED')", NO_PROXY=excluded,
        )
        assert result.returncode != 0
        assert "UNSAFE_CHILD_EXECUTED" not in result.stdout
        assert f"NO_PROXY={excluded}" in result.stderr


def test_nonlogin_profile_rejects_wildcard_no_proxy_before_command_execution() -> None:
    result = _execute_with_profile(
        sys.executable,
        "-c",
        "print('UNSAFE_CHILD_EXECUTED')",
        NO_PROXY="*",
    )
    assert result.returncode != 0
    assert "UNSAFE_CHILD_EXECUTED" not in result.stdout
    assert "NO_PROXY=*" in result.stderr

def test_ignored_profile_failure_preserves_safe_exclusions_and_never_bypasses_public() -> None:
    # Developer login shells are not obligated to use errexit; their exported
    # environment must be safe even when a profile return status is ignored.
    # Python urllib strips whitespace from NO_PROXY entries.
    for unsafe in ("*", "  *  "):
        command = (
            'source "$1" || :; '
            'printf "NO_PROXY=%s\n" "$NO_PROXY"; '
            'printf "no_proxy=%s\n" "$no_proxy"; '
            'printf "HTTPS_PROXY=%s\n" "$HTTPS_PROXY"; '
            'printf "https_proxy=%s\n" "$https_proxy"'
        )
        result = subprocess.run(
            ["/usr/bin/bash", "--noprofile", "--norc", "-c", command, "--", str(PROFILE)],
            env={
                "PATH": "/usr/bin:/bin",
                "NO_PROXY": "registry.alpha.internal",
                "no_proxy": f"{unsafe},registry.beta.internal",
            },
            check=True,
            capture_output=True,
            text=True,
        )
        values = dict(line.split("=", 1) for line in result.stdout.splitlines())
        assert values["NO_PROXY"] == values["no_proxy"]
        assert values["HTTPS_PROXY"] == values["https_proxy"] == PROXY
        assert "*" not in [x.strip() for x in values["no_proxy"].split(",")]
        assert "registry.alpha.internal" in values["no_proxy"].split(",")
        assert "registry.beta.internal" in values["no_proxy"].split(",")
        program = (
            "import json,urllib.request;"
            "print(json.dumps([urllib.request.proxy_bypass_environment(n)"
            " for n in ('registry.alpha.internal','registry.beta.internal','pypi.org')]))"
        )
        consumer = subprocess.run(
            ["/usr/bin/python3", "-c", program],
            env={"PATH": "/usr/bin:/bin", **values},
            check=True,
            capture_output=True,
            text=True,
        )
        import json
        assert json.loads(consumer.stdout) == [True, True, False]


def test_nonlogin_python_https_consumes_selected_proxy_and_fails_closed(tmp_path: Path) -> None:
    """Real urllib transport, not just proxy environment variables."""
    import socketserver
    import threading

    requests: list[bytes] = []

    class Proxy(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            data = self.request.recv(4096)
            requests.append(data.split(b"\r\n", 1)[0])
            self.request.sendall(
                b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n"
                b"Connection: close\r\n\r\n"
            )

    with socketserver.TCPServer(("127.0.0.1", 0), Proxy) as server:
        server.timeout = 4
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        candidate = tmp_path / "profile.sh"
        script = PROFILE.read_text(encoding="utf-8")
        assert script.count(PROXY) == 1
        candidate.write_text(
            script.replace(PROXY, f"http://127.0.0.1:{server.server_address[1]}"),
            encoding="utf-8",
        )
        try:
            result = subprocess.run(
                [
                    "/usr/bin/bash", str(candidate), "--", sys.executable, "-c",
                    ("import urllib.request; "
                     "urllib.request.urlopen('https://consumer-network-contract.example.invalid/', timeout=3);"
                     "print('DIRECT_FALLBACK_FALSE_GREEN')"),
                ],
                env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
                text=True, capture_output=True, check=False, timeout=7,
            )
        finally:
            server.shutdown()
            worker.join(timeout=2)

    assert len(requests) == 1
    assert requests[0].startswith(b"CONNECT consumer-network-contract.example.invalid:443 HTTP/1.")
    assert result.returncode != 0
    assert "DIRECT_FALLBACK_FALSE_GREEN" not in result.stdout


def test_nonlogin_python_private_loopback_survives_unavailable_proxy() -> None:
    """Public access may be blocked without breaking local Runtime/Host RPC."""
    import http.server
    import threading

    class Local(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(204)
            self.end_headers()

        def log_message(self, *_args: object) -> None:
            pass

    with http.server.HTTPServer(("127.0.0.1", 0), Local) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        url = f"http://127.0.0.1:{server.server_address[1]}/runtime"
        try:
            result = _execute_with_profile(
                sys.executable, "-c",
                "import urllib.request,sys; "
                "print(urllib.request.urlopen(sys.argv[1],timeout=3).status)",
                url,
                HTTP_PROXY="http://127.0.0.1:9",
                HTTPS_PROXY="http://127.0.0.1:9",
            )
        finally:
            server.shutdown()
            worker.join(timeout=2)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "204"


def test_real_urllib_public_url_uses_selected_proxy_and_fails_closed() -> None:
    # Real urllib consumer, selected proxy and reachable direct-origin decoy.
    # This falsifies silent direct fallback, not just a missing-DNS failure.
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Reply(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.server.observed.append(self.path)
            body = self.server.answer
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args: object) -> None:
            pass

    servers = []
    threads = []
    for answer in (b"direct-origin", b"selected-provider-egress"):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Reply)
        server.answer = answer
        server.observed = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        threads.append(thread)

    origin, proxy = servers
    proxy_url = f"http://127.0.0.1:{proxy.server_port}"
    url = f"http://public.network.invalid:{origin.server_port}/agent-skill-tool"
    # Route only the simulated public hostname to a reachable local origin.
    # Under the approved proxy path no direct DNS lookup is needed.
    program = (
        "import socket,urllib.request,sys\n"
        "real_resolve=socket.getaddrinfo\n"
        "def resolve(host,port,*args,**kwargs):\n"
        "    return real_resolve('127.0.0.1' if host=='public.network.invalid' else host,"
        "port,*args,**kwargs)\n"
        "socket.getaddrinfo=resolve\n"
        f"url={url!r}\n"
        "try:\n"
        "    print(urllib.request.urlopen(url,timeout=2).read().decode())\n"
        "except OSError:\n"
        "    sys.exit(32)\n"
    )
    try:
        success = _execute_with_profile(
            sys.executable, "-c", program, http_proxy=proxy_url,
            no_proxy="private.network.internal",
        )
        assert success.returncode == 0, success.stderr
        assert success.stdout.strip() == "selected-provider-egress"
        assert proxy.observed == [url]
        assert origin.observed == [], "no direct origin use when proxy is healthy"

        # Keep the direct origin live while the selected proxy is down.
        proxy.shutdown()
        proxy.server_close()
        threads[1].join(timeout=3)
        failed = _execute_with_profile(
            sys.executable, "-c", program, http_proxy=proxy_url,
            no_proxy="private.network.internal",
        )
        assert failed.returncode == 32, (failed.stdout, failed.stderr)
        assert origin.observed == [], "proxy outage must not fall back to direct"
    finally:
        origin.shutdown()
        origin.server_close()
        threads[0].join(timeout=3)
        if threads[1].is_alive():
            proxy.shutdown()
            proxy.server_close()
            threads[1].join(timeout=3)








@pytest.mark.parametrize("wide_bypass", [
    "0.0.0.0/1",
    "128.0.0.0/1",
    "192.0.0.0/8",
    "8.0.0.0/8",
    "198.18.0.0/15",
    "::/1",
    "8000::/1",
])
def test_undeclared_cidr_no_proxy_cannot_direct_bypass_vpn(wide_bypass: str) -> None:
    """Only source-declared private CIDRs may bypass the selected VPN."""
    result = _capture_network_env(no_proxy=wide_bypass)
    assert result.returncode != 0
    assert "consumer-ran=yes" not in result.stdout
    assert "NO_PROXY" in result.stderr
    # Even if login startup ignores the shell error, the unsafe CIDR is absent.
    ignored = subprocess.run(
        [
            "/usr/bin/bash", "--noprofile", "--norc", "-c",
            'source "$1" || :; printf "%s" "$no_proxy"', "--", str(PROFILE),
        ],
        env={"PATH": "/usr/bin:/bin", "no_proxy": wide_bypass},
        capture_output=True, text=True, check=True,
    )
    assert wide_bypass not in ignored.stdout.split(",")


@pytest.mark.parametrize("local", [
    "service.internal",
    "registry.private.internal",
    "device.ts.net",
    "localhost",
    "127.0.0.1",
])
def test_private_no_proxy_consumer_local_ports_keep_working(local: str) -> None:
    result = _capture_network_env(no_proxy=local)
    assert result.returncode == 0
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    assert local in values["NO_PROXY"].split(",")

def test_public_no_proxy_entries_cannot_spawn_agent_or_runtime_child() -> None:
    # Unlike NO_PROXY=*, a single public-domain exception looks harmless yet
    # makes that provider request bypass the mandatory scoped VPN transport.
    for key, value in (
        ("NO_PROXY", "api.github.com"),
        ("no_proxy", ".com"),
        ("NO_PROXY", "api.github.com,build.internal"),
        ("no_proxy", "198.51.100.1"),
        ("NO_PROXY", "1.2.3.0/0"),
        ("no_proxy", "api.github.com,localhost"),
    ):
        result = _execute_with_profile(
            sys.executable, "-c", "print('UNSAFE_NETWORK_CHILD_RAN')",
            **{key: value},
        )
        assert result.returncode != 0, (key, value, result.stdout)
        assert "UNSAFE_NETWORK_CHILD_RAN" not in result.stdout


def test_ignored_public_bypass_error_never_leaves_public_direct_route() -> None:
    # Login startup may ignore a sourced script's nonzero return. The exported
    # env still must not exempt public providers from proxy routing.
    script = (
        'source "$1" || :; '
        'printf "NO_PROXY=%s\\n" "$NO_PROXY"; '
        'printf "no_proxy=%s\\n" "$no_proxy"; '
        'printf "HTTPS_PROXY=%s\\n" "$HTTPS_PROXY"'
    )
    r = subprocess.run(
        ["/usr/bin/bash", "--noprofile", "--norc", "-c", script, "--", str(PROFILE)],
        env={
            "PATH": "/usr/bin:/bin",
            "NO_PROXY": "api.github.com,build.internal",
            "no_proxy": ".com,localhost",
        },
        capture_output=True, text=True, check=True,
    )
    values = dict(line.split("=", 1) for line in r.stdout.splitlines())
    assert values["NO_PROXY"] == values["no_proxy"]
    assert "api.github.com" not in values["no_proxy"].split(",")
    assert ".com" not in values["no_proxy"].split(",")
    assert "build.internal" in values["no_proxy"].split(",")
    assert "localhost" in values["no_proxy"].split(",")
    assert values["HTTPS_PROXY"] == PROXY


def test_private_no_proxy_aliases_remain_usable() -> None:
    result = _capture_network_env(
        NO_PROXY="build.internal,service.ts.net,localhost",
        no_proxy="assets.local,.internal,.ts.net",
    )
    assert result.returncode == 0, result.stderr
    env = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    for name in ("build.internal", "service.ts.net", "localhost", "assets.local"):
        assert name in env["NO_PROXY"].split(",")



def test_systemd_env_rejects_inherited_proxies_without_partial_output() -> None:
    # Production materialization cannot inherit a developer-selected route.
    for wrong in (
        {"HTTPS_PROXY": "http://127.0.0.1:59999"},
        {"http_proxy": "http://127.0.0.1:59998"},
        {"ORDIVON_MODEL_PROVIDER_HTTPS_PROXY": "http://127.0.0.1:1"},
    ):
        result = subprocess.run(
            ["/usr/bin/bash", str(PROFILE), "--systemd-env"],
            env={"PATH": "/usr/bin:/bin", **wrong},
            text=True, capture_output=True, check=False, timeout=10,
        )
        assert result.returncode != 0, wrong
        assert result.stdout == ""


def test_systemd_env_uses_canonical_provider_and_private_bypass() -> None:
    result = subprocess.run(
        ["/usr/bin/bash", str(PROFILE), "--systemd-env"],
        env={"PATH": "/usr/bin:/bin", "NO_PROXY": "localhost,127.0.0.1"},
        text=True, capture_output=True, check=False, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    exported = dict(line.split("=", 1) for line in result.stdout.splitlines())
    assert exported["HTTPS_PROXY"] == exported["https_proxy"] == PROXY
    assert exported["HTTP_PROXY"] == exported["http_proxy"] == PROXY
    assert exported["ORDIVON_MODEL_PROVIDER_HTTPS_PROXY"] == "http://127.0.0.1:19881"
    assert exported["NO_PROXY"] == exported["no_proxy"]
    assert "localhost" in exported["NO_PROXY"].split(",")


def test_runtime_envfile_rejects_non_literal_values_without_partial_output() -> None:
    """An EnvironmentFile projection must not permit additional assignments.

    Values that systemd may reinterpret (newlines, continuations, quotes,
    whitespace) must fail before any part of the file is emitted.
    """
    cases = (
        ("HTTPS_PROXY", "http://127.0.0.1:7788\nINJECTED_ROUTE=direct"),
        ("HTTP_PROXY", "http://127.0.0.1:7788\nINJECTED_ROUTE=direct"),
        ("NO_PROXY", "localhost\nINJECTED_ROUTE=direct"),
        ("HTTPS_PROXY", "http://127.0.0.1:7788\\"),
        ("NO_PROXY", "localhost, example.org"),
        ("ORDIVON_MODEL_PROVIDER_HTTPS_PROXY", '"http://127.0.0.1:19881"'),
    )
    for name, value in cases:
        result = subprocess.run(
            ["/usr/bin/bash", str(PROFILE), "--systemd-env"],
            env={"PATH": "/usr/bin:/bin", name: value},
            capture_output=True, text=True, check=False,
        )
        assert result.returncode != 0, name
        assert result.stdout == "", name
        assert "INJECTED_ROUTE" not in result.stderr, name


def test_historical_discord_merge_requires_current_n05_consumer_before_revival() -> None:
    """A unique merge resolution is not a license to resurrect a daemon."""
    root = Path(__file__).resolve().parents[3]
    assert not (root / "platform/network/consumers/discord/systemd/network-v2-discord-egress.service").exists()
    plan = json.loads((root / "platform/network/planning/lego-plan-r1.json").read_text())
    n05 = next(x for x in plan["nodes"] if x["id"] == "N05")
    assert any(
        "77c36033da05586dbd965d407f35bf2fece578ef" in entry
        and "NO_CURRENT_CONSUMER" in entry
        and "UNPROVED" in entry
        for entry in n05["evidence"]
    )


def test_retired_model_provider_history_uses_existing_n05_consumer() -> None:
    """Only a qualified current consumer can justify reviving an old model readiness daemon."""
    root = Path(__file__).resolve().parents[3]
    retired = root / "platform/network/consumers/model-provider/ready.sh"
    assert not retired.exists()
    ready = (root / "tools/repo/workspace-ready").read_text(encoding="utf-8")
    assert 'platform/network/consumers/developer-egress/profile.sh' in ready
    plan = json.loads(
        (root / "platform/network/planning/lego-plan-r1.json").read_text(encoding="utf-8")
    )
    n05 = next(node for node in plan["nodes"] if node["id"] == "N05")
    evidence = " ".join(n05["evidence"])
    assert "83fb2956e051ad9c27c091e96631a842f8eebcc7" in evidence
    assert "7b51fd3e033f964db551c127e2e910ae3bc88ef8" in evidence
    assert "tests/test_developer_egress_profile.py" in evidence



def test_historical_capability_router_is_not_an_admitted_network_consumer() -> None:
    # Existing N05 owner-native CDC: commit uniqueness cannot resurrect a
    # retired standalone route DAG or grant network authority.
    root = Path(__file__).resolve().parents[1]
    retired = (
        "scripts/network_capability_router.py",
        "config/network-capability-routes.json",
        "tests/test_network_capability_router.py",
        "docs/NETWORK_CAPABILITY_ROUTER_R1.md",
    )
    assert all(not (root / name).exists() for name in retired)
    assert (root / "consumers/developer-egress/profile.sh").is_file()
    plan = json.loads((root / "planning/lego-plan-r1.json").read_text())
    owner = next(item for item in plan["nodes"] if item["id"] == "N05")
    evidence = " ".join(owner["evidence"])
    for commit in (
        "329f86db80dd", "086793c4174d", "08c485070671", "cb750b696b57",
        "d6388e91d7ea", "a9fadabd8f5c", "6840c27fd6ae", "e31280f36b2e",
    ):
        assert commit in evidence
    assert "NO_CURRENT_CONSUMER" in evidence
    assert "NOT_PROVEN_EQUIVALENT" in evidence
