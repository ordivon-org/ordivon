#!/usr/bin/env python3
"""Structured Browser Use actions on Ordivon's isolated Browserless pool.

Browser Use owns browser perception/action helpers and its daemon. Browserless owns Chromium
lifecycle. This adapter exposes a bounded action surface instead of arbitrary Browser Use Python,
and constructs token-bearing CDP URLs only inside a controlled daemon-bootstrap child process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from browserless_substrate import BrowserlessPool

DEFAULT_CONFIG = Path("/etc/ordivon/browser-use-browserless.json")
SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
MAX_TEXT_BYTES = 32_768
MAX_OBSERVE_ELEMENTS = 160
ACTION_ROLES = (
    "button",
    "link",
    "textbox",
    "searchbox",
    "checkbox",
    "radio",
    "combobox",
    "listbox",
    "menuitem",
    "tab",
    "slider",
    "switch",
    "option",
)


def load_config(path: Path) -> tuple[dict, BrowserlessPool]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("kind") != "ordivon.browser-use-browserless-pool":
        raise ValueError("Browser Use config kind mismatch")
    pool = BrowserlessPool.from_dict(value.get("browserSubstrate"))
    if any(not endpoint.endpoint_id.startswith("browser-agent-") for endpoint in pool.endpoints):
        raise ValueError("Browser Use pool may contain only browser-agent-* endpoints")
    return value, pool


def session_name(session_id: str) -> str:
    if not SESSION_RE.fullmatch(session_id):
        raise ValueError("session-id must be 1..128 safe identifier characters")
    return "ordivon-bu-" + hashlib.sha256(session_id.encode()).hexdigest()[:24]


def select_endpoint(pool: BrowserlessPool, session_id: str, endpoint_id: str | None):
    if endpoint_id is None:
        return pool.select(session_id)
    rows = [row for row in pool.endpoints if row.endpoint_id == endpoint_id]
    if len(rows) != 1:
        raise ValueError("endpoint-id must resolve exactly once in the Browser Use pool")
    return rows[0]


def browser_env(endpoint, session_id: str, *, include_cdp: bool) -> dict[str, str]:
    env = dict(os.environ)
    env["BU_NAME"] = session_name(session_id)
    env["BH_OPEN_LIVE_URL"] = "0"
    env["BH_TAB_MARKER"] = "0"
    if include_cdp:
        env["BU_CDP_WS"] = endpoint.authenticated_operator_connection_endpoint(timeout_ms=300_000)
    else:
        env.pop("BU_CDP_WS", None)
        env.pop("BU_CDP_URL", None)
    return env


def _run_browser_use(
    executable: str, program: str, env: dict[str, str], *, timeout: int = 90
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [executable],
        input=program,
        text=True,
        capture_output=True,
        env=env,
        timeout=timeout,
        check=False,
    )


def ensure_daemon(executable: str, endpoint, session_id: str) -> None:
    if getattr(endpoint, "activation_unit", None):
        lifecycle = endpoint.ensure_active(start_timeout_seconds=20.0)
        if lifecycle.get("healthy") is not True:
            raise RuntimeError(
                "Browserless on-demand activation failed: "
                + str(lifecycle.get("detail") or lifecycle.get("status") or "unhealthy")
            )
    proc = _run_browser_use(
        executable,
        'import json\nprint(json.dumps({"standing":"DAEMON_READY","page":page_info()},sort_keys=True))\n',
        browser_env(endpoint, session_id, include_cdp=True),
        timeout=45,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "browser-use daemon bootstrap failed").strip()[
            -1200:
        ]
        raise RuntimeError(detail)


def _generated_env(endpoint, session_id: str) -> dict[str, str]:
    env = browser_env(endpoint, session_id, include_cdp=False)
    env["BH_REQUIRE_EXISTING_DAEMON"] = "1"
    return env


def _execute_generated(
    executable: str, endpoint, session_id: str, program: str, *, timeout: int = 90
) -> int:
    ensure_daemon(executable, endpoint, session_id)
    proc = _run_browser_use(
        executable, program, _generated_env(endpoint, session_id), timeout=timeout
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=os.sys.stderr)
    return int(proc.returncode)


def _validate_url(url: str) -> str:
    if not isinstance(url, str) or not url or url != url.strip():
        raise ValueError("url must be a non-empty trimmed string")
    scheme = urlsplit(url).scheme.lower()
    if scheme not in {"http", "https", "data"}:
        raise ValueError("Browser Use open permits only http, https, or data URLs")
    return url


def _validate_text(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    if len(value.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ValueError(f"{label} exceeds {MAX_TEXT_BYTES} UTF-8 bytes")
    return value


def _affordance_prelude() -> str:
    roles = json.dumps(list(ACTION_ROLES))
    lines = [
        "def _ordivon_affordances():",
        f"    roles=set({roles})",
        "    rows=[]",
        "    for n in cdp('Accessibility.getFullAXTree')['nodes']:",
        "        role=(n.get('role') or {}).get('value') or ''",
        "        name=(n.get('name') or {}).get('value') or ''",
        "        bid=n.get('backendDOMNodeId')",
        "        if role not in roles or not bid:",
        "            continue",
        "        row={'role':role,'name':name,'backendDOMNodeId':bid}",
        "        try:",
        "            q=cdp('DOM.getBoxModel', backendNodeId=bid)['model']['content']",
        "            row['x']=sum(q[0::2])/4; row['y']=sum(q[1::2])/4",
        "        except Exception:",
        "            row['x']=None; row['y']=None",
        "        rows.append(row)",
        f"    return rows[:{MAX_OBSERVE_ELEMENTS}]",
        "",
        "def _ordivon_page_info():",
        "    try:",
        "        return page_info()",
        "    except Exception:",
        "        return None",
        "",
    ]
    return "\n".join(lines)


def program_open(url: str) -> str:
    url = _validate_url(url)
    return (
        "import json\n"
        f"new_tab({json.dumps(url)})\nwait_for_load()\n"
        'print(json.dumps({"standing":"OPENED","page":page_info()},sort_keys=True))\n'
    )


def program_observe(*, include_text: bool, max_chars: int) -> str:
    if max_chars < 1 or max_chars > 20_000:
        raise ValueError("max-chars must be between 1 and 20000")
    text_expr = (
        f'body=js("document.body ? document.body.innerText : \\"\\"") or ""\nbody=body[:{max_chars}]\n'
        if include_text
        else "body=None\n"
    )
    return (
        "import json\n"
        + _affordance_prelude()
        + "try:\n    wait_for_load(timeout=10.0)\nexcept Exception:\n    pass\n"
        + text_expr
        + "rows=_ordivon_affordances()\n"
        'safe=[{"index":i,"role":r["role"],"name":r["name"],"x":r["x"],"y":r["y"]} for i,r in enumerate(rows)]\n'
        'print(json.dumps({"standing":"OBSERVED","page":page_info(),"affordances":safe,"visibleText":body},sort_keys=True,ensure_ascii=False))\n'
    )


def _target_program(
    index: int, expect_role: str, expect_name: str, action_code: str, standing: str
) -> str:
    if index < 0 or index >= MAX_OBSERVE_ELEMENTS:
        raise ValueError(f"index must be between 0 and {MAX_OBSERVE_ELEMENTS - 1}")
    if expect_role not in ACTION_ROLES:
        raise ValueError("expect-role is not an actionable role")
    expect_name = _validate_text(expect_name, "expect-name")
    return (
        "import json\n" + _affordance_prelude() + f"rows=_ordivon_affordances()\nidx={index}\n"
        'assert idx < len(rows), {"error":"affordance-index-out-of-range","count":len(rows)}\n'
        "row=rows[idx]\n"
        f"assert row['role']=={json.dumps(expect_role)} and row['name']=={json.dumps(expect_name)}, "
        "{'error':'affordance-changed','observed':{'role':row['role'],'name':row['name']}}\n"
        "assert row['x'] is not None and row['y'] is not None, {'error':'affordance-has-no-box'}\n"
        + action_code
        + f'print(json.dumps({{"standing":{json.dumps(standing)},"target":{{"index":idx,"role":row["role"],"name":row["name"]}},"pageAfter":_ordivon_page_info()}},sort_keys=True,ensure_ascii=False))\n'
    )


def program_click(index: int, expect_role: str, expect_name: str) -> str:
    return _target_program(
        index, expect_role, expect_name, 'click_at_xy(row["x"],row["y"])\nwait(0.25)\n', "CLICKED"
    )


def program_input(index: int, expect_role: str, expect_name: str, text: str) -> str:
    text = _validate_text(text, "text")
    code = (
        'click_at_xy(row["x"],row["y"])\n'
        'press_key("a",modifiers=2)\npress_key("Backspace")\n'
        f"type_text({json.dumps(text)})\nwait(0.25)\n"
    )
    return _target_program(index, expect_role, expect_name, code, "INPUT")


def program_scroll(dy: int) -> str:
    if dy < -20_000 or dy > 20_000 or dy == 0:
        raise ValueError("dy must be a non-zero integer within [-20000,20000]")
    return (
        "import json\ninfo=page_info()\n"
        f"scroll(info['w']/2,info['h']/2,dy={dy})\nwait(0.25)\n"
        'print(json.dumps({"standing":"SCROLLED","pageAfter":page_info()},sort_keys=True))\n'
    )


def program_back() -> str:
    return (
        "import json\n"
        'hist=cdp("Page.getNavigationHistory")\nidx=hist.get("currentIndex",0)\nentries=hist.get("entries",[])\n'
        'assert idx>0, {"error":"no-back-history"}\n'
        'cdp("Page.navigateToHistoryEntry",entryId=entries[idx-1]["id"])\nwait_for_load()\n'
        'print(json.dumps({"standing":"BACK","pageAfter":page_info()},sort_keys=True))\n'
    )


def program_tabs() -> str:
    return 'import json\nprint(json.dumps({"standing":"TABS","tabs":list_tabs(include_chrome=False),"current":current_tab()},sort_keys=True))\n'


def close_session(executable: str, endpoint, session_id: str) -> dict:
    proc = subprocess.run(
        [executable, "--reload"],
        text=True,
        capture_output=True,
        env=browser_env(endpoint, session_id, include_cdp=False),
        timeout=30,
        check=False,
    )
    lifecycle = (
        endpoint.release_if_idle()
        if proc.returncode == 0 and getattr(endpoint, "idle_stop_units", ())
        else {"standing": "NOT_EVALUATED", "stoppedUnits": []}
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-use-session-close",
        "sessionId": session_id,
        "browserlessEndpointId": endpoint.endpoint_id,
        "standing": "CLOSED" if proc.returncode == 0 else "HOLD",
        "returnCode": proc.returncode,
        "lifecycle": lifecycle,
    }


def doctor(executable: str, endpoint, session_id: str) -> dict:
    version = subprocess.run(
        [executable, "--version"], capture_output=True, text=True, timeout=10, check=False
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-use-browserless-doctor",
        "browserUseCliVersion": version.stdout.strip() if version.returncode == 0 else None,
        "browserlessEndpointId": endpoint.endpoint_id,
        "browserlessHealth": endpoint.health(),
        "activeBrowserlessSessions": len(endpoint.sessions()),
        "sessionNameDigest": "sha256:"
        + hashlib.sha256(session_name(session_id).encode()).hexdigest(),
        "credentialsExposed": False,
        "arbitraryPythonExposed": False,
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--session-id", required=True)
    p.add_argument("--endpoint-id")
    sub = p.add_subparsers(dest="operation", required=True)
    op = sub.add_parser("open")
    op.add_argument("--url", required=True)
    obs = sub.add_parser("observe")
    obs.add_argument("--include-text", action="store_true")
    obs.add_argument("--max-chars", type=int, default=6000)
    click = sub.add_parser("click")
    click.add_argument("--index", type=int, required=True)
    click.add_argument("--expect-role", required=True)
    click.add_argument("--expect-name", required=True)
    inp = sub.add_parser("input")
    inp.add_argument("--index", type=int, required=True)
    inp.add_argument("--expect-role", required=True)
    inp.add_argument("--expect-name", required=True)
    inp.add_argument("--text", required=True)
    scr = sub.add_parser("scroll")
    scr.add_argument("--dy", type=int, required=True)
    sub.add_parser("back")
    sub.add_parser("tabs")
    sub.add_parser("close")
    sub.add_parser("doctor")
    return p


def main() -> int:
    a = parser().parse_args()
    value, pool = load_config(a.config)
    executable = str(value.get("browserUseExecutable") or "")
    if not executable.startswith("/") or not Path(executable).is_file():
        raise SystemExit("configured Browser Use executable is unavailable")
    endpoint = select_endpoint(pool, a.session_id, a.endpoint_id)
    if a.operation == "close":
        print(json.dumps(close_session(executable, endpoint, a.session_id), sort_keys=True))
        return 0
    if a.operation == "doctor":
        print(json.dumps(doctor(executable, endpoint, a.session_id), sort_keys=True))
        return 0
    programs = {
        "open": lambda: program_open(a.url),
        "observe": lambda: program_observe(include_text=a.include_text, max_chars=a.max_chars),
        "click": lambda: program_click(a.index, a.expect_role, a.expect_name),
        "input": lambda: program_input(a.index, a.expect_role, a.expect_name, a.text),
        "scroll": lambda: program_scroll(a.dy),
        "back": program_back,
        "tabs": program_tabs,
    }
    return _execute_generated(executable, endpoint, a.session_id, programs[a.operation]())


if __name__ == "__main__":
    raise SystemExit(main())
