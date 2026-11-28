//! Read-only native ownership observation for PG RUNNER_BOUND.
//! Job object membership is checked using the SAME live process handles
//! whose creation FILETIMEs were qualified, never from a bare PID.
use super::{
    same_win32_owner, PgWindowsWitnessIdentity, PgWindowsWitnessObservation, PgWindowsWitnessPhase,
};
use std::os::windows::io::{AsRawHandle, FromRawHandle, OwnedHandle};
use windows_sys::Win32::{
    Foundation::FILETIME,
    System::{
        JobObjects::{IsProcessInJob, OpenJobObjectW},
        Threading::{
            GetProcessTimes, OpenProcess, WaitForSingleObject, PROCESS_QUERY_LIMITED_INFORMATION,
        },
    },
};

const SYNCHRONIZE: u32 = 0x0010_0000;
const JOB_OBJECT_QUERY: u32 = 0x0004;
const WAIT_TIMEOUT: u32 = 258;

fn live(handle: &OwnedHandle) -> bool {
    unsafe { WaitForSingleObject(handle.as_raw_handle(), 0) == WAIT_TIMEOUT }
}

fn exact_live_process(pid: u64, birth: u64) -> Option<OwnedHandle> {
    if pid == 0 || birth == 0 {
        return None;
    }
    let raw = unsafe {
        OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE,
            0,
            u32::try_from(pid).ok()?,
        )
    };
    if raw.is_null() {
        return None;
    }
    let handle = unsafe { OwnedHandle::from_raw_handle(raw) };
    let blank = FILETIME {
        dwLowDateTime: 0,
        dwHighDateTime: 0,
    };
    let (mut creation, mut exit, mut kernel, mut user) = (blank, blank, blank, blank);
    let ok = unsafe {
        GetProcessTimes(
            handle.as_raw_handle(),
            &mut creation,
            &mut exit,
            &mut kernel,
            &mut user,
        )
    };
    let actual = ((creation.dwHighDateTime as u64) << 32) | creation.dwLowDateTime as u64;
    (ok != 0 && same_win32_owner(pid, birth, pid, actual) && live(&handle)).then_some(handle)
}

pub(super) fn observe_owned_target(
    expected: &PgWindowsWitnessIdentity,
    witness: &PgWindowsWitnessObservation,
) -> Option<String> {
    if witness.phase != PgWindowsWitnessPhase::TargetWitness
        || witness.admitted_job_object_name != format!("Ordivon.{}", expected.attempt_id)
    {
        return None;
    }
    let (launcher_pid, launcher_birth) = (
        witness.launcher_process_id?,
        witness.launcher_creation_file_time?,
    );
    let (target_pid, target_birth) = (
        witness.target_process_id?,
        witness.target_creation_file_time?,
    );
    if launcher_pid == target_pid {
        return None;
    }
    let launcher = exact_live_process(launcher_pid, launcher_birth)?;
    let target = exact_live_process(target_pid, target_birth)?;
    let name: Vec<u16> = witness
        .admitted_job_object_name
        .encode_utf16()
        .chain(Some(0))
        .collect();
    let raw = unsafe { OpenJobObjectW(JOB_OBJECT_QUERY, 0, name.as_ptr()) };
    if raw.is_null() {
        return None;
    }
    let job = unsafe { OwnedHandle::from_raw_handle(raw) };
    let mut member = 0;
    let matched =
        unsafe { IsProcessInJob(target.as_raw_handle(), job.as_raw_handle(), &mut member) };
    if matched == 0 || member == 0 || !live(&launcher) || !live(&target) {
        return None;
    }
    Some(format!(
        "windows-launcher:{launcher_pid}:{launcher_birth}:{}",
        expected.attempt_id
    ))
}
