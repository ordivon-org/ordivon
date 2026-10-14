from __future__ import annotations
from pathlib import Path
import os, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]/"capabilities/gluetun/m4-source"
SCRIPT=ROOT/"m4-owned-restore-legacy"

PODMAN="""#!/bin/sh
if test "$1" = container && test "$2" = exists; then
 case "$FAKE_CANDIDATE" in absent) exit 1;; present) exit 0;; unknown) exit 125;; esac
fi
if test "$1" = rm; then test "$FAKE_RM_OK" = 1; exit $?; fi
exit 125
"""
SYSTEMCTL="""#!/bin/sh
echo "$*" >>"$FAKE_LOG"
if test "$1" = is-active; then
 test "$3" != "network-v2-gluetun-owned.service"; exit $?
fi
case "$1" in stop|disable|enable|start) exit 0;; esac
exit 125
"""

def exercise(candidate="absent",rm_ok="0"):
    with tempfile.TemporaryDirectory() as t:
        p=Path(t); b=p/"bin"; b.mkdir()
        for n,body in (("podman",PODMAN),("systemctl",SYSTEMCTL)):
            f=b/n; f.write_text(body); f.chmod(0o755)
        log=p/"log";log.write_text("")
        env={**os.environ,"PATH":str(b)+":"+os.environ["PATH"],"FAKE_CANDIDATE":candidate,"FAKE_RM_OK":rm_ok,"FAKE_LOG":str(log),"M4_RESTORE_LOCK":str(p/"lock"),"M4_READY_CHECK":"/bin/true","M4_PATH_CHECK":"/bin/true"}
        r=subprocess.run(["/usr/bin/bash",str(SCRIPT)],env=env,text=True,capture_output=True,timeout=8,check=False)
        return r,log.read_text()

def test_uncertain_candidate_never_starts_legacy():
    r,c=exercise("unknown"); assert r.returncode==70; assert " start " not in " "+c

def test_failed_candidate_removal_never_starts_legacy():
    r,c=exercise("present","0"); assert r.returncode==70; assert " start " not in " "+c

def test_absent_candidate_switches_boot_mode_then_starts_fallback():
    r,c=exercise("absent"); assert r.returncode==0,(r.stdout,r.stderr)
    assert "M4_LEGACY_FALLBACK_FULL_READY" in r.stdout
    lines=c.splitlines()
    assert "disable network-v2-gluetun-owned.target" in lines
    assert "enable network-v2-browserless-legacy-provider.target" in lines
    assert "start network-v2-browserless.target" in lines
    assert "start network-v2-browserless-legacy-provider.target" in lines

def test_quadlet_generator_accepts_owned_source_without_install_effect():
    env={**os.environ,"QUADLET_UNIT_DIRS":str(ROOT)}
    r=subprocess.run(["/usr/lib/systemd/system-generators/podman-system-generator","--dryrun"],env=env,text=True,capture_output=True,timeout=12,check=False)
    assert r.returncode==0,r.stderr
    assert "--publish 10.252.246.1:19682:8888/tcp" in r.stdout
    assert "--pull never" in r.stdout
