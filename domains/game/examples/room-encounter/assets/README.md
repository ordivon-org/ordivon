# Original Kenney UI Audio: Game native project consumer

Original source: https://kenney.nl/assets/ui-audio (CC0 1.0).
Godot WAV provider: https://github.com/Calinou/kenney-ui-audio
Immutable provider commit 8c3d81b9159d058c444f89d12d518276b0b09345.
click1.wav SHA256 dd90b97f38b0ec7d52161d7c3bf8d61a66655766fd0af06439963351b4853a83
click2.wav SHA256 a8b35cb35ff45738a9d7fe008490ad21a3ad30417dadd544a435d8b0ea84d841

Only two actual clips are reused from previously installed Game audio carrier; an
independent Godot res:// export root requires its own physical files. The
LICENSE.txt preserves the original legal text with trailing blank-line whitespace normalized. Actual playback consumer: EncounterAudio
native AudioStreamPlayer in main.tscn bound to authoritative Rules state_changed;
valid combat turn plays, invalid action/reset/room advance produces none.
Headless checks engine playback request, not sound from speakers nor playtest.
