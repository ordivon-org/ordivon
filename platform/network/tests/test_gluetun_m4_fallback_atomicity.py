from pathlib import Path
import os,subprocess,tempfile

ROOT=Path(__file__).resolve().parents[1]/"capabilities/gluetun/m4-source"
SELECTOR="/etc/network-v2/gluetun/m4-owned-mode.selected"

def test_legacy_boot_target_is_inverse_of_owned_mode_selector():
    owned=(ROOT/"network-v2-gluetun-owned.target").read_text()
    legacy=(ROOT/"network-v2-browserless-legacy-provider.target").read_text()
    assert f"ConditionPathExists={SELECTOR}" in owned
    assert f"ConditionPathExists=!{SELECTOR}" in legacy
    assert "WantedBy=multi-user.target" in legacy

def test_fallback_uses_testable_root_mode_marker_and_pre_enables_legacy():
    s=(ROOT/"m4-owned-restore-legacy").read_text()
    assert "M4_PROVIDER_MODE_MARKER" in s
    assert 'systemctl enable "$LEGACY_TARGET"' in s
    assert 'rm -f "$MARKER"' in s
    assert s.index('systemctl enable "$LEGACY_TARGET"') < s.index('rm -f "$MARKER"')

PODMAN='''#!/bin/sh
if test "$1" = container && test "$2" = exists; then exit 1; fi
exit 125
'''
SYSTEMCTL='''#!/bin/sh
if test -e "$M4_PROVIDER_MODE_MARKER"; then selected=1; else selected=0; fi
printf '%s | mode=%s\\n' "$*" "$selected" >>"$FAKE_SYSTEMCTL_LOG"
if test "$1" = is-active; then
 test "$3" != network-v2-gluetun-owned.service; exit $?
fi
if test "$1" = enable && test "$FAIL_LEGACY_ENABLE" = 1; then exit 73; fi
case "$1" in stop|disable|enable|start) exit 0;; esac
exit 125
'''

def run_with_fault(enable_fail):
    with tempfile.TemporaryDirectory() as t:
        p=Path(t);b=p/"bin";b.mkdir()
        for n,body in (("podman",PODMAN),("systemctl",SYSTEMCTL)):
            f=b/n;f.write_text(body);f.chmod(0o755)
        selector=p/"selected"; selector.write_text("owned")
        calls=p/"log"; calls.write_text("")
        env={**os.environ,"PATH":str(b)+":"+os.environ["PATH"],
             "M4_PROVIDER_MODE_MARKER":str(selector),"M4_RESTORE_LOCK":str(p/"lock"),
             "M4_READY_CHECK":"/bin/true","M4_PATH_CHECK":"/bin/true",
             "FAKE_SYSTEMCTL_LOG":str(calls),"FAIL_LEGACY_ENABLE":str(int(enable_fail))}
        r=subprocess.run(["/usr/bin/bash",str(ROOT/"m4-owned-restore-legacy")],
                         env=env,text=True,capture_output=True,check=False,timeout=10)
        return r,selector.exists(),calls.read_text()

def test_failed_enable_does_not_erase_current_owned_boot_choice():
    r,present,calls=run_with_fault(True)
    assert r.returncode!=0
    assert present
    assert "enable network-v2-browserless-legacy-provider.target | mode=1" in calls
    assert "start network-v2-browserless-legacy-provider.target" not in calls

def test_success_switches_boot_choice_only_after_enable():
    r,present,calls=run_with_fault(False)
    assert r.returncode==0,(r.stdout,r.stderr)
    assert not present
    assert "enable network-v2-browserless-legacy-provider.target | mode=1" in calls
    assert "start network-v2-browserless-legacy-provider.target | mode=0" in calls
