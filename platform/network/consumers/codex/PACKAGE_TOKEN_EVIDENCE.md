## Windows MSIX package identity versus live process-token identity

A Windows MSIX `PackageFamilyName` is not interchangeable with the app SID
required by `New-NetFirewallRule -Package`; derive the latter via Microsoft's
native `DeriveAppContainerSidFromAppContainerName` API. On Windows, the
read-only Python standard-library witness `windows_package_token_evidence.py`
accepts `--package-family` and repeated `--target executable.exe:PID` for
actual Windows process instances. Obtain package family and PID samples from
`Get-AppxPackage` and `Get-CimInstance Win32_Process`, respectively.

The witness reads (never adjusts) Windows process tokens with
`OpenProcessToken` / `GetTokenInformation`, specifically
`TokenIsAppContainer`, `TokenAppContainerSid`, and `TokenGroups`.
Its `tokenObservation` is distinct from `packageFirewallEnforcement`:
the latter is **always UNKNOWN** until a disposable package-aware firewall
acceptance experiment actually exercises the intended target.

On 2026-11-08, 5 active Session-1 OpenAI.Codex app samples (ChatGPT.exe,
codex.exe, codex-code-mode-host.exe) were successfully inspected; all were
non-AppContainer tokens with neither the derived package SID as
TokenAppContainerSid nor in TokenGroups. This constrains the representation,
but does *not* prove `-Package` will fail for packaged classic Win32 apps:
a firewall provider may have additional package identity classification
not represented by these token fields.

Do not replace proven `-Program` filtering with a `-Package` rule based only
on MSIX installation metadata or these token findings. Do not install
permanent filters on production ChatGPT/Codex until isolated app-specific
testing confirms actual WFP effect, necessary direct exceptions and rollback.

Microsoft upstream references:
- https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-deriveappcontainersidfromappcontainername
- https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule
- https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-token_information_class
