# R21 native contact sheet cardinality and geometry
Host #33405. Native RED: public Review on one valid 320x240 frame
rejected by FFmpeg xstack min inputs=2. Prior fixed scale also stretched
non-16:9 square-pixel input.
Thought: native operator domain, exact selected frame cardinality,
geometry preservation, no invented observations.
Logic selected frames -> native aspect fit/pad -> direct singleton tile
or xstack for multiple -> ordered layout and exact resulting Blob.
Capability existing FFmpeg scale(force_original_aspect_ratio=decrease,
force_divisible_by=2), pad, xstack, native FFprobe/RGB readback.
I nonempty finite images, even positive tile geometry and positive columns;
O image+layout; S native outputs; pre supported square-pixel frame inputs;
post exactly one observed tile per selected frame, no stretch (integer
pixel rounding), ordered fit; inv singleton cannot fabricate a duplicate,
invalid geometry is rejected; eff existing native rendering; c O(N * tile
pixels); epsilon not aesthetic judgment or general SAR/rotation support;
prov actual one-frame native RED and GREEN, mixed aspect actual RGB pixels,
four invalid geometries, existing VFR/Review controls; unfold fit->compose
->observe. No new dependency, no new playback transport.
