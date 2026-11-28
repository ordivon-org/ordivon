# Windows packaged-program coverage witness

The OpenAI.Codex MSIX registration and its actual Windows process tree are
different representations. A Windows Firewall rule scoped with -Program matches
an executable program, not all descendants of the process that launched it.
The -Package rule takes a package SID, and its effectiveness against this
full-trust Win32 package has NOT been established.

## One-shot native check

From the Network owner directory on a Windows interactive desktop run:

    python consumers/codex/windows_package_program_coverage.py

It uses Microsoft-native Get-AppxPackage, Win32_Process CIM, and
Get-AuthenticodeSignature, invoked from Python without installing new
dependencies. It does not change routes, proxy settings, audit policy,
firewall rules, installed apps or system services.

Input stays in the local process. The JSON output contains only package
family/version, relative package binary paths, executable signature validity,
process counts, session numbers and external descendant basenames.
It does not export command lines, user home paths or raw credentials.

## 2026-11-08 Session 1 consumer acceptance

The native read-only witness returned:

- Package: OpenAI.Codex 26.1103.4239.0
- 24 running processes under the actual installed package root
- 6 distinct package-root executable paths, all Authenticode Valid
- 11 live descendant processes with executables outside the package root:
  conhost.exe x9, node.exe x1, cmd.exe x1
- zero missing executable paths and zero PID-generation ambiguities

These are time-specific observations, not an assertion that external children
actually opened direct network sockets. The code intentionally retains
allProtocolFirewallCoverage=UNKNOWN even on a clean snapshot.

## Human guidance

Before considering an outbound enforcement policy, compare actual executable
coverage and child processes after app startup, when network actions execute,
and after every package update. Validate Windows Firewall -Program with a
disposable executable first. Do not assume a single -Program rule for
ChatGPT.exe or codex.exe covers auxiliary executables, external node.exe or
cmd.exe children, DNS implemented by system services, or UDP/IPv6/QUIC.

## Agent guidance

Treat this as a bounded source observation. Do not convert the absence of a
descendant in a one-shot snapshot into a guarantee about the future.
Do not invent a package-SID enforcement claim. If a process generation cannot
be correlated, report UNKNOWN instead of claiming its parentage. Do not
install any production firewall rule without an independent disposable
acceptance, actual Consumer demand, and a tested rollback.

## Upstream mechanisms

- https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-process
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-authenticodesignature
- https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule
- https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallapplicationfilter

Issue: https://github.com/ordivon-org/ordivon/issues/1824
