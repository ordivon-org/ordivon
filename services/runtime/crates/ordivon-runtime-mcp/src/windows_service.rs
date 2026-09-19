use std::ffi::c_void;
use std::io;
use std::net::SocketAddr;
use std::ptr::null_mut;
use std::sync::atomic::{AtomicU32, AtomicUsize, Ordering};
use std::sync::OnceLock;

use tokio_util::sync::CancellationToken;
use windows_sys::Win32::System::Services::{
    RegisterServiceCtrlHandlerExW, SetServiceStatus, StartServiceCtrlDispatcherW,
    SERVICE_ACCEPT_SHUTDOWN, SERVICE_ACCEPT_STOP, SERVICE_CONTROL_INTERROGATE,
    SERVICE_CONTROL_SHUTDOWN, SERVICE_CONTROL_STOP, SERVICE_RUNNING, SERVICE_START_PENDING,
    SERVICE_STATUS, SERVICE_STATUS_HANDLE, SERVICE_STOPPED, SERVICE_STOP_PENDING,
    SERVICE_TABLE_ENTRYW, SERVICE_WIN32_OWN_PROCESS,
};

pub(crate) const SERVICE_NAME: &str = "OrdivonRuntime";

pub(crate) fn requested() -> bool {
    std::env::args_os()
        .skip(1)
        .any(|argument| argument == "--windows-service")
}
const START_WAIT_HINT_MS: u32 = 15_000;
const STOP_WAIT_HINT_MS: u32 = 30_000;

static STATUS_HANDLE: AtomicUsize = AtomicUsize::new(0);
static CURRENT_STATE: AtomicU32 = AtomicU32::new(SERVICE_STOPPED);
static CURRENT_CONTROLS: AtomicU32 = AtomicU32::new(0);
static CURRENT_CHECKPOINT: AtomicU32 = AtomicU32::new(0);
static SERVICE_CANCELLATION: OnceLock<CancellationToken> = OnceLock::new();

pub(crate) fn dispatch() -> io::Result<()> {
    let mut service_name = wide(SERVICE_NAME);
    let table = [
        SERVICE_TABLE_ENTRYW {
            lpServiceName: service_name.as_mut_ptr(),
            lpServiceProc: Some(service_main),
        },
        SERVICE_TABLE_ENTRYW {
            lpServiceName: null_mut(),
            lpServiceProc: None,
        },
    ];
    let ok = unsafe { StartServiceCtrlDispatcherW(table.as_ptr()) };
    if ok == 0 {
        return Err(io::Error::last_os_error());
    }
    Ok(())
}

pub(crate) fn report_running(_address: SocketAddr) {
    let _ = report_status(
        SERVICE_RUNNING,
        SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN,
        0,
        0,
        0,
    );
}

unsafe extern "system" fn service_main(_argc: u32, _argv: *mut *mut u16) {
    let mut service_name = wide(SERVICE_NAME);
    let handle = RegisterServiceCtrlHandlerExW(
        service_name.as_mut_ptr(),
        Some(service_control_handler),
        null_mut(),
    );
    if handle.is_null() {
        return;
    }
    STATUS_HANDLE.store(handle as usize, Ordering::Release);
    let _ = report_status(SERVICE_START_PENDING, 0, 0, 1, START_WAIT_HINT_MS);

    let cancellation = CancellationToken::new();
    if SERVICE_CANCELLATION.set(cancellation.clone()).is_err() {
        let _ = report_status(SERVICE_STOPPED, 0, 1, 0, 0);
        return;
    }

    let runtime = match tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
    {
        Ok(runtime) => runtime,
        Err(error) => {
            tracing::error!(%error, "cannot construct native Windows service runtime");
            let _ = report_status(SERVICE_STOPPED, 0, 1, 0, 0);
            return;
        }
    };

    let result = runtime.block_on(crate::run_runtime_server(
        cancellation,
        false,
        Some(report_running),
    ));
    match result {
        Ok(()) => {
            let _ = report_status(SERVICE_STOPPED, 0, 0, 0, 0);
        }
        Err(error) => {
            tracing::error!(%error, "native Windows Runtime service failed");
            let _ = report_status(SERVICE_STOPPED, 0, 1, 0, 0);
        }
    }
}

unsafe extern "system" fn service_control_handler(
    control: u32,
    _event_type: u32,
    _event_data: *mut c_void,
    _context: *mut c_void,
) -> u32 {
    match control {
        SERVICE_CONTROL_STOP | SERVICE_CONTROL_SHUTDOWN => {
            let _ = report_status(SERVICE_STOP_PENDING, 0, 0, 1, STOP_WAIT_HINT_MS);
            if let Some(cancellation) = SERVICE_CANCELLATION.get() {
                cancellation.cancel();
            }
            0
        }
        SERVICE_CONTROL_INTERROGATE => {
            let _ = report_current_status();
            0
        }
        _ => 0,
    }
}

fn report_current_status() -> io::Result<()> {
    report_status(
        CURRENT_STATE.load(Ordering::Acquire),
        CURRENT_CONTROLS.load(Ordering::Acquire),
        0,
        CURRENT_CHECKPOINT.load(Ordering::Acquire),
        0,
    )
}

fn report_status(
    state: u32,
    controls: u32,
    service_specific_exit: u32,
    checkpoint: u32,
    wait_hint: u32,
) -> io::Result<()> {
    let raw = STATUS_HANDLE.load(Ordering::Acquire);
    if raw == 0 {
        return Err(io::Error::new(
            io::ErrorKind::NotConnected,
            "SCM service status handle is unavailable",
        ));
    }
    let handle = raw as SERVICE_STATUS_HANDLE;
    let status = SERVICE_STATUS {
        dwServiceType: SERVICE_WIN32_OWN_PROCESS,
        dwCurrentState: state,
        dwControlsAccepted: controls,
        dwWin32ExitCode: if service_specific_exit == 0 { 0 } else { 1066 },
        dwServiceSpecificExitCode: service_specific_exit,
        dwCheckPoint: checkpoint,
        dwWaitHint: wait_hint,
    };
    let ok = unsafe { SetServiceStatus(handle, &status) };
    if ok == 0 {
        return Err(io::Error::last_os_error());
    }
    CURRENT_STATE.store(state, Ordering::Release);
    CURRENT_CONTROLS.store(controls, Ordering::Release);
    CURRENT_CHECKPOINT.store(checkpoint, Ordering::Release);
    Ok(())
}

fn wide(value: &str) -> Vec<u16> {
    value.encode_utf16().chain(std::iter::once(0)).collect()
}
