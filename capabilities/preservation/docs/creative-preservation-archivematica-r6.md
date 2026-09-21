# Creative Preservation Archivematica R6 Closeout

**Standing:** `ACCEPTED_BOUNDED`

R6 graduates a real Archivematica 1.18 preservation path on the frozen creative corpus. It is no longer an A3M-only pilot or a synthetic preservation claim.

## Graduated path

`frozen owner/source corpus -> BagIt transfer -> Archivematica 1.18 -> Transfer 3880a92e-b919-4bcf-a06b-1885e654a39d -> SIP/AIP 1593a748-703b-46b6-8114-314040f44bd8 -> Storage Service -> stored 7z AIP -> fixity -> restart/reopen -> fixity`

## Corpus and byte preservation

- Frozen corpus: **12 works, 86 files, 4,200,279 bytes**.
- The R6 reconstruction was checked against the historical PREMIS evidence: **86/86 SHA-256 exact** before ingest.
- The stored AIP contains all **86 original files byte-identically**; missing = 0, mismatched = 0.
- All **3 hidden `.gitignore` files** survived.
- Archivematica additionally created **2 preservation derivatives**, both SVG files, with PREMIS `normalization` events and `derivation / has source` relationships. The normalization agent is Inkscape 1.2.2.

## Stored AIP

- AIP UUID: `1593a748-703b-46b6-8114-314040f44bd8`
- Package status: `UPLOADED`
- Stored size: **3,027,140 bytes**
- Stored SHA-256: `e08f0197821c05684cfc50b3dc6119801de6f9137dfeef1df5a43cc8a42ffbda`
- 7z extraction: **PASS**
- METS/PREMIS: **PASS**
- Archivematica Storage Service canonical fixity before restart: **PASS**
- Full compose restart, reopen, unchanged stored SHA-256, and second canonical fixity: **PASS**
- Storage Service now has **2 successful FixityLog records** for this AIP.

## Format-identification boundary

The internal Siegfried 1.11.2 run and an independent external Siegfried 1.11.6 / PRONOM V124 run agree: **84/86 identified**. The two current UNKNOWN files are:

- `gesture-orrery.blend`
- `signal-seed-mark.svg`

Therefore this is a **current PRONOM coverage boundary**, not merely a stale-signature defect in the bundled Archivematica toolchain. Archivematica records failed file-format-identification jobs for these two objects but continues through a valid preservation workflow and stores the AIP.

## Standards boundary

Archivematica 1.18 currently emits its AIP with `BagIt-Version: 0.97` through bagit.py 1.9.0. The AIP fresh-validates and Storage Service fixity passes, but R6 does **not** call this RFC 8493 BagIt 1.0. Our forward handoff can remain BagIt 1.0 while the mature preservation engine's AIP output is recorded faithfully as a bounded legacy declaration.

## What R6 now owns

Ordivon does not own AIP/PREMIS/METS semantics. Archivematica + Storage Service own the preservation implementation. Ordivon owns only the thin admission/handoff, evidence binding, acceptance criteria, and disposition record.

## Not claimed

R6 does not yet prove off-site replication, disaster recovery restore, repository federation/deposit, scheduled long-term fixity operations, or universal format identification. Those remain future operational/preservation layers and are not prerequisites for this local engine graduation.
