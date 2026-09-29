# Microsoft Activation Scripts (MAS) — Deep Architecture Study

Status: **DEEP-STUDY PASS / STUDIED-AVOID FOR ACTIVATION BYPASS / ENGINEERING LESSONS RETAINED**
Registered: 2026-09-14
Upstream: `massgravel/Microsoft-Activation-Scripts`
Snapshot basis: MAS 3.12, released 2026-07-04.

## One-sentence understanding

**MAS is a data-driven Windows/Office licensing-environment resolver and privileged repair/mutation toolbox: it inventories OS/product/licensing reality, selects among method-specific activation engines through compatibility rules, applies state changes to Microsoft licensing mechanisms, and surrounds them with diagnostics, status inspection, edition conversion, cleanup and recovery paths.**

The activation-bypass effects are not acceptable Ordivon licensing authority. The architecture and operational discipline are nevertheless worth understanding in detail.

## Project-study gates

### One-sentence test

**PASS.** The essential mechanism can be stated without reducing the project to "a batch activator": MAS is a compatibility-sensitive dispatcher around several distinct Microsoft licensing subsystems and activation techniques, plus read-only diagnostics and repair tooling.

### Prototype test

**PASS at the safe/legitimate architectural level.** A lawful prototype can reproduce the core control architecture as:

```text
inventory installed Microsoft products
        ↓
identify OS/build/edition/channel/architecture/licensing subsystem
        ↓
collect entitlement evidence
        ↓
classify supported official activation channel
        ↓
read activation/licensing status
        ↓
run supported repair/activation provider
        ↓
read back status + retain entitlement evidence
```

That reproduces the valuable resolver/diagnostic/verification kernel without reproducing license-bypass methods.

---

# 1. Current project shape

At the current snapshot, the repository exposes an intentionally small top-level tree:

```text
Microsoft-Activation-Scripts/
├─ README.md
├─ LICENSE
└─ MAS/
   ├─ All-In-One-Version-KL/
   │  └─ MAS_AIO.cmd
   └─ Separate-Files-Version/
      ├─ Activators/
      │  ├─ HWID_Activation.cmd
      │  ├─ Ohook_Activation_AIO.cmd
      │  ├─ Online_KMS_Activation.cmd
      │  └─ TSforge_Activation.cmd
      ├─ Check_Activation_Status.cmd
      ├─ Troubleshoot.cmd
      ├─ Change_Windows_Edition.cmd
      ├─ Change_Office_Edition.cmd
      └─ Extract_OEM_Folder.cmd
```

The current `MAS_AIO.cmd` is approximately:

```text
19,228 lines
~743 KB
177 batch labels
107 distinct internal call targets observed
```

The method-specific standalone scripts are themselves substantial:

```text
HWID       ~2.1k lines
Ohook      ~3.3k lines
Online KMS ~4.2k lines
TSforge    ~9.8k lines
```

This matters because MAS is not architecturally a one-liner or a thin wrapper around one exploit. It is a large compatibility and system-state management program implemented in Batch/PowerShell/native Windows interfaces.

---

# 2. Architectural layers

A useful decomposition is:

```text
┌──────────────────────────────────────────────┐
│  UX / entry layer                           │
│  AIO menu, command-line switches, unattended│
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Bootstrap / environment normalization       │
│  OS/build/arch/admin/temp/terminal/PowerShell│
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Licensing inventory + health census         │
│  SPP/OSPP/ClipSVC/WMI/services/product state │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Compatibility / applicability resolver      │
│  SKU, edition, build, channel, IDs, internet │
│  static product/method data tables            │
└──────────────────────┬───────────────────────┘
                       ↓
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
      HWID           Ohook         TSforge       Online KMS
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Post-action validation / cleanup / recovery │
│  status, service refresh, uninstall, repair  │
└──────────────────────────────────────────────┘
```

Separate cross-cutting tools sit beside this path:

```text
Activation Status
Troubleshoot
Windows Edition Change
Office Edition Change
OEM/preinstallation export
```

## Why this decomposition matters

The durable engineering idea is not the effect engine. It is that **method selection happens only after a reality census** and that the project maintains explicit read-only/status/repair surfaces around privileged mutation.

---

# 3. Entry model: interactive and unattended use share one kernel

MAS provides:

- interactive menu operation;
- command-line switches for unattended operation;
- an All-In-One distribution;
- separate per-function scripts;
- preinstallation/OEM export paths.

The important architectural pattern is:

```text
human menu
command-line automation
preinstallation setup
        ↓
     same core method code
```

This avoids building unrelated "GUI logic" and "automation logic" with different compatibility semantics.

For Ordivon, the transferable lesson is:

> keep one semantic execution kernel and expose multiple control surfaces around it.

---

# 4. Bootstrap and environment normalization

Across the standalone method scripts, the same family of shared routines recurs (`dk_*` naming in the current codebase). The exact routines vary, but the responsibilities include:

- OS/build and edition discovery;
- architecture handling (x86/x64/ARM64 cases);
- administrative-permission checks/elevation handling;
- WMI availability and fallback behavior;
- Software Protection Platform health checks;
- product/SKU/license-ID discovery;
- installed-key/channel inspection;
- service state/refresh operations;
- Internet availability where a method depends on it;
- malware/security-product interference warnings;
- error classification and human-readable remediation suggestions;
- console/output normalization.

This shared layer is one reason method-specific scripts can remain relatively independent while still behaving consistently.

### Lesson

Privileged Windows automation should not begin with the mutation command. It should begin with an explicit **environment contract census**.

A reusable safe model is:

```text
preconditions
+ platform identity
+ provider health
+ authority
+ dependency availability
+ compatibility
→ only then effect proposal
```

---

# 5. Data-driven compatibility rather than pure branching

The AIO script contains large dedicated data sections such as:

- `hwiddata`;
- `hwidfallback`;
- `ohookdata`;
- `tsksdata`;
- `ksdata`;
- `kmsfallback`;
- `msiofficedata`;
- Windows/Office edition data.

These encode things such as:

- SKU/edition relationships;
- activation IDs;
- product/channel mapping;
- Windows/Server generation applicability;
- Office generation/product mapping;
- alternative/fallback editions;
- method-specific support information.

The exact licensing data is not imported into Ordivon. The architectural lesson is important:

> **compatibility knowledge is treated as versioned data adjacent to the execution algorithm rather than as thousands of scattered one-off conditionals.**

This makes it easier to update when Microsoft introduces a new build, SKU, ESU family or licensing behavior.

---

# 6. Four method engines are semantically different

The most important technical mistake would be to treat HWID, Ohook, TSforge and Online KMS as four implementations of the same operation. They act on different authority/state boundaries.

## 6.1 HWID — server-persisted digital-license path manipulation

High-level model:

```text
local Windows licensing state
        ↓
construct/obtain activation eligibility artifact/state
        ↓
Microsoft digital-license activation path
        ↓
Microsoft-side hardware-linked activation state
```

The upstream documentation describes the result as a hardware-associated digital license that is later recognized by Microsoft's servers. The project therefore treats Internet connectivity and Windows build/edition compatibility as consequential preconditions.

Architecturally, HWID is interesting because the durable state is **not only local**. Once the remote activation state exists, reinstall behavior can be driven by Microsoft's server-side record for the hardware.

### Lesson

An external effect whose durable authority lives at the provider cannot be undone merely by deleting local files/state. Local rollback and provider rollback are different concepts.

This is directly relevant to Ordivon external-effect modeling.

## 6.2 Ohook — local runtime licensing interception for Office

High-level model:

```text
Office licensing call path
        ↓
locally installed hook/interposition component
        ↓
licensing result presented to Office
```

Current MAS packages the required hook binaries into the AIO script as encoded payloads. The source comments include expected SHA-256 values and point to independent source/rebuild information for the hook component.

The current project also explicitly hardened this area in v3.12 by removing support for user-supplied replacement DLLs.

### Engineering lessons

1. **Embedded binary provenance should be explicit.** A privileged self-contained script should bind embedded payloads to source/rebuild information and expected digests.
2. **Arbitrary plugin/payload substitution in a privileged tool is a security boundary.** Flexibility can be less valuable than removing an injection surface.
3. A local hook is persistent local state and requires explicit uninstall/cleanup semantics.

The hook's license-bypass semantics are not adopted.

## 6.3 TSforge — direct manipulation of Software Protection Platform state

TSforge is the deepest method-specific subsystem in the current source and is responsible for a large fraction of the script's complexity.

The upstream documentation frames it around Windows' Software Protection Platform (SPP), including SPP's token/physical stores and protected licensing state. The method family is designed to produce licensing states accepted by SPP, with multiple sub-methods selected according to Windows generation and context.

Conceptually:

```text
SPP product/license model
      +
protected licensing stores/state
      +
product/activation-ID knowledge
        ↓
construct licensing state accepted by SPP
        ↓
refresh/reload licensing subsystem
```

Current source contains a very large method-specific implementation section plus product/license databases and separate reset/remove/recovery logic.

### Engineering lessons

- The project isolates the most version-sensitive internal mechanism behind one method boundary.
- Build-specific behavior is explicit and changes over time.
- The same engine exposes removal/reset operations rather than only forward mutation.
- The project's changelog actively tracks Microsoft changes that invalidate prior assumptions.

The state-forging logic itself is exactly the authority boundary Ordivon must not adopt for software entitlement.

## 6.4 Online KMS — real protocol, wrong authority

Microsoft KMS itself is a genuine volume-activation mechanism for organizations. MAS' Online KMS path uses KMS-compatible activation semantics while pointing the client at public/emulated KMS infrastructure rather than an organization-owned/authorized KMS host.

Conceptually:

```text
KMS-capable Windows/Office product
        ↓
KMS protocol/client behavior
        ↓
non-authorized public/emulated host
        ↓
time-limited local activation state
        ↓
optional renewal automation
```

This is the cleanest demonstration in MAS of **protocol validity != authority validity**.

The technical protocol can be perfectly compatible while the actor/server lacks the organizational license authority that gives KMS its legitimate meaning.

For Ordivon this becomes a general rule:

> **A valid protocol exchange is not proof that the counterparty is an authorized authority.**

---

# 7. Read-only Activation Status is a distinct subsystem

MAS integrates an advanced activation-status tool (CAS), maintained as a separate project. Its documented scope includes Windows and Office licensing status, expiration, key channels, add-on licenses, ADBA/AVMA/subscription activation and other licensing information.

This separation is architecturally strong:

```text
read-only census/status
!=
mutation engine
```

A licensing-management system should be able to answer:

```text
What products are installed?
What licensing subsystem/channel is in use?
What is the current status/expiration?
Which add-on licenses exist?
```

without first offering to mutate anything.

### Ordivon lesson

**Census before effect.**

For future system-management capabilities, expose an inspect/status provider independently of the effect provider whenever possible.

---

# 8. Troubleshoot is not just "activation retry"

The current Troubleshoot script contains separate recovery families including:

- DISM/SFC-based Windows component repair paths;
- ClipSVC licensing cleanup/rebuild;
- SPP token/license reconstruction;
- Office licensing repair;
- WMI diagnosis/repair;
- permissions checks/repair;
- logging/compression/reporting helpers.

This reveals an important mature support model:

```text
activation failure
   ↓
classify underlying subsystem failure
   ↓
repair subsystem
   ↓
re-census
   ↓
only then retry higher-level licensing operation
```

It does **not** assume every failure is solved by repeating the same activation action.

That aligns with the broader Ordivon rule:

> retry belongs to the semantic layer that understands the failure.

---

# 9. Edition conversion is treated as prerequisite normalization

MAS includes both Windows and Office edition/channel conversion tooling because method applicability is often tied to installed edition/channel.

The project therefore sometimes follows:

```text
current installed product
        ↓
incompatible with selected licensing method
        ↓
convert/normalize edition/channel
        ↓
apply method
```

This is an important but dangerous pattern.

### General lesson

A provider may normalize an input into its supported domain, but normalization is a **real effect** and must not be hidden as mere preprocessing.

For Ordivon:

```text
input normalization that changes external state
!=
pure adapter transformation
```

It needs its own authorization, evidence and rollback/repair story.

---

# 10. OEM/preinstallation export turns an interactive tool into deployment composition

The `$OEM$` extraction path can package activation-related behavior into Windows installation media/setup flows. Architecturally this changes the execution time from:

```text
operator runs tool on installed machine
```

to:

```text
image/build preparation
  ↓
installation lifecycle
  ↓
post-setup effect
```

The important transferable idea is **deployment-time materialization of an already-defined method**, not the activation bypass itself.

For legitimate Windows administration, the same pattern is used for drivers, enterprise enrollment, provisioning packages, authorized volume activation and setup automation.

---

# 11. Packaging: AIO is generated self-contained composition

The project offers both modular files and a self-contained AIO form. The AIO script contains:

- method code;
- compatibility/product data;
- diagnostics;
- selected binary payloads represented as encoded text;
- extraction/reconstruction logic.

This gives users one artifact while maintainers conceptually retain separable method boundaries.

The Ohook payload section is especially illustrative: comments include binary hashes and links to source/rebuild information.

### Lesson

A single-file operational artifact can still preserve internal provenance if:

```text
source identity
+ payload digest
+ rebuild path
+ version
```

are retained.

This is much stronger than anonymous embedded binary blobs.

---

# 12. Compatibility maintenance is a first-class project capability

MAS' changelog is unusually informative architecturally.

Examples in recent history include:

- method behavior changed because Microsoft server-side behavior changed;
- KMS38 was removed after newer Windows builds deprecated the relied-upon migration behavior;
- new Windows/Server/ESU products and IDs were added;
- Office/Windows edge cases changed by build/channel;
- Smart App Control interactions were surfaced;
- ARM64 and old OS support issues were fixed;
- v3.12 hardened the script and removed user-provided DLL substitution.

This tells us the real maintenance burden:

> **MAS is a compatibility-tracking project against a moving proprietary licensing implementation.**

A method can be technically correct today and obsolete after a Microsoft build/server change.

### Ordivon lesson

When consuming an implementation-detail-dependent provider, compatibility debt should be treated as a measurable ongoing liability, not a one-time integration cost.

---

# 13. MAS is itself a composition project

MAS is not the work of one isolated algorithm or one author. Current/historical documentation credits or integrates work such as:

- CAS / activation-status work maintained separately;
- Ohook and its separate source/rebuild path;
- TSforge from the MASSGRAVE R&D team;
- KMS_VL_ALL heritage/contributions in earlier Online KMS generations;
- community-developed Windows scripting/compatibility techniques;
- text/binary packaging techniques used for self-contained AIO distribution.

This is one reason the project became broad and resilient: **it composes specialized licensing research behind one compatibility and UX layer.**

That composition pattern is worth learning even though the resulting entitlement-bypass product is not an acceptable Ordivon provider.

---

# 14. Security architecture and supply-chain observations

## 14.1 High privilege magnifies provenance requirements

Licensing repair/mutation touches Windows services, protected licensing state, registry/filesystem locations and product configuration. The scripts therefore operate in a high-authority environment.

That makes provenance and exact source identity more important than for an ordinary utility.

## 14.2 Mutable remote execution is the weakest distribution pattern

The project publicly warns about malicious look-alike URLs while also offering a network-download-and-immediate-execute convenience path.

For Ordivon-managed endpoints, prefer:

```text
pinned release/source
+ exact digest/signature
+ reviewed content
+ explicit authority
+ receipt
```

rather than executing mutable remote text directly.

## 14.3 Embedded-payload anti-AV transformations are a trust smell even when source is available

The current AIO comments document text transformations intended to prevent antivirus products from flagging an encoded binary payload representation.

This is understandable from the project's distribution perspective, but it creates a general defensive lesson:

> **When software intentionally changes representation to avoid static security detection, provenance/reproducibility must carry more of the trust burden, not less.**

Do not copy detector-evasion patterns into normal Ordivon packaging.

## 14.4 Removing arbitrary DLL substitution is good hardening

MAS 3.12 removed support for user-provided DLL substitution and cites script hardening. In a privileged operational tool, restricting extension points can be a security improvement.

This supports a broader rule:

> **Plugin/extensibility surfaces are authority surfaces. Delete them when their value does not justify the supply-chain risk.**

---

# 15. Failure model

MAS' effective failure model can be summarized as:

```text
unsupported platform/product
provider subsystem unhealthy
missing/corrupt licensing packages
WMI/SPP/ClipSVC service problems
network/server unavailable
security software interference
method invalidated by Windows/Microsoft change
edition/channel mismatch
method-specific state corruption
```

The project often attempts to distinguish these rather than returning one generic "activation failed" state.

That is exactly the right shape for reliable automation.

### General rule

```text
failure classification
→ specific repair or method fallback
```

is superior to:

```text
failure
→ generic retry
```

---

# 16. Natural-authority analysis

MAS itself owns only its script logic and local execution behavior.

It does **not** naturally own:

```text
Microsoft software entitlement
Microsoft licensing policy
organization volume-license authority
provider-side digital-license records
legal/compliance truth
```

Those remain with Microsoft/license agreements/organization records.

The project's methods intentionally make Microsoft licensing components accept states outside those normal entitlement authorities; this is why technical success cannot be used as licensing evidence.

---

# 17. What Ordivon should retain from MAS

## 17.1 Environment census before mutation

Build/edition/SKU/channel/architecture/services/network/health first.

## 17.2 Data-driven applicability tables

Keep evolving compatibility knowledge versioned and separate from core effect code.

## 17.3 Multiple method engines behind one resolver

Different mechanisms can solve superficially similar user-facing problems while having radically different persistence/authority/failure semantics.

## 17.4 Read-only diagnostics as a first-class product

Status should be independently callable from mutation.

## 17.5 Repair is separate from retry

Fix the underlying subsystem before replaying a higher-level action.

## 17.6 Explicit cleanup/uninstall paths

Any persistent local change should declare what "remove" means and what state cannot be rolled back locally.

## 17.7 Provider-side effects need provider-side reasoning

HWID demonstrates that some durable results live remotely; local state deletion is not equivalent to provider rollback.

## 17.8 Protocol validity does not imply authority validity

Online KMS is the clearest example.

## 17.9 Embedded artifacts need hashes and source/rebuild provenance

Especially in privileged single-file tools.

## 17.10 Kill obsolete methods when upstream reality changes

KMS38 removal is a strong example of deleting a once-working path instead of indefinitely preserving it.

## 17.11 Restrict privileged extension points

The v3.12 DLL-substitution removal is a useful hardening lesson.

## 17.12 Compatibility debt is real operational debt

Implementation-detail-dependent providers require continuous tracking against vendor releases.

---

# 18. What Ordivon must not copy

- Windows/Office entitlement-bypass methods;
- direct licensing-store forgery/manipulation as entitlement authority;
- unauthorized/public-emulated KMS as a substitute for organization-owned licensed KMS;
- runtime licensing hooks as software-license proof;
- activation UI/state as proof of valid entitlement;
- detector-evasion packaging as a standard distribution technique;
- mutable remote privileged download-and-execute as default administration;
- arbitrary edition/channel changes hidden as preprocessing;
- Microsoft internal implementation assumptions as permanent Ordivon semantics.

---

# 19. Safe mature substitute architecture

For a legitimate organization or user, the comparable mature architecture is:

```text
Microsoft product inventory
       ↓
entitlement evidence
├─ OEM/digital/retail
├─ organization volume agreement
├─ MAK
├─ authorized KMS/ADBA
└─ other supported Microsoft channel
       ↓
activation-status census
       ↓
channel-specific supported activation/repair
       ↓
VAMT / Microsoft-supported management where appropriate
       ↓
status read-back
       ↓
retain license/asset-management evidence
```

Microsoft documents VAMT as the supported centralized management tool for retail/MAK/KMS activation, including online/proxy activation scenarios.

---

# 20. Safe prototype specification

A legal MAS-inspired prototype could be built as **Microsoft Licensing Diagnostics & Repair Router**.

## Input

```text
machine identity
installed Windows/Office inventory
OS build/architecture
product editions/channels
current licensing status
organization entitlement records
```

## Read-only stages

```text
Inventory
→ Licensing subsystem health
→ Activation/channel classification
→ Entitlement match
→ Applicable supported provider
```

## Effects

Only supported effects, for example:

```text
run Windows Activation Troubleshooter
apply legitimate digital/retail key path
VAMT online/proxy activation
organization-authorized KMS/MAK/ADBA action
DISM/SFC/WMI/licensing-component repair
```

## Evidence

```text
pre-state
provider/channel selected
entitlement record reference
exact repair/activation action
post-state
provider/read-back result
```

This reproduces MAS' best engineering ideas without inheriting its licensing-authority violation.

---

# 21. Comparison to Ordivon architecture

MAS is a useful negative mirror for several Ordivon principles.

```text
MAS compatibility census
↔ Ordivon DEFINE/precondition binding

MAS method resolver
↔ provider/capability selection

MAS independent activator engines
↔ natural authority/provider-specific execution

MAS Activation Status
↔ read-only reality projection

MAS Troubleshoot
↔ failure-specific recovery

MAS changelog-driven method removal
↔ delete custom/provider semantics when upstream reality invalidates them
```

The critical divergence is:

```text
MAS target = make licensing subsystem accept activation state

Ordivon legitimate target = establish/repair activation under valid entitlement authority
```

That difference is exactly why the project is valuable to understand but inappropriate to adopt as a licensing provider.

---

# 22. Final verdict

**DEEP-STUDY PASS / STUDIED-AVOID.**

MAS is a mature, highly maintained Windows licensing compatibility and mutation toolbox, not merely a trivial activator. Its strongest transferable engineering patterns are reality census before mutation, data-driven compatibility, method isolation, independent diagnostics, failure-specific repair, explicit cleanup, payload provenance, and aggressive removal of obsolete paths.

Its activation engines deliberately cross or emulate licensing authority boundaries, so they are not acceptable Ordivon providers for Microsoft entitlement. The correct Ordivon reuse is **architectural knowledge**, not the bypass effects.

## References

- https://github.com/massgravel/Microsoft-Activation-Scripts
- https://github.com/massgravel/massgrave.dev/blob/main/docs/intro.md
- https://github.com/massgravel/massgrave.dev/blob/main/docs/hwid.md
- https://github.com/massgravel/massgrave.dev/blob/main/docs/tsforge.md
- https://github.com/massgravel/massgrave.dev/blob/main/docs/online_kms.md
- https://github.com/massgravel/massgrave.dev/blob/main/docs/check_activation_status.md
- https://github.com/massgravel/massgrave.dev/blob/main/docs/changelog.md
- https://learn.microsoft.com/en-us/windows/deployment/volume-activation/volume-activation-windows
- https://learn.microsoft.com/en-us/windows/deployment/volume-activation/volume-activation-management-tool
