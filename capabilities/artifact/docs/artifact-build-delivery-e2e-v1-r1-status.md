# Artifact Build & Delivery E2E v1 — R1 current status

## 2026-09-11 superseding standing — 34:10 Golden R2 accepted in profile

The separate 34:10 PDU/SDU migration branch has now closed every required gate in `presentation-ultrawide-34x10-r1` on one exact build tuple. The accepted editable PPTX is SHA-256 `fa48aa4a513f7ab04e05cc374b80592903acae8c39d727cf3c9737d68f2f1d03` (2,745,582 bytes, 8 slides); the required native PowerPoint PDF companion is `bea385bfc2d78b82498315c251203c4ee54f0112fe24430a8142cd1aebb850fe` (1,149,721 bytes). The final profile gate is `PASS` with `requiredGateFailures=[]`, evidence SHA-256 `c3e9666b287f7dc29d1eb6371f1aaa088c0eb56b9708e3d29658f9ca29feeecd`.

The accepted tuple was rebuilt from the exact `artifact-golden-r1` parent package through Runtime `workspace.execBound`, passed `DocumentFormat.OpenXml` 3.5.1 with zero validation errors, then passed a real Microsoft PowerPoint Desktop 16.0 target run. Eight 3400×1000 target PNGs were digest-bound and visually reviewed against the frozen source rasters; no blocking visual defects were recorded. The exact PPTX/PDF tuple was then written to and read back byte-identically from both `C:\\Users\\Public\\Documents\\Ordivon Artifact E2E\\Golden R2 fa48aa4a` and `/Google Drive/Ordivon Artifact E2E/Golden R2 Accepted fa48aa4a`.

Canonical acceptance is frozen in `artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-acceptance-r2.json`. This is deliberately `ACCEPTED_IN_PROFILE`, not a universal Artifact E2E graduation claim. Business-content truth, accessibility/human usability, and formal third-party IV&V remain outside this acceptance. At acceptance time, cross-workspace byte determinism was also explicitly unproven; that historical nonclaim remains truthful in the immutable acceptance manifest. A successor Engineering E2E investigation later reproduced the byte variation, isolated it to ZIP DOS header timestamps only, and closed it for the tested non-ZIP64 generated-PPTX builder without changing the accepted `fa48aa4a…` tuple. See `pdu-sdu-34x10-determinism-evidence-r1.json`.

An earlier D2 run recorded `589829d2…` PPTX plus `22dcd6f2…` PDF as a successful accepted run before the source-current `fa48aa4a…` acceptance manifest was frozen. Independent Drive read-back and byte-level reconciliation now show that the two PPTX files have identical 60-member OOXML and compressed payload bytes and differ only in ZIP timestamps; the two PDF files have identical eight-page content streams, XObject payloads, extracted text and rendered pixels and differ in PowerPoint export metadata such as timestamps and document IDs. The earlier pair is therefore retained as a historical accepted metadata variant, not a second current canonical tuple. `pdu-sdu-34x10-acceptance-lineage-r1.json` records this currentness relationship.

The older R1/R2 transport-frontier statements below are retained as historical evidence and are superseded where they still say the 34:10 branch is `NOT PASS` or blocked on raster/source transport.

## R2 current transport closure — parent OPC package, not eight external raster transfers

The R1 statements below remain historical evidence of the earlier transport frontier. They are no longer the current transport design. R2 observes that the eight frozen visual JPEGs are package parts of one exact OOXML/OPC parent artifact, `PDU_SDU_34x10_8页演示稿.pptx`, rather than eight independent external source objects. The current external ingress target is therefore one parent package binding: SHA-256 `b50ab3025c4b285c728d029416492b4c7a03de1fc9e0bfe3f05293bfaf5f468c`, 2,791,610 bytes. `pdu-sdu-34x10-runtime-package-input-set-r2.json` freezes that single Runtime `workspace.execBound` object.

After Runtime independently verifies and presents the parent package, Artifact owns only an internal OPC projection step. `pdu-sdu-34x10-opc-member-projection-r2.json` binds the exact eight `ppt/media/image-*-1.jpeg` package parts by member name, uncompressed size and SHA-256 and projects only those bytes to `slide-01.jpeg` … `slide-08.jpeg`. The projection is fail-closed on parent digest/size drift, member digest/size drift, duplicate archive members, duplicate output paths, unsafe paths, symlinked parent packages, encrypted members and conflicting existing outputs. Exact replay is accepted only for byte-identical outputs. This is package-part materialization evidence, not provider identity, visual parity, accessibility, target-render or business-content acceptance.

The existing deck reference map already binds `slideIndex + legacySource.sha256`; no second hybrid-plan schema is introduced. `compose-reference-hybrid-source` mechanically prepends each exact frozen visual under the corresponding native semantic overlay and preserves the native editable overlay above it. The raster is not treated as proof of accessibility; alt-text metadata explicitly retains the requirement for independent accessibility/use review. Current mechanical evidence is 8/8 dedicated OPC/hybrid contract/destructive tests PASS plus the existing Artifact/Doctor/Temporal regression set 78/78 PASS (12 environment-dependent external-validator skips). Final Golden standing remains **NOT PASS** until real production ingress, exact Runtime-bound parent-package execution, Microsoft PowerPoint target rendering, eight-slide visual review, native PDF generation and delivery/read-back evidence all close.


Date: 2026-09-09
Host Task: `task:artifact-build-delivery-e2e-v1`
Initial R1 implementation commit: `3271da0edf917c302aed537e33ecb62b325cc696`

## Standing

The R1 Presentation substrate is now proven on a Windows PowerPoint smoke fixture. The PDU/SDU Golden case is **not graduated**.

Current split standing:

- `presentation-r1-windows-smoke`: `PASS` across profile, OOXML, dependencies, semantics, PDF, Microsoft PowerPoint target render, PNG integrity, visual smoke review, Windows delivery and Windows read-back.
- Original PDU/SDU 8-slide artifacts: frozen regression inputs; they fail the R1 font dependency contract because they directly reference unavailable/unapproved Aptos.
- Font-fixed PDU/SDU candidates: source repair PASS, Google Drive write/read-back PASS, secondary-render confidence PASS, Microsoft PowerPoint primary target `NOT_RUN`.

The remaining PDU/SDU blocker is no longer PowerPoint availability. It is exact source-byte transport from the durable repaired candidates into the target workstation through a mature existing input/API mechanism.

## Separate 34:10 controlled migration branch

A newer approved 8-slide **34:10 visual deck** is being migrated under the same Artifact Build & Delivery substrate, but it is a separate source/product branch from the older 16:9 PDU/SDU Golden artifacts described below. Do not transfer the 16:9 font-repair standing onto the 34:10 deck.

The presentation authoring layer now has the prerequisites for that migration: digest-bound slide-free PPTX template/master/layout/placeholder binding, digest-bound PNG/JPEG hybrid media, and the generic `presentation-ultrawide-34x10-r1` profile. A standard DrawingML alpha mapping is also available for native text opacity, allowing a migration stage to preserve a frozen visual raster while carrying zero-opacity native editable semantic text without changing the visual render. This is a migration technique, not an accessibility PASS: accessibility remains an independent target gate.

The full eight-slide visual deck is now recorded in a schema-valid deck-level `reference-map`; each slide binds the exact supplied JPEG SHA-256 and observed common source dimensions `1536×452`. A deck-wide buildable native semantic overlay now carries 111 zero-opacity editable text elements across all eight slides using standard DrawingML alpha. The overlay source validates, builds as an eight-slide 34:10 PPTX, and passes `DocumentFormat.OpenXml`; its source SHA-256 is `5ed264937da812c2fe67f4a13566d4bdc4dbac3c700a6dbdcbed4bff9f6f8743` and the overlay-only smoke PPTX SHA-256 is `287b5b2c54fa941cbab123bde8b4c77e50ea85bc8bfb42fd8ab33d4f2f2a3e70`. These reference/overlay sources carry approved wording only and are intentionally separate from business-claim validation. The overlay deliberately omits any small-text wording that is not sufficiently established rather than guessing it.

The deck-wide standing is `DECK_REFERENCE_MAP_AND_NATIVE_SEMANTIC_OVERLAY_READY_FINAL_HYBRID_BLOCKED_ON_EXACT_RASTER_TRANSPORT`. The reference-map is intentionally not accepted by the native builder. The dedicated Runtime input authority `artifact-golden-r1` is now configured and `workspace.execBound` has passed an exact-digest read-only smoke through `/run/ordivon/inputs`. The eight committed JPEG objects themselves are not yet materialized into that authority, so no final hybrid visual composition PASS is claimed.

The transport gap is therefore explicit and narrower than before: the Runtime authority and immutable-input execution path are working; only the eight exact committed raster objects still need to be deposited into the operator-owned `artifact-golden-r1` root by an approved external file/materialization carrier. `pdu-sdu-34x10-runtime-input-set-r1.json` freezes the eight `authority + relativeObject + expectedDigest + presentationRelativePath` bindings for the subsequent `workspace.execBound` admission. A direct slide-01 probe now fails specifically with `cannot resolve input object inside authority`, proving that the remaining blocker is object materialization rather than authority registration. Once those exact objects are present, compose each 34:10 slide with full-raster visual authority plus native editable semantic overlays, verify OpenXML/semantics, and only then run visual/target gates. The migration does not justify a new Artifact-specific file transport.

## Implemented contract and gates

R1 uses JSON Schema Draft 2020-12 profiles, native OOXML PPTX, `DocumentFormat.OpenXml` 3.5.1 `OpenXmlValidator`, explicit target font dependencies, qpdf for ordinary PDF structural checking, digest-bound render and visual evidence, destination read-back SHA-256 verification, and in-toto Statement v1 + SLSA Provenance v1. No universal document AST or Ordivon-specific file/provenance/accessibility standard is introduced.

Render-relevant font closure covers slide, slideLayout and slideMaster parts. Concrete typeface references must be declared and target-satisfied when `fontPolicy=REQUIRED`; theme-symbolic `+mj-*` / `+mn-*` references are not treated as concrete installed-font requirements.

The current semantic gate also enforces declared presentation aspect ratio and configured minimum/maximum slide count. This prevents a structurally valid but wrong-form artifact such as the inspected one-slide 10:34 long-canvas deck from graduating under the 16:9 presentation profile.

PowerPoint output enumeration is extension-case-insensitive because localized PowerPoint exported the smoke PNG as `幻灯片1.PNG`. Target evidence additionally binds the exact PNG name/digest map; file count or process exit alone cannot establish target-render integrity.

## Standard validator verification

`jsonschema==4.26.0` validates the R1 profile against Draft 2020-12. `.NET SDK 8.0.424` was materialized only under ignored `.cache` for verification. `DocumentFormat.OpenXml==3.5.1` restored and built in Release with 0 warnings and 0 errors. A real PPTX created by Microsoft PowerPoint Desktop validated through `OpenXmlValidator` with zero errors.

## Microsoft PowerPoint smoke — primary target proof

The bounded one-shot worker is staged on local NTFS and uses Microsoft PowerPoint Desktop rather than a Linux renderer as target truth. For ordinary `PDF_VIEW`, it uses native `Presentation.SaveAs(..., ppSaveAsPDF=32)` and `Presentation.Export(..., PNG, ...)`, then closes PowerPoint.

Successful target run facts:

- PPTX SHA-256: `7cb01e91a8273f6673bfcb791b85b8746dcb42d6065cc15fcb41a99697148968`
- PowerPoint version: `16.0`
- `POWERPNT.EXE` SHA-256: `90fa931172c507b763ba92a82b19d5bc70816e008c5bb87577e1838e8a92e9f9`
- PDF SHA-256: `770f573025f561cb94852c7b7d6cc2684bd3ce78b9a2d3ae0dfe3fb00863b6a6`
- target PNG: `幻灯片1.PNG`
- PNG SHA-256: `b716ff15bb388be443cb5a6c821a3428c5c7b9b896d337e1351fb3b254c36eec`
- qpdf structural check: PASS
- deterministic smoke visual review: PASS; non-background bounds stay clear of slide edges

The Windows delivery branch then copied the exact PPTX/PDF into `C:\Users\Public\Documents\Ordivon Artifact E2E\R1 Smoke Accepted\` and read them back with exact source/destination SHA-256 equality.

A temporary smoke profile containing only the `windows-workstation` delivery target completed every required gate with `requiredGateFailures=[]`. Full gate evidence SHA-256: `9659e0849d86b90deeb837c3d5f8b822323cb72dda3a01ee2ac09ad553f8487f`.

This proves the PowerPoint/Windows branch of the substrate. It does not graduate PDU/SDU and does not imply Google Drive delivery of the smoke outputs.

## Original Golden regression

Frozen originals:

- `PDU_SDU_解释版_8页.pptx`: `4534bce68f184b6f841b8f07b82312b3137344775145e015019bb299c198f329`
- `PDU_SDU_论证版_8页.pptx`: `1b407368a7ceb008a44ac002a2b8c2fdf29e829a432c193b434719986597dcfa`

Both are 8-slide 16:9 structural candidates with complete OPC relationships and no placeholder hits, but their render graph explicitly references Aptos, Arial and Microsoft YaHei. Arial and Microsoft YaHei are approved/present; Aptos is not. The originals therefore remain regression inputs rather than release candidates.

## Font-fixed Golden candidates

The source repair is intentionally narrow and OOXML-native: only concrete Aptos bindings in render-relevant slide/layout/master parts were replaced by script role (`latin/cs → Arial`, `ea → Microsoft YaHei`). No global theme rewrite and no silent fallback was used.

Candidates:

- explain: `PDU_SDU_解释版_8页_fontfixed_r1.pptx`, SHA-256 `fdd1aca9c4cef977a2c1f447987f5ab66ee1c9bab6f13c056ccc8f4a784e8bf1`, 33 font-binding replacements.
- argue: `PDU_SDU_论证版_8页_fontfixed_r1.pptx`, SHA-256 `c66b873650657131144ab373dc3ac13f7740ec16a3889aee7cceec905d2fa98c`, 27 replacements.

Both remain 8 slides at `12192000 × 6858000` EMU (16:9), contain zero concrete Aptos references in render-relevant parts, and expose only Arial + Microsoft YaHei as concrete render typefaces. ZIP CRC and XML/relationship parsing checks pass.

Both candidates plus the repair receipt were uploaded under `/Google Drive/Ordivon Artifact E2E/Golden R1/` and re-materialized from Drive. Read-back bytes exactly match their frozen output digests. Repair receipt SHA-256: `36d6a48d9dd5a55e99bd49d053969dbb8e1be06a98ca82ef7469658d6260b708`.

## Secondary-render regression confidence

LibreOffice 25.2.3.2 was used only as a non-authoritative regression renderer on original versus font-fixed candidates. Both repaired candidates produced eight pages. The argue deck is effectively pixel-stable. The explain deck changes primarily on slides 5 and 6 where explicit English PDU/SDU labels moved from Aptos to Arial; changed-pixel fractions are roughly 0.1% and direct full-slide inspection showed no clipping, overflow or structural layout break.

Secondary evidence SHA-256: `bbca6f81927eadddada97e0b7d482febbb2143630efa07cf144d4f3d0aaeac75`.

This is confidence evidence only. It cannot substitute for Microsoft PowerPoint primary target render and visual acceptance.

## Delivery and source-transport facts

Google Drive is exercised through the API-backed file Library surface rather than browser-click automation. Existing originals, newly repaired candidates, repair receipt and current evidence objects have all demonstrated exact API write/read-back identity where applicable.

Windows endpoint delivery/read-back is independently proven by the target-accepted smoke PPTX/PDF.

What is missing is a mature input path for the exact repaired Golden bytes into the workstation. Current observations:

- Runtime `workspace.execBound` is now configured with the dedicated `artifact-golden-r1` authority and has passed an exact-digest local smoke; the current deck blocker is the absence of the eight committed JPEG objects inside that operator-owned authority, not the Runtime mechanism itself.
- rclone 1.75.0 is installed but no Drive remote/configuration exists.
- no Google Drive Desktop mount is present.
- ambient WSL HTTPS, the existing `native-a` and `native-b` scoped HTTPS profiles, and Windows-native direct HTTPS currently time out against Google Drive endpoints.
- a one-off fixture transport was tested and rejected as an architecture solution; no Artifact-specific transport is being introduced.

Therefore the next correct action is to reuse/configure an existing mature exact-input/API path, not add another Ordivon transport protocol.

## Current R1 graduation frontier

Full PDU/SDU R1 remains `NOT_PASS`. Graduation requires the exact font-fixed candidate bytes to reach the target workstation under digest binding, followed by `DocumentFormat.OpenXml` validation, Microsoft PowerPoint open/export, eight target PNGs, digest-bound visual review, companion PDF, Google Drive write/read-back, and Windows write/read-back on the same accepted build tuple.
