from pathlib import Path
import os
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT/'capabilities/gluetun/acceptance/m3b-restore-helpers.sh'

PODMAN='''#!/usr/bin/env bash
case "$1 $2" in
  "container exists")
    case "${FAKE_EXISTS:-absent}" in present) exit 0;; absent) exit 1;; *) exit 125;; esac;;
  "rm -f")
    test "${FAKE_RM_OK:-0}" = 1 && exit 0 || exit 125;;
esac
exit 125
'''
SYSTEMCTL='''#!/usr/bin/env bash
case "$1" in
  start) test "${FAKE_START_OK:-0}" = 1;;
  is-active) test "${FAKE_ACTIVE:-0}" = 1;;
  *) exit 1;;
esac
'''

def run(shell, env_extra):
    with tempfile.TemporaryDirectory() as td:
        for name,body in [('podman',PODMAN),('systemctl',SYSTEMCTL)]:
            p=Path(td)/name;p.write_text(body);p.chmod(0o755)
        env=os.environ.copy();env.update(env_extra);env['PATH']=td+os.pathsep+env['PATH']
        return subprocess.run(['/bin/bash','-c',f'source {HELPER!s}; {shell}'],
                              text=True,capture_output=True,env=env,check=False,timeout=10)

def test_candidate_removal_failure_is_not_treated_as_absence():
    r=run('m3b_candidate_teardown candidate',{'FAKE_EXISTS':'present','FAKE_RM_OK':'0'})
    assert r.returncode != 0

def test_unknown_podman_state_fails_closed():
    r=run('m3b_candidate_teardown candidate',{'FAKE_EXISTS':'unknown'})
    assert r.returncode != 0

def test_absent_candidate_is_safe():
    r=run('m3b_candidate_teardown candidate',{'FAKE_EXISTS':'absent'})
    assert r.returncode == 0,r.stderr

def test_required_unit_must_start_and_read_back_active():
    assert run('m3b_start_required_unit u',{'FAKE_START_OK':'0','FAKE_ACTIVE':'0'}).returncode != 0
    assert run('m3b_start_required_unit u',{'FAKE_START_OK':'1','FAKE_ACTIVE':'0'}).returncode != 0
    assert run('m3b_start_required_unit u',{'FAKE_START_OK':'1','FAKE_ACTIVE':'1'}).returncode == 0

def test_actual_restore_function_never_starts_legacy_when_candidate_teardown_is_unknown():
    source=(ROOT/'capabilities/gluetun/acceptance/m3b-serialized-canary.sh').read_text()
    begin=source.index('restore() {')
    end=source.index('\ntrap restore EXIT ERR INT TERM',begin)
    restore_fn=source[begin:end]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        bindir=td/'bin';bindir.mkdir()
        log=td/'systemctl.log';log.write_text('')
        podman=bindir/'podman'
        podman.write_text('''#!/usr/bin/env bash
case "$1 $2" in
  "container exists") exit 0;;
  "rm -f") exit 125;;
  "logs --tail") exit 0;;
esac
exit 0
''');podman.chmod(0o755)
        systemctl=bindir/'systemctl'
        systemctl.write_text('''#!/usr/bin/env bash
echo "$*" >>"$FAKE_SYSTEMCTL_LOG"
case "$1" in is-active) exit 0;; start) exit 0;; esac
exit 0
''');systemctl.chmod(0o755)
        state=td/'state';state.mkdir()
        profile=td/'profile';profile.write_text('profile')
        envfile=td/'provider.env';envfile.write_text('env')
        (state/'profile.preimage').write_text('profile')
        (state/'provider.env.preimage').write_text('env')
        (state/'active-consumers.txt').write_text('')
        ok=td/'ok';ok.write_text('#!/usr/bin/env bash\nexit 0\n');ok.chmod(0o755)
        import hashlib
        psha=hashlib.sha256(profile.read_bytes()).hexdigest()
        esha=hashlib.sha256(envfile.read_bytes()).hexdigest()
        harness=f'''set -u
source {HELPER}
watchdog_pid=; adapter_pid=; CTR=candidate; candidate_pass=0; network_created=1; restore_failed=0
state={state}; PROFILE={profile}; PROVIDER_ENV={envfile}; profile_sha={psha}; env_sha={esha}
NS=not-used; ns_inode=1; WG=legacy-wg; DNS=legacy-dns; CARRIER=legacy-carrier; TARGET=legacy-target
LEGACY_READY={ok}; LEGACY_PATH={ok}; CONSEQUENCE={ok}; WORKER=worker; MCP=mcp
worker_was_active=1; mcp_was_active=1; imageDigest=x; SOURCE_HEAD=x; SCRIPT_SHA=x; digest=x
{restore_fn}
restore
'''
        env=os.environ.copy();env['PATH']=str(bindir)+os.pathsep+env['PATH'];env['FAKE_SYSTEMCTL_LOG']=str(log)
        r=subprocess.run(['/bin/bash','-c',harness],text=True,capture_output=True,env=env,check=False,timeout=10)
        assert r.returncode == 70,(r.stdout,r.stderr)
        assert 'BLOCKED_ROLLBACK' in r.stderr
        assert 'legacy will remain stopped' in r.stderr
        assert log.read_text() == ''
        assert (state/'profile.preimage').exists()
        assert (state/'provider.env.preimage').exists()

def test_actual_restore_preserves_preimage_if_previously_active_producer_cannot_restart():
    source=(ROOT/'capabilities/gluetun/acceptance/m3b-serialized-canary.sh').read_text()
    begin=source.index('restore() {')
    end=source.index('\ntrap restore EXIT ERR INT TERM',begin)
    restore_fn=source[begin:end]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        bindir=td/'bin';bindir.mkdir()
        log=td/'systemctl.log';log.write_text('')
        podman=bindir/'podman'
        podman.write_text('#!/usr/bin/env bash\ncase "$1 $2" in "container exists") exit 1;; esac\nexit 0\n')
        podman.chmod(0o755)
        systemctl=bindir/'systemctl'
        systemctl.write_text('#!/usr/bin/env bash\nif test "$1" = start; then echo "$*" >>"$FAKE_SYSTEMCTL_LOG"; test "$2" = "$FAIL_UNIT" && exit 1; exit 0; fi\nif test "$1" = is-active; then exit 0; fi\nexit 1\n')
        systemctl.chmod(0o755)
        state=td/'state';state.mkdir();(state/'active-consumers.txt').write_text('')
        profile=td/'profile';profile.write_text('profile')
        envfile=td/'env';envfile.write_text('env')
        (state/'profile.preimage').write_text('profile')
        (state/'provider.env.preimage').write_text('env')
        ok=td/'ok';ok.write_text('#!/usr/bin/env bash\nexit 0\n');ok.chmod(0o755)
        import hashlib
        psha=hashlib.sha256(profile.read_bytes()).hexdigest()
        esha=hashlib.sha256(envfile.read_bytes()).hexdigest()
        ns='nv2-browserless-prod'; inode=os.stat('/run/netns/'+ns).st_ino
        harness=('set -u\n'
                 f'source {HELPER}\n'
                 'watchdog_pid=; adapter_pid=; CTR=candidate; candidate_pass=0; network_created=0; restore_failed=0\n'
                 f'state={state}; PROFILE={profile}; PROVIDER_ENV={envfile}; profile_sha={psha}; env_sha={esha}\n'
                 f'NS={ns}; ns_inode={inode}; WG=legacy-wg; DNS=legacy-dns; CARRIER=legacy-carrier; TARGET=legacy-target\n'
                 f'LEGACY_READY={ok}; LEGACY_PATH={ok}; CONSEQUENCE={ok}; WORKER=worker; MCP=mcp\n'
                 'worker_was_active=1; mcp_was_active=1; SOURCE_HEAD=x; SCRIPT_SHA=x; digest=x\n'
                 + restore_fn + '\nrestore\n')
        env=os.environ.copy()
        env.update({'PATH':str(bindir)+os.pathsep+env['PATH'],'FAKE_SYSTEMCTL_LOG':str(log),'FAIL_UNIT':'worker'})
        r=subprocess.run(['/bin/bash','-c',harness],text=True,capture_output=True,env=env,check=False,timeout=10)
        assert r.returncode==70,(r.stdout,r.stderr)
        assert 'BLOCKED_ROLLBACK' in r.stderr
        assert (state/'profile.preimage').exists() and (state/'provider.env.preimage').exists()
        starts=log.read_text()
        assert 'start legacy-wg' in starts and 'start worker' in starts
        assert 'start mcp' not in starts
