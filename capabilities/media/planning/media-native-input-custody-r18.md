# R18 native input byte custody
Host #33103, extends R17 #33092.
RED on fa97280baba421a4f9078067020256b81fdb82a0: actual FFprobe
observes 1920x1080 then caller path is replaced with 320x240; accepted
receipt claims replacement SHA256. Separate path hash is not an observation.

| Thought LEGO | Logic | Capability |
|---|---|---|
| Representation-first | selected carrier vs observed copy | existing path selection, GNU cp |
| Native-first | ephemeral local copy | cp --reflink=auto, mktemp |
| Evidence identity | digest+size from native observation copy | sha256sum stdin, stat |
| Effect separation | admission, native observation, qualification, retirement | native-input.sh, existing providers |
| Source closure | helper identity | existing processing plan and Runtime commitments |
| Independent falsification | real native provider with controlled source drift | unittest, actual FFprobe/FFmpeg/xmllint/ttconv |

I selected local regular carrier; O raw observations and receipt with
original path and digest/size of attempt copy; S attempt-private scratch;
pre valid profile and absent attempt dir; post native commands use same
copy, observed metadata stable, digest describes copied bytes and no
large duplicate retained after normal or handled failure; inv no receipt
on detected unstable copy or native failure; eff temporary copy+cleanup;
c one copy (COW if available), one SHA pass, native observation, metadata
checks; epsilon not atomic full FS, not adversarial same-UID protection,
not transitive resource binding, not proof of caller-selected original
Runtime witness. Hard kill can retain attempt-local scratch; cleanup is
not guaranteed on SIGKILL. Scope current local single-carrier AV/audio/TTML
profiles, not arbitrary external playlists/sidecars. Existing OTIO read
once semantics unchanged. Raw FFprobe filename can be a retired path.
prov actual source replacement on three providers, copy drift, snapshot
metadata drift, invalid media failure, no residue, source closure tests.
unfold copy -> observe bytes -> native tools -> qualify -> retire -> receipt.

Reuse GNU coreutils; no third-party dependencies, no CAS or new registry.
This filesystem reports ext2/ext3 family via stat; COW support not asserted.
Ordinary copy fallback needs capacity for one input during execution.
P1 actual Runtime admission can compare receipt digest to selected digest,
not infer consumption from admission alone. Root CI remains natural owner.
Refs https://www.gnu.org/software/coreutils/manual/coreutils.html
https://www.man7.org/linux/man-pages/man2/FICLONERANGE.2const.html
https://ffmpeg.org/ffprobe.html
