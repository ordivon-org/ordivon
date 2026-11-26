# R20 Review input custody
Host #33303. Actual RED: FFprobe inspected 1920x1080, source replaced with
320x240, old public review QC passed and attributed the replacement digest.
Thought: selected bytes, native observation, scoped resource lifetime.
Logic: stable source -> private copy -> one selected Blob -> native QC and
perception consume same snapshot -> verify snapshot -> retire -> packet.
Capability: shutil.copyfile (native fast-copy when available), tempfile,
assets.hash_file, existing FFprobe/FFmpeg and perception bundle.
I selected local regular file; O scoped snapshot and exact observed Blob;
S one private temporary directory; pre source stable during copy;
post technical and perception results refer to same bytes, cleanup before
qualified packet; inv replaced source path cannot relabel evidence,
snapshot drift rejects, failed observation retires own copy; eff copy/read,
existing native observers, output frames; c O(media bytes) storage and reads;
epsilon no atomic/adversarial filesystem proof, no guaranteed COW, SIGKILL
can leave scratch, partial perception outputs are not qualified packet;
prov actual RED, real native replacement and 1920x1080 frame readback,
copy drift and snapshot mutation/exception controls; unfold copy->observe
->verify->retire. The retained original path is a label: consumers must
revalidate digest or recover exact bytes before playback.
No new third-party dependencies; do not own Runtime cleanup or duplicate
native QC. Next natural Runtime/Artifact capacity and kill-recovery review.
