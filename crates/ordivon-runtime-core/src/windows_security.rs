use std::ffi::c_void;
use std::io;
use std::os::windows::ffi::OsStrExt;
use std::path::Path;
use std::ptr::{null, null_mut};

use windows_sys::Win32::Foundation::{CloseHandle, LocalFree, HANDLE};
use windows_sys::Win32::Security::Authorization::{
    GetExplicitEntriesFromAclW, GetNamedSecurityInfoW, SetEntriesInAclW, SetNamedSecurityInfoW,
    EXPLICIT_ACCESS_W, GRANT_ACCESS, SET_ACCESS, SE_FILE_OBJECT, TRUSTEE_IS_SID,
    TRUSTEE_IS_UNKNOWN, TRUSTEE_W,
};
use windows_sys::Win32::Security::{
    CreateWellKnownSid, EqualSid, GetSecurityDescriptorControl, GetTokenInformation, TokenUser,
    WinBuiltinAdministratorsSid, WinLocalSystemSid, DACL_SECURITY_INFORMATION, NO_INHERITANCE,
    PROTECTED_DACL_SECURITY_INFORMATION, SECURITY_MAX_SID_SIZE, SE_DACL_PROTECTED,
    SUB_CONTAINERS_AND_OBJECTS_INHERIT, TOKEN_QUERY, TOKEN_USER,
};
use windows_sys::Win32::Storage::FileSystem::{FILE_ALL_ACCESS, FILE_GENERIC_READ};
use windows_sys::Win32::System::Threading::{GetCurrentProcess, OpenProcessToken};

pub(crate) fn protect_private_directory(path: &Path) -> io::Result<()> {
    protect_private_path(path, true)
}

pub(crate) fn protect_private_file(path: &Path) -> io::Result<()> {
    protect_private_path(path, false)
}

/// Validate a private configuration/secret file that the Runtime identity may read but not write.
pub fn validate_private_readonly_file_acl(path: &Path) -> io::Result<()> {
    validate_private_file_acl_with_principal_access(path, PrincipalAccess::ReadOnly)
}

pub fn current_token_is_local_system() -> io::Result<bool> {
    let mut current = CurrentTokenUserSid::load()?;
    let mut system = WellKnownSid::new(WinLocalSystemSid)?;
    Ok(unsafe { EqualSid(current.as_mut_ptr(), system.as_mut_ptr()) } != 0)
}

#[derive(Clone, Copy)]
enum PrincipalAccess {
    ReadOnly,
}

fn validate_private_file_acl_with_principal_access(
    path: &Path,
    principal_access: PrincipalAccess,
) -> io::Result<()> {
    let mut system = WellKnownSid::new(WinLocalSystemSid)?;
    let mut administrators = WellKnownSid::new(WinBuiltinAdministratorsSid)?;
    let mut principal = CurrentTokenUserSid::load()?;
    let allowed = [
        system.as_mut_ptr(),
        administrators.as_mut_ptr(),
        principal.as_mut_ptr(),
    ];

    let mut wide = path.as_os_str().encode_wide().collect::<Vec<_>>();
    wide.push(0);

    let mut dacl = null_mut();
    let mut descriptor = null_mut();
    let result = unsafe {
        GetNamedSecurityInfoW(
            wide.as_mut_ptr(),
            SE_FILE_OBJECT,
            DACL_SECURITY_INFORMATION,
            null_mut(),
            null_mut(),
            &mut dacl,
            null_mut(),
            &mut descriptor,
        )
    };
    if result != 0 {
        return Err(io::Error::from_raw_os_error(result as i32));
    }
    let _descriptor = LocalAcl(descriptor.cast());
    if dacl.is_null() {
        return Err(io::Error::new(
            io::ErrorKind::PermissionDenied,
            "private Windows file has no DACL",
        ));
    }

    let mut control = 0_u16;
    let mut revision = 0_u32;
    let ok = unsafe { GetSecurityDescriptorControl(descriptor, &mut control, &mut revision) };
    if ok == 0 {
        return Err(io::Error::last_os_error());
    }
    if control & SE_DACL_PROTECTED == 0 {
        return Err(io::Error::new(
            io::ErrorKind::PermissionDenied,
            "private Windows file DACL inherits from its parent",
        ));
    }

    let mut count = 0_u32;
    let mut entries = null_mut();
    let result = unsafe { GetExplicitEntriesFromAclW(dacl, &mut count, &mut entries) };
    if result != 0 {
        return Err(io::Error::from_raw_os_error(result as i32));
    }
    let _entries = LocalAcl(entries.cast());
    if entries.is_null() || count == 0 {
        return Err(io::Error::new(
            io::ErrorKind::PermissionDenied,
            "private Windows file has no explicit access entries",
        ));
    }

    let slice = unsafe { std::slice::from_raw_parts(entries, count as usize) };
    let mut observed_allowed = [false; 3];
    for entry in slice {
        if entry.Trustee.TrusteeForm != TRUSTEE_IS_SID || entry.Trustee.ptstrName.is_null() {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                "private Windows file ACL contains a non-SID trustee",
            ));
        }
        if !matches!(entry.grfAccessMode, SET_ACCESS | GRANT_ACCESS) {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                "private Windows file ACL contains a non-allow entry",
            ));
        }

        let sid = entry.Trustee.ptstrName.cast();
        let matched_index = allowed
            .iter()
            .position(|candidate| unsafe { EqualSid(sid, *candidate) } != 0)
            .ok_or_else(|| {
                io::Error::new(
                    io::ErrorKind::PermissionDenied,
                    "private Windows file ACL grants access to an unexpected principal",
                )
            })?;

        let required = if matched_index < 2 {
            FILE_ALL_ACCESS
        } else {
            match principal_access {
                PrincipalAccess::ReadOnly => FILE_GENERIC_READ,
            }
        };
        if entry.grfAccessPermissions != required {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                format!(
                    "private Windows file ACL principal {matched_index} has unexpected access mask 0x{:08x}, expected 0x{required:08x}",
                    entry.grfAccessPermissions
                ),
            ));
        }
        observed_allowed[matched_index] = true;
    }

    // Current identity can legitimately be SYSTEM. Require each distinct effective SID, not
    // three syntactically separate ACEs.
    for index in 0..allowed.len() {
        let duplicate_of_earlier =
            (0..index).any(|prior| unsafe { EqualSid(allowed[index], allowed[prior]) != 0 });
        if !duplicate_of_earlier && !observed_allowed[index] {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                "private Windows file ACL omits a required Runtime principal",
            ));
        }
    }
    Ok(())
}

fn protect_private_path(path: &Path, directory: bool) -> io::Result<()> {
    let mut system = WellKnownSid::new(WinLocalSystemSid)?;
    let mut administrators = WellKnownSid::new(WinBuiltinAdministratorsSid)?;
    let mut principal = CurrentTokenUserSid::load()?;
    let inheritance = if directory {
        SUB_CONTAINERS_AND_OBJECTS_INHERIT
    } else {
        NO_INHERITANCE
    };
    let entries = [
        explicit_full_control(system.as_mut_ptr(), inheritance),
        explicit_full_control(administrators.as_mut_ptr(), inheritance),
        explicit_full_control(principal.as_mut_ptr(), inheritance),
    ];
    let mut acl = null_mut();
    let result =
        unsafe { SetEntriesInAclW(entries.len() as u32, entries.as_ptr(), null(), &mut acl) };
    if result != 0 {
        return Err(io::Error::from_raw_os_error(result as i32));
    }
    let _acl = LocalAcl(acl.cast());

    let mut wide = path.as_os_str().encode_wide().collect::<Vec<_>>();
    wide.push(0);
    let result = unsafe {
        SetNamedSecurityInfoW(
            wide.as_mut_ptr(),
            SE_FILE_OBJECT,
            DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION,
            null_mut(),
            null_mut(),
            acl,
            null(),
        )
    };
    if result != 0 {
        return Err(io::Error::from_raw_os_error(result as i32));
    }
    Ok(())
}

fn explicit_full_control(
    sid: windows_sys::Win32::Security::PSID,
    inheritance: u32,
) -> EXPLICIT_ACCESS_W {
    EXPLICIT_ACCESS_W {
        grfAccessPermissions: FILE_ALL_ACCESS,
        grfAccessMode: SET_ACCESS,
        grfInheritance: inheritance,
        Trustee: TRUSTEE_W {
            pMultipleTrustee: null_mut(),
            MultipleTrusteeOperation: 0,
            TrusteeForm: TRUSTEE_IS_SID,
            TrusteeType: TRUSTEE_IS_UNKNOWN,
            ptstrName: sid.cast(),
        },
    }
}

struct WellKnownSid {
    storage: Vec<u8>,
}

impl WellKnownSid {
    fn new(kind: i32) -> io::Result<Self> {
        let mut storage = vec![0_u8; SECURITY_MAX_SID_SIZE as usize];
        let mut size = storage.len() as u32;
        let ok =
            unsafe { CreateWellKnownSid(kind, null_mut(), storage.as_mut_ptr().cast(), &mut size) };
        if ok == 0 {
            return Err(io::Error::last_os_error());
        }
        storage.truncate(size as usize);
        Ok(Self { storage })
    }

    fn as_mut_ptr(&mut self) -> windows_sys::Win32::Security::PSID {
        self.storage.as_mut_ptr().cast()
    }
}

struct CurrentTokenUserSid {
    storage: Vec<u8>,
}

impl CurrentTokenUserSid {
    fn load() -> io::Result<Self> {
        let mut token = 0 as HANDLE;
        let ok = unsafe { OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &mut token) };
        if ok == 0 {
            return Err(io::Error::last_os_error());
        }
        let token = OwnedHandle(token);

        let mut required = 0_u32;
        unsafe {
            let _ = GetTokenInformation(token.0, TokenUser, null_mut(), 0, &mut required);
        }
        if required == 0 {
            return Err(io::Error::last_os_error());
        }

        let mut storage = vec![0_u8; required as usize];
        let ok = unsafe {
            GetTokenInformation(
                token.0,
                TokenUser,
                storage.as_mut_ptr().cast(),
                required,
                &mut required,
            )
        };
        if ok == 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(Self { storage })
    }

    fn as_mut_ptr(&mut self) -> windows_sys::Win32::Security::PSID {
        let token_user = unsafe { &mut *self.storage.as_mut_ptr().cast::<TOKEN_USER>() };
        token_user.User.Sid
    }
}

struct OwnedHandle(HANDLE);

impl Drop for OwnedHandle {
    fn drop(&mut self) {
        if !self.0.is_null() {
            unsafe {
                let _ = CloseHandle(self.0);
            }
        }
    }
}

struct LocalAcl(*mut c_void);

impl Drop for LocalAcl {
    fn drop(&mut self) {
        if !self.0.is_null() {
            unsafe {
                let _ = LocalFree(self.0);
            }
        }
    }
}
